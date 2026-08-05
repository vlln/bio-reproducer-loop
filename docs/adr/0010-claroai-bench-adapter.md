---
title: ADR-0010 — ClaroAI-Bench 接入形态
description: 决定以 converter 将 ClaroAI-Bench 任务确定性转换为标准 entry，首轮 scored scope 为 D1–D3 审计模式，作者 ground truth 只作校准参考。
type: adr
status: proposed
created: 2026-08-04T00:00:00Z
---

# ADR-0010: ClaroAI-Bench 接入形态

## 背景

BL-011：ClaroAI-Bench（Kyle O'Connell, bioRxiv 2026.05.08.723611）提供 35 篇真实 NIH
论文任务及作者给出的 D1–D5 可复现性评分（数据可定位/可获取/代码可用/环境可重建/结果
可匹配），归档于 GitHub `kyleaoconnell22/claroai-bench` 与 HF `kyleaoconnell22/claroai-bench`
（本地调研副本 `~/Project/claroai-bench*`，调研报告 `RESEARCH_REPORT.md`）。

bio-reproducer 需要真实论文 entry（执行容器 0002-l4-l5 处于 pending，目前仅 bench-100
一个 L4 任务）。ClaroAI-Bench 是现成的真实论文任务来源，且其作者评分可作为校准参照。

关键差异：ClaroAI-Bench 的任务是"agent 对论文做可复现性审计"，评分是作者用
Claude/GPT/Gemini 多模型给出的 D1–D5 分数 + evidence；bio-reproducer 的 entry 是
"被测系统复现论文"，评分是独立 evaluator 用确定性 comparator 检查 submission 产物。
本 ADR 决定两者的对接形态，不改变 InputBundle/OracleBundle 信任边界（ADR-0005/0007/0009）。

## 决策内容

### 1. 接入形态：Converter，而非独立 adapter

将 claroai-bench 的 `papers/paper_XX/` 经**确定性、可重放**的转换生成标准 entry
（`metadata.yaml` + `bundle.yaml` + `input/` + `oracle/`），走既有 bundle gate 与
独立 evaluator。不采用仿 `adapters/loopflow.py` 直接消费 claroai-bench JSONL 的
adapter 路线。

理由：converter 产出标准 entry 后，评分、发布、版本管理和外部引擎兼容全部复用现有
协议（Interface 0001），不需要为外部格式维护第二套运行时路径；这也符合公开 benchmark
"引擎无关、独立评分"的定位。

### 2. 首轮 scored scope：D1–D3 审计模式

每个论文任务生成一个 entry，`scored_scope` 显式声明为 `d1_d3_audit`（机制见
BL-006/0016，物化 ADR-0008 scored scope）。评分对象是系统在 Reader→Data→Provision 阶段产生的
审计证据（accession 解析、下载尝试、代码仓库与工具可用性处理），oracle 用
`python_verify` 对比作者 ground truth 状态。

D4/D5（环境重建、结果匹配）不在首轮范围：它们需要逐篇人工补全数值 claims 与真实
复现运行，周期长且失败率高（作者报告全能力 agent D5 仅 60.6%）。D1–D3 可从
`extraction.json`/`scores.json` 的 evidence 半自动转换，先行上量。

### 3. Oracle 策略：ground truth 转结构化 claims，作者分数只作校准

- `oracle/claims.yaml` 结构化记录每个数据/代码引用的作者 ground truth 状态
  （accession 是否有效、数据是否可下载、代码仓库是否完整可跑），来源是
  `scores.json` 的 evidence + `extraction.json`，由 converter 转录并随快照冻结。
- 作者 D1–D3 分数**不进入** rubric 的 expected verdict 与 bundle lock
  （BR-018）：分数是主观多模型审计结果，只作事后校准观测（baseline），
  与独立 evaluator 的 verdict/score 对照分析。
- 转录正确性由 converter 测试保证（fixture = claroai-bench 真实文件），
  不依赖人工转录。

### 4. Entry 命名与 level：L5 + DOI/PMID locator

- Entry ID 从 `bench-200` 起连续分配（35 篇预留 bench-200~234），遵循 Spec 001
  "bench-100~999 保留给真实论文"的约定；命名空间不与现有构造 entry（bench-001~099）
  和 bench-100 冲突。
