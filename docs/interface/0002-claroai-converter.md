---
title: Interface 002 — ClaroAI Converter 与审计评分协议
description: 定义 claroai2bench CLI 契约、审计模式 oracle 的 ground truth 结构、rubric check 模式与 submission 审计证据约定（BL-011 / ADR-0010）。
type: interface
status: proposed
created: 2026-08-04T00:00:00Z
---

# Interface 002: ClaroAI Converter 与审计评分协议

本接口服务两类使用者：benchmark maintainer（运行 converter 生成 entry）与 evaluator
（消费审计模式 oracle/submission）。被测系统不接触本接口；审计模式对被测系统的唯一
要求是正常执行 Reader→Data→Provision 阶段并产出既有报告产物。

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

## 2. 审计模式 oracle：`claims.yaml` ground truth 结构

converter 从 `scores.json` evidence + `extraction.json` 转录，结构如下（每个 entry 一份）：

```yaml
id: bench-200
paper_title: "<真实论文标题>"
paper_doi: "<DOI>"
pmid: "<PMID>"
audit_scope: d1_d3_audit
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
calibration:            # 作者分数只作校准，不进 rubric
  d1: 2
  d2: 0
  d3: 1
  confidence: {d1: 0.85, d2: 0.8, d3: 0.95}
```

状态词表（ground truth / 系统判断共用）：

| 字段 | 取值 | 含义 |
|------|------|------|
| data_references.ground_truth | `valid` / `invalid` / `unknown` | accession/链接能否从论文定位并解析 |
| data_references.downloadable | `true` / `false` / `unknown` | 数据能否实际下载（作者审计结论） |
| code_references.ground_truth | `available` / `hollow` / `missing` / `unknown` | 代码仓库：完整可跑 / 空壳 / 404 或不存在 / 无法判断 |

## 3. 审计模式 rubric check 模式

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
      function: check_data_reference   # verify.py 内命名函数
      config: {accession: GSE308855}   # evaluator 签名: function(artifact_path, config) -> {"passed": bool, "actual": ..., "note": str}
    weight: 20
```

`verify.py` 的职责：校验 `claims.yaml` 的 `audit_scope` 与 `metadata.yaml` 的
`scored_scope` 一致（不一致视为 oracle 自检失败）；解析 evidence artifact
（`data_manifest.md`/`provision_report.md` 或可选的 `audit.json`）提取系统对每个
引用的判断，与 `claims.yaml` ground truth 对比；系统判断缺失或无法解析时该 check
判定失败并附原因（不做无依据的 NA 放行，除非 `claims.yaml` 该引用为 `unknown`）。

## 4. Submission 审计证据约定

被测系统不新增协议要求；它照常执行复现 pipeline。verify.py 按以下优先级消费证据：

1. `submission.json` artifacts 中 role=`audit` 的可选结构化产物（如 `audit.json`，
   被测系统自愿产出时使用——schema 与 claims.yaml 状态词表一致）；
2. 现有报告产物（`data_manifest.md`、`provision_report.md`、`run.log`），
   verify.py 内置解析器按论文类型提取 accession 解析/下载/代码检查事实；
3. 两者都不可用 → 该 check 判定失败，记录 `evidence_unavailable`。

系统对引用做出的**错误判断**（如把无效 accession 记为可用）按对应 check 失败计入，
这正是审计模式要测的能力：系统判断论文数据/代码可用性的正确性。

## 5. 信任边界

- converter 与 oracle 生成属于 trusted control plane，不进入被测系统可见范围。
- `claims.yaml` 的 `calibration` 段（作者分数）只被评估后处理脚本读取用于校准分析，
  evaluator 的 verdict/score 计算不引用它。
- primary paper 为 DOI/PMID locator（L5 external，CC-004），entry 不附带论文全文文件（版权）；
  转换失败/待人工复核的论文（处置清单）在完成复核前不进入 release/baseline。
