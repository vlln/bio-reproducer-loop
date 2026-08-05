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

每个论文任务生成一个 entry，`scope` 显式声明为 `d1_d3_audit`（机制见 BL-006/0016，
物化 ADR-0008 scored scope）。评分对象是系统在 Reader→Data→Provision 阶段产生的
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

### 4. Entry 命名与 level

- Entry ID 从 `bench-200` 起连续分配（35 篇预留 bench-200~234），遵循 Spec 001
  "bench-100~999 保留给真实论文"的约定；命名空间不与现有构造 entry（bench-001~099）
  和 bench-100 冲突。
- level 按论文定：审计模式 entry 提供真实发布论文 original PDF + 冻结资源
  descriptor，满足 L4 材料要求（BR-009）；资源缺失/受限的按 L4 的
  restricted/unavailable record 处理。不引入新 level。
- `metadata.yaml` 的 `paper_origin: real_published`、`reproduction_target:
  reproducibility_audit`（taxonomy 取值扩展，见 ADR-0008 正交维度表）。

### 5. 论文全文获取：EuropePMC/PMC REST，bundled

34/35 篇未在 claroai-bench 归档中打包全文。converter 提供 PDF 抓取步骤：
优先 EuropePMC fullTextXML/PDF（PMC 开放论文），失败回退 PMC 直链，再失败标记为
`unavailable` 并在 entry review 中人工处置。抓取结果以 sha256 记录进 bundle，
PDF 是 L4 primary paper 的 original（满足 BR-009）。

## 候选方案与 trade-off

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| Converter → 标准 entry | 复用全部现有协议与 evaluator；可发布；引擎无关 | 需实现转换器与 PDF 抓取；D4/D5 claims 仍待人工补 | **采纳** |
| 独立 claroai adapter | 原型快，直接消费 JSONL | 绕过 bundle gate 与独立 oracle；双运行时路径；不可发布 | 拒绝 |
| 首轮直接 D5 全链路 | 一步到位测复现 | 35 篇数值 claims 人工补全 + 真实复现运行，周期最长 | 拒绝（列为后续迭代） |
| 作者分数直接作 oracle | 实现简单 | 多模型主观评分违背独立确定性评分原则 | 拒绝（只作校准） |

## 后果

### 正面

- 35 篇真实论文任务批量接入，补齐 L4 覆盖（0002-l4-l5 的入口问题）。
- 审计模式与现有 pipeline 兼容：不要求被测系统新增"审计"能力，评分其正常执行过程
  产生的审计证据。
- 作者分数成为校准资源：可量化"确定性独立评分 vs 多模型主观评分"的差异
  （对应 claroai-bench 论文中 D3/D4 跨模型一致性差异的观察）。

### 负面

- 审计模式不直接测"复现能力"（D5），第一轮无法与作者 60.6% D5 复现率直接对比。
- PDF 抓取依赖外部服务的开放度与网络；部分论文可能需要人工处置。
- 35 个 entry 的 oracle/claims 由转换生成，首次发布前需要逐篇 fidelity review。

## 约束规则

| 规则编号 | 规则 | 检出方式 |
|----------|------|----------|
| CC-001 | converter 输出必须确定性可重放（同快照 → 字节一致 entry） | converter 测试（golden 对比） |
| CC-002 | 审计模式 entry 的 metadata scope 必须为 `d1_d3_audit` | bundle validator |
| CC-003 | rubric/bundle 不得包含作者分数或 expected verdict | bundle validator forbidden-field 检查 |
| CC-004 | primary paper 必须为真实发布 original PDF/XML，bundled 且记录 sha256 | bundle validator + fidelity review |
| CC-005 | claroai-bench 快照版本（HF commit/树 hash）必须记录进 converter provenance | converter 输出检查 |
| CC-006 | entry ID 使用 bench-200+，不与既有 entry 冲突 | validator + README 一致性检查 |

## 验证

| 验证项 | 复现步骤 | 预期结论 |
|--------|----------|----------|
| 最小转换可行 | 用 claroai-bench 真实 paper_01 文件生成一个审计模式 entry（metadata/bundle/claims/rubric 骨架），跑 `bench-run validate-entry` | entry 通过 bundle gate |
| PDF 抓取可行 | 对 paper_01（PMC 开放论文）执行 EuropePMC REST 抓取 | 获得 original PDF，sha256 记录 |
| 转录正确性 | converter 对 paper_01 生成的 claims 与 scores.json evidence 逐项对照 | 无漂移（测试断言） |
| 审计评分闭环 | 构造 mock submission（审计证据）跑 evaluator | rubric checks 按 ground truth 判定通过/失败 |

验证执行于 `spike/0010-claroai-converter` 分支，完成后本段回填实际命令、依赖版本与结论。