- **level 固定为 L5，不附带论文全文**：claroai-bench 归档本身不分发论文（只提供
  DOI/PMID 引用），在 benchmark 内打包论文全文涉及版权，不予附带。primary paper
  使用稳定 DOI/PMID locator（availability=`external`），符合 Interface 0001 的 L5
  材料要求（"original paper 或稳定 DOI/PMID/arXiv locator"，允许 external）；
  被测系统在 `controlled-egress` 网络策略下自行获取论文全文并记录实际解析结果
  （L5 语义，Spec 001）。获取失败由系统记录为 `external` blocked（BR-004 不计入失败）。
- `metadata.yaml` 的 `paper_origin: real_published`、`reproduction_target:
  reproducibility_audit`（taxonomy 取值扩展，见 ADR-0008 正交维度表）；
  同时必须声明 `complexity_profile.paper.paper_type: real_published`
  （bundle validator 对 bench-100+ 的硬性要求，缺失即 INVALID_BUNDLE；
  `paper_type` 是 validator 强制字段，`paper_origin` 是 ADR-0008 正交分类维度，二者并存）。

### 5. 不附带论文全文（版权决策）

claroai-bench 归档不含论文全文；本 benchmark 亦不打包。converter 不执行全文抓取、
不产生 bundled paper 文件。entry 的 `input/` 仅包含论文 locator 描述
（`input/paper/locator.md`，记录 DOI/PMID/PMC id 与获取指引），primary paper
resource 的 `source` 为 DOI/PMID，`availability=external`。

被测系统自行获取论文全文的能力是本模式的前提（claroai-bench 的 agent 即如此运行）；
获取失败按 `external` blocked 记录，不计入系统失败。D1 的 ground truth（作者判断的
accession/链接可解析性）与系统实际解析结果的对比仍由 oracle 完成。

L5 材料语义（稳定标识符最小可信起点 + 运行时发现）可服务本 curated 集合（35 篇固定
论文），与 Spec 的 L5 随机采样/长期观测用途不冲突：材料语义相同，操作面不同。运行
次数沿用 BR-001 的 L3/L4 约定精神，审计模式 entry 建议 N≥1（推荐 2-3 次），与 L4 一致，
不作 CI gate、结果进入观测。

## 候选方案与 trade-off

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| Converter → 标准 entry | 复用全部现有协议与 evaluator；可发布；引擎无关；不附带论文全文（版权） | 需实现转换器；D4/D5 claims 仍待人工补；依赖被测系统运行时获取论文 | **采纳** |
| 独立 claroai adapter | 原型快，直接消费 JSONL | 绕过 bundle gate 与独立 oracle；双运行时路径；不可发布 | 拒绝 |
| 首轮直接 D5 全链路 | 一步到位测复现 | 35 篇数值 claims 人工补全 + 真实复现运行，周期最长 | 拒绝（列为后续迭代） |
| 作者分数直接作 oracle | 实现简单 | 多模型主观评分违背独立确定性评分原则 | 拒绝（只作校准） |

## 后果

### 正面

- 35 篇真实论文任务批量接入，补齐真实论文覆盖（0002-l4-l5 的入口问题），且不附带论文全文、无版权分发负担。
- 审计模式与现有 pipeline 兼容：不要求被测系统新增"审计"能力，评分其正常执行过程
  产生的审计证据。
- 作者分数成为校准资源：可量化"确定性独立评分 vs 多模型主观评分"的差异
  （对应 claroai-bench 论文中 D3/D4 跨模型一致性差异的观察）。

### 负面

- 审计模式不直接测"复现能力"（D5），第一轮无法与作者 60.6% D5 复现率直接对比。
- 被测系统运行时获取论文全文依赖外部服务的开放度与网络；获取失败的论文结果按 external blocked 记录，系统能力之外存在外部依赖噪声。
- 35 个 entry 的 oracle/claims 由转换生成，首次发布前需要逐篇 fidelity review。

## 约束规则

