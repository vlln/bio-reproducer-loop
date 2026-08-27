---
title: Interface 002 — ClaroAI Converter 与评分协议
description: 定义 claroai2bench CLI 契约、claims 模式 oracle 的 ground truth 结构、rubric check 模式与 submission 证据约定（BL-011 / ADR-0010 / Plan 0025）。
type: interface
status: active
created: 2026-08-04T00:00:00Z
updated: 2026-08-27T00:00:00Z
---

# Interface 002: ClaroAI Converter 与评分协议

> Plan 0025 修订：审计模式（`scored_scope=d1_d3_audit`）已退役。ClaroAI entry 恢复
> 原始任务——D5 数值 claims（论文发表的定量声明）为评分主体，D1–D3 数据/代码可用性
> 状态为同 rubric 内辅助 checks。系统侧任务为自然语言（`metadata.task`），评分维度
> 代码不再进入被测系统。
>
> **单元 04 修订（2026-08-27，证据面切换，ADR-0011 §4/§4.1）**：外部评分只读
> **标准格式真实产物**——数值 claim 的证据是 `05_run/answers.csv`（+强制交叉核对），
> 数据/代码审计的证据是 04_data sha256sums+获取日志、03_provision digests；
> `06_validate/` 整目录不在证据面；`validate_report` 角色已从 converter 生成的
> rubric 移除（FC-004）。公开问题清单 `input/questions.yaml`（ADR §4.1）新增。

本接口服务两类使用者：benchmark maintainer（运行 converter 生成 entry）与 evaluator
（消费 claims 模式 oracle/submission）。被测系统不接触 oracle 私有部分；对被测系统的
唯一要求是产出标准格式产物（04_data/03_provision/05_run 契约，见 Interface 001
「被测系统标准格式产物」），其中 `05_run/answers.csv` 是数值 claim 的证据。

## 1. Converter CLI：`claroai2bench`

```text
claroai2bench --source <hf|dir> --output <entries-dir> [--start-id 200]
              [--snapshot <ref>] [--dry-run]
```

### 入参

| 参数 | 必需 | 说明 |
|------|------|------|
| `--source` | 是 | `hf`（拉取 HF `kyleaoconnell22/claroai-bench` 快照）或本地 claroai-bench 目录 |
| `--output` | 是 | entry 输出根目录（默认 `benchmarks/entries/`） |
| `--start-id` | 否 | 起始 entry 编号，默认 200；按 paper 序号递增分配 |
| `--snapshot` | 否 | 显式记录 claroai-bench 快照 ref（默认：HF 时取当前 commit/树 hash，dir 时取目录内 `.git` 或指纹） |
| `--dry-run` | 否 | 只生成 plan 清单，不写文件 |

### 出参

| 产物 | 说明 |
|------|------|
| `entries/bench-<id>/` | 标准 entry（L5）：metadata.yaml、bundle.yaml、input/paper/locator.md、oracle/claims.yaml + rubric.yaml |
| `<output>/claroai-converter-provenance.json` | 快照 ref、converter 版本、转换时间、每 entry 的 ID 映射（paper_XX → bench-NNN） |

### 错误码

| code | 含义 |
|------|------|
| `CONVERT_OK` | 全部论文转换成功 |
| `CONVERT_PARTIAL` | 部分论文转换成功（含转换失败/待人工复核论文清单，见 E-1 语义），退出码 1 |
| `CONVERT_INVALID_SOURCE` | 快照目录缺 metadata/extraction/scores 或 JSON 损坏 |
| `CONVERT_ID_CONFLICT` | 目标 entry ID 与既有 entry 冲突 |
| `CONVERT_DRIFT` | golden 对比显示同快照转换漂移（仅测试模式触发） |

## 2. Claims 模式 oracle：`claims.yaml` ground truth 结构

converter 从 `scores.json` evidence + `extraction.json` 转录，结构如下（每个 entry 一份）：

