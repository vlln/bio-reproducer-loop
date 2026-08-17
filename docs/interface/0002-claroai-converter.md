---
title: Interface 002 — ClaroAI Converter 与评分协议
description: 定义 claroai2bench CLI 契约、claims 模式 oracle 的 ground truth 结构、rubric check 模式与 submission 证据约定（BL-011 / ADR-0010 / Plan 0025）。
type: interface
status: active
created: 2026-08-04T00:00:00Z
updated: 2026-08-12T00:00:00Z
---

# Interface 002: ClaroAI Converter 与评分协议

> Plan 0025 修订：审计模式（`scored_scope=d1_d3_audit`）已退役。ClaroAI entry 恢复
> 原始任务——D5 数值 claims（论文发表的定量声明）为评分主体，D1–D3 数据/代码可用性
> 状态为同 rubric 内辅助 checks。系统侧任务为自然语言（`metadata.task`），评分维度
> 代码不再进入被测系统。

本接口服务两类使用者：benchmark maintainer（运行 converter 生成 entry）与 evaluator
（消费 claims 模式 oracle/submission）。被测系统不接触本接口；对被测系统的唯一
要求是正常执行 Reader→Data→Provision→Run→Validate 阶段并产出既有报告产物
（`data_manifest.md`、`provision.md`、`06_validate/report.md`），D5 数值比较基于
被测系统自行产出的复现值（claims evidence）。

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
    metric: "Fig4A tumor"
    paper_value: 599      # 论文发表值（ground truth）
    unit: count
    tolerance: {type: relative, value: 0.05}   # 容差：relative|absolute
    source: "scores.json D5 evidence"
    author_match: exact    # 作者 agent 的对比结论（只作校准上下文）
    author_repr: 599.0
    notes: "..."
  - id: C2
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

## 3. Claims 模式 rubric check 模式

rubric 的 check 统一使用 `python_verify` comparator，`module` 指向 entry 内
`oracle/verify.py`；每个 check 声明 evidence artifact role（指向被测系统既有产物）。

```yaml
checks:
  - id: A1
    description: "系统对 GSE308855 数据可定位性的判断与 ground truth 一致"
    evidence:
      artifact_role: data_manifest   # 被测系统 Data 阶段报告
    comparison:
      comparator: python_verify
      module: verify.py
      function: check_data_references   # verify.py 内命名函数
      config: {}
    weight: 15
  - id: C1
    description: "复现声明 Fig4A tumor（论文值 599）"
    evidence:
      artifact_role: validate_report   # 被测系统 Validate 阶段报告（含复现值）
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

`verify.py` 的职责：解析 evidence artifact（`data_manifest.md`/`provision_report.md`
或 `validate_report.md`）提取系统判断/复现值，与 `claims.yaml` ground truth 对比；
`check_claim` 支持容差数值比较（relative/absolute）与阈值比较（gte/lte）；系统判断
缺失或无法解析时该 check 判定失败并附原因（不做无依据的 NA 放行，除非 ground truth
为 `unknown`）。claims evidence artifact 接受两种格式：结构化 JSON
（`{"claims": [{"metric": ..., "actual": ...}]}`，推荐）或 validate report Markdown
表格（Expected/Actual 列，legacy run 兼容）。

## 4. Submission 证据约定

被测系统不新增协议要求；它照常执行复现 pipeline。verify.py 按以下优先级消费证据：

1. `submission.json` artifacts 中 role=`validate_report` 的产物：结构化 claims
   evidence JSON（`{"claims": [{"metric": ..., "actual": ...}]}`，推荐）或
   `06_validate/report.md`（表格含 Expected/Actual 列）；claims checks（C*）只消费
   该产物；
2. role=`data_manifest`（`data_manifest.md`）+ role=`provision_report`
   （`provision.md`）：D1–D3 证据 checks（A1/A2）的输入；
3. 任一产物缺失或无法解析 → 对应 check 判定失败，记录 `evidence_unavailable`。

系统对引用做出的**错误判断**（如把无效 accession 记为可用）按对应 check 失败计入：
D1–D3 checks 测系统判断论文数据/代码可用性的正确性；claims checks 测系统复现值与
论文发表值的数值一致性。

## 5. 信任边界

- converter 与 oracle 生成属于 trusted control plane，不进入被测系统可见范围。
- `claims.yaml` 的 `calibration` 段（作者分数）只被评估后处理脚本读取用于校准分析，
  evaluator 的 verdict/score 计算不引用它。
- **评估设计不泄漏**（Plan 0025）：`metadata.task` 为自然语言任务说明，禁止携带
  评分维度代码（`scored_scope`、`d1_d3_audit` 等已从 schema 删除）；系统侧参数由
  adapter 从 `task` 翻译，validator 拒绝任何残留维度代码。
- primary paper 为 DOI/PMID locator（L5 external，CC-004），entry 不附带论文全文文件（版权）；
  转换失败/待人工复核的论文（处置清单）在完成复核前不进入 release/baseline。