| 规则编号 | 规则 | 检出方式 |
|----------|------|----------|
| CC-001 | converter 输出必须确定性可重放（同快照 → 字节一致 entry） | converter 测试（golden 对比） |
| CC-002 | 审计模式 entry 的 metadata scored_scope 必须为 `d1_d3_audit` | bundle validator（扩展：审计模式 entry 缺失或非该值 → INVALID_BUNDLE） |
| CC-003 | rubric 不得包含作者真值派生键（精确名单：顶层 `author_score`/`author_scores`/`calibration`/`ground_truth` 及顶层 `d1`/`d2`/`d3` 分数键）；协议合法键（`checks`、`expected_verdict`、`verdict_match_threshold`、`verdict_thresholds` 等）不受影响；bundle 沿用 FORBIDDEN_KEYS | bundle validator 扩展以该精确名单扫描 `oracle/rubric.yaml`（仅审计模式 entry）；release gate 复核 |
| CC-004 | primary paper 为真实发布论文的稳定 DOI/PMID locator，`availability=external`，entry 不附带论文全文文件（版权）；拒绝审计模式 entry 以 bundled 形式声明 primary paper 属 validator 扩展（与 CC-002 同批落地） | bundle validator（扩展）+ fidelity review |
| CC-005 | claroai-bench 快照版本（HF commit/树 hash）必须记录进 converter provenance | converter 输出检查 |
| CC-006 | entry ID 使用 bench-200+，不与既有 entry 冲突 | validator + README 一致性检查 |

## 验证

验证执行于 `spike/0010-claroai-converter` 分支（保留不合并）。验证代码：
`benchmarks/converters/claroai/spike_convert.py`；真实输入 `~/Project/claroai-bench/papers/paper_01/`
（claroai-bench 归档）；输出与 mock 位于 `/tmp/claroai-spike/`。Python 3.13，依赖 pyyaml。

| 验证项 | 复现步骤 | 预期结论 | 实际结论 |
|--------|----------|----------|----------|
| 最小转换可行 | `python3 benchmarks/converters/claroai/spike_convert.py ~/Project/claroai-bench/papers/paper_01 /tmp/claroai-spike/entries/bench-200 bench-200 <paper_01.xml>` 后 `validate_entry('…/bench-200')` | entry 通过 bundle gate | **通过**：`VALID: bench-200 L4`（bundled XML 版验证了转换链路）；版权决策后另验证 **L5 locator 版**：primary paper 改 external DOI locator + `paper/locator.md` 声明为 bundled metadata resource → `VALID: bench-200 L5`，确认 L5 方案通过既有 bundle gate |
| 全文获取路径可行 | `curl https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12874334/fullTextXML` | 获得 original 全文 | **通过**：EuropePMC fullTextXML 稳定可用（JATS XML 173 KB）——验证了被测系统经 DOI/PMC id 自行获取论文全文的路径可行；`fullTextPDF` 对 paper_01 返回空、PMC OA tgz 的 https 路径 404、PMC 网页 PDF 需浏览器 → 系统获取策略定为 XML 优先、PDF 增强。entry 不打包全文（版权），此验证仅证明运行时获取路径 |
| 转录正确性 | 对比生成的 `oracle/claims.yaml` 与 `scores.json` evidence | 无漂移 | **通过（含精度发现）**：D1=2/D2=0/D3=1 → 全部 accession `valid`+`downloadable=false`、code `hollow` 与维度分一致；**发现 per-reference 精度问题**：D3=1 时把全部 code_references 标 `hollow`，但作者 justification 只针对主仓库，正式 converter 须从 evidence 文本解析逐引用状态（AC-0009-N-5 覆盖） |
| 审计评分闭环 | `evaluate_submission('…/bench-200', '…/submission.json')`，mock 证据与 ground truth 一致；再改坏一个判断重跑 | 一致→REPRODUCED；错判→失败 | **通过**：一致 → `verdict=REPRODUCED, score=100`；把 GSE308855 误判为可下载 → `verdict=PARTIAL, score=50`，check 附原因 |

结论：converter 路线可行；审计模式 entry（scored_scope=d1_d3_audit，data/code 引用
unavailable+核查记录）通过既有 bundle gate 与 evaluator，无需新增运行时路径。版权决策后
primary paper 为 L5 external DOI/PMID locator（CC-004），不附带论文全文。