```yaml
id: bench-200
paper_title: "<真实论文标题>"
paper_doi: "<DOI>"
pmid: "<PMID>"
reproduction_target: result_verification   # ADR-0008 taxonomy；与 metadata 一致
task: "复现该论文报告的关键定量结果（Fig4A tumor、Fig4A normal），并与论文发表的数值核对；..."  # 自然语言，无评分维度代码
data_references:        # 来源 extraction.json data_references + scores D1/D2 evidence
  - accession: GSE308855
    repository: GEO
    is_primary: true
    ground_truth: valid   # valid | invalid | unknown
    downloadable: false   # 作者审计结论：能否实际下载
    notes: "scores.json D2 evidence: No downloadable files found"
code_references:        # 来源 extraction.json code_references + scores D3 evidence
  - url: "https://github.com/shamsalazzam/code_Multi-omics-profiling"
    language: R
    ground_truth: hollow   # available | hollow | missing | unknown
    notes: "README 描述 pipeline 但零可执行代码"
claims:                 # D5 数值声明（Plan 0025 新增；从 scores.json D5 evidence 转录）
  - id: C1
    target_id: fig4a-tumor      # 公开问题清单的键（ADR §4.1，单元 04 新增）
    metric: "Fig4A tumor"
    paper_value: 599      # 论文发表值（ground truth）
    unit: count
    tolerance: {type: relative, value: 0.05}   # 容差：relative|absolute
    source: "scores.json D5 evidence"
    author_match: exact    # 作者 agent 的对比结论（只作校准上下文）
    author_repr: 599.0
    notes: "..."
  - id: C2
    target_id: fig4a-normal
    metric: "Fig4A normal"
    paper_value: 1390
    tolerance: {type: relative, value: 0.05}
    source: "scores.json D5 evidence"
    author_match: exact
    author_repr: 1386.0
calibration:            # 作者分数只作校准，不进 rubric（含 d1–d5）
  d1: 2
  d2: 0
  d3: 1
  d4: 1
  d5: 2
  confidence: {d1: 0.85, d2: 0.8, d3: 0.95}
```

状态词表（ground truth / 系统判断共用，同审计模式）：

| 字段 | 取值 | 含义 |
|------|------|------|
| data_references.ground_truth | `valid` / `invalid` / `unknown` | accession/链接能否从论文定位并解析 |
| data_references.downloadable | `true` / `false` / `unknown` | 数据能否实际下载（作者审计结论） |
| code_references.ground_truth | `available` / `hollow` / `missing` / `unknown` | 代码仓库：完整可跑 / 空壳 / 404 或不存在 / 无法判断 |
| claims[].tolerance | `{type: relative\|absolute, value: <float>}` | D5 数值比较容差（默认 relative 0.05） |
| claims[].comparison | `{op: gte\|lte}`（可选） | 阈值型声明（如论文声明 AUROC > 0.95 → op=gte, paper_value=0.95） |
| claims[].target_id | 小写连字符 slug | 公开问题清单的键（`input/questions.yaml`）；claim id（C1/…）是 oracle 私有，系统不可能知道（ADR §4.1） |

## 2.1 公开问题清单：`input/questions.yaml`（ADR §4.1，单元 04 新增）

converter 从 `claims.yaml` 转录生成，**只含标识符与问题，无期望值**：

```yaml
schema: questions/v1
questions:
  - target_id: fig4a-tumor
    question: "复现论文报告的 Fig4A tumor 数值"
    unit: count
  - target_id: fig4a-normal
    question: "复现论文报告的 Fig4A normal 数值"
    unit: count
```

- 这是任务的一部分：被测系统按 `target_id` 在 `05_run/answers.csv` 中填写复现值
  （`target_id,value,unit,source_file`）
- oracle 判分 = 比对 answers 的 value 与私有期望值（`claims.yaml` paper_value +
  容差），并**强制交叉核对**（FC-005）：value 必须能在 answers 自述的 `source_file`
  中定位（容差由书写精度导出，`0.5×10^-decimals`，无魔数）；交叉核对失败 →
  **NO-EVIDENCE**（该 claim 不计分不扣分，非判错）
- 代价（论文 limitation 中声明）：公开问题清单把「自行判断该报告哪些数值」从测量中
  移除——换来评分无歧义与引擎中立（baseline 系统用同一份清单）

## 3. Claims 模式 rubric check 模式

rubric 的 check 统一使用 `python_verify` comparator，`module` 指向 entry 内
`oracle/verify.py`；每个 check 声明 evidence artifact role（指向**标准格式真实产物**，
单元 04 起不读任何系统散文报告）：

```yaml
checks:
  - id: A1
    description: "数据引用可获取判断与 ground truth 一致"
    evidence:
      artifact_role: data_evidence   # 04_data sha256sums 输出（+同目录获取日志）
    comparison:
      comparator: python_verify
      module: verify.py
      function: check_data_references
      config: {}
    weight: 15
  - id: A2
    description: "代码引用可用性判断与 ground truth 一致"
    evidence:
      artifact_role: environment   # 03_provision digests.txt（docker images --digests 输出）
    comparison:
      comparator: python_verify
      module: verify.py
      function: check_code_references
      config: {}
    weight: 15
  - id: C1
    description: "复现声明 Fig4A tumor（论文值 599）"
    evidence:
      artifact_role: answers   # 05_run/answers.csv（target_id,value,unit,source_file）
    comparison:
      comparator: python_verify
      module: verify.py
      function: check_claim
      config: {claim_id: C1}
    weight: 35
```

权重约定：D1–D3 证据 checks（A1/A2）各 15；claims checks 合计 70（按条均分）。
无数值 claims 可转录的 entry（湿实验论文或 scores.json 无 D5 evidence）回退为
A1/A2 各 50，`metadata.task` 如实说明边界。

`verify.py` 的职责（单元 04 起，301 行散文解析已退役）：
- `check_claim`：读 `answers.csv` 中 `target_id` 匹配行 → **交叉核对** value 能在
  `source_file` 定位（容差由书写精度导出）→ 与 `claims.yaml` paper_value 容差/阈值
  比较；交叉核对失败或 target 缺失 → 返回 `no_evidence`（不计分不扣分）
- `check_data_references`：从 04_data 获取日志终态（completed/unavailable/
  not_attempted，ADR §2.1）推导系统判断，与 ground truth 比对
- `check_code_references`：从 digests 是否存在推导环境构建产出

## 4. Submission 证据约定

被测系统产出标准格式产物（Interface 001「被测系统标准格式产物」）。verify.py 只消费：

1. role=`answers`（`05_run/answers.csv`）：claims checks（C*）的唯一证据；
   `target_id` 来自公开问题清单，值必须能在自述 `source_file` 中定位；
2. role=`data_evidence`（`04_data/sha256sums.txt`，同目录获取日志）：A1 输入；
3. role=`environment`（`03_provision/digests.txt`）：A2 输入。

**`06_validate/` 整目录不在证据面**（FC-006）：Validate 是系统内部自反馈路由，
不产出对外 verdict；claimed_verdict 只作校准观测。

**NO-EVIDENCE 语义**（FC-005）：任一产物缺失、target 缺失或交叉核对失败 →
该 check 记为 `no_evidence`，**不计分不扣分**（不是判错）；全部 check 均无证据 →
evaluator 返回 BLOCKED，score 不构成复现率。系统对引用做出的**错误判断**（如把无效
accession 记为可用、复现值与论文值超容差）按对应 check 失败计入。

## 5. 信任边界

- converter 与 oracle 生成属于 trusted control plane，不进入被测系统可见范围。
- `claims.yaml` 的 `calibration` 段（作者分数）只被评估后处理脚本读取用于校准分析，
  evaluator 的 verdict/score 计算不引用它。
- **评估设计不泄漏**（Plan 0025）：`metadata.task` 为自然语言任务说明，禁止携带
  评分维度代码（`scored_scope`、`d1_d3_audit` 等已从 schema 删除）；系统侧参数由
  adapter 从 `task` 翻译，validator 拒绝任何残留维度代码。
- primary paper 为 DOI/PMID locator（L5 external，CC-004），entry 不附带论文全文文件（版权）；
  转换失败/待人工复核的论文（处置清单）在完成复核前不进入 release/baseline。
