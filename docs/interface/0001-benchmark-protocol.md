---
title: Interface 001 — Benchmark 输入、提交与评估协议
description: 定义分层且可追溯的 input bundle、submission bundle 和 evaluator result 协议及其信任边界。
type: interface
status: proposed
created: 2026-07-19T00:00:00Z
---

# Interface 001: Benchmark 输入、提交与评估协议

## InputBundle

Runner 校验 `entries/<id>/input/manifest.yaml` 后，将整个 `input/` 复制到隔离工作目录，
并只向被测系统提供该目录。`oracle/`、baseline、其他系统的历史结果和故障注入意图不属于
InputBundle。

```text
input/
├── manifest.yaml          # 必需，公开的资源与 provenance 清单
├── paper/                 # 论文原始文件与派生表示
├── supplementary/         # 补充材料原件
├── code/                  # cited code 的冻结快照
├── data/                  # 冻结数据、派生数据或访问 descriptor
└── resources/             # landing page、availability record 等辅助快照
```

除 `manifest.yaml` 外，每个 staged 文件都必须由一个 resource 声明。目录可以不存在，
但论文引用而未打包的资源必须有带状态的 resource record，不能通过省略目录表达。

### manifest.yaml

```yaml
schema_version: "1.0"
entry_id: bench-003
level: L4
primary_paper: paper-main
resources:
  - id: paper-main
    role: paper
    authority: original
    path: paper/article.pdf
    source: https://doi.org/10.1371/journal.pone.0099625
    retrieved_at: 2026-07-20T00:00:00Z
    sha256: "<64 lowercase hex characters>"
    media_type: application/pdf
    license: CC-BY-4.0
    availability: bundled
  - id: paper-markdown
    role: paper
    authority: derived
    path: paper/article.md
    availability: bundled
    derived_from: [paper-main]
    transform:
      tool: mineru
      version: "<version>"
      command: "<reproducible command or script path>"
  - id: cited-code
    role: code
    authority: original
    source: https://example.org/cited-repository
    availability: unavailable
    checked_at: 2026-07-20T00:00:00Z
    access_notes: Repository returned 404 during bundle review.
```

### ManifestResource

| 字段 | 必需 | 说明 |
|------|------|------|
| `id` | 是 | InputBundle 内稳定且唯一的资源 ID |
| `role` | 是 | `paper` / `supplementary` / `code` / `data` / `metadata` / `environment` / `resource_page` |
| `authority` | 是 | `original` 或 `derived` |
| `availability` | 是 | `bundled` / `external` / `restricted` / `unavailable` / `not_applicable` |
| `path` | bundled 时 | 相对 `input/` 的文件路径；禁止绝对路径和 `..` |
| `source` | original 时 | DOI、accession、仓库/发布页 URL；constructed L3 使用 `urn:benchmark:<entry>:<resource>` |
| `sha256` | bundled 文件时 | 文件内容校验和 |
| `retrieved_at` | bundled original 时 | 获取时间 |
| `media_type` | bundled 文件时 | IANA media type |
| `license` | 可选 | SPDX ID 或原始许可说明 |
| `derived_from` | derived 时 | 一个或多个上游 resource ID |
| `transform` | derived 时 | 可重复的工具版本、命令或脚本路径 |
| `checked_at` | unavailable/restricted 时 | 可用性核查时间 |
| `access_notes` | unavailable/restricted 时 | 核查位置、访问条件或失败事实 |

### Level 约束

| Level | primary paper | resources |
|-------|---------------|-----------|
| L3 | constructed original，可为 Markdown/PDF | 场景需要的构造材料；虚构或不可用引用必须登记 |
| L4 | 真实发布的 original PDF/XML/HTML | 所有 cited resources 必须 bundled、restricted 或 unavailable；派生/裁剪材料必须可追溯 |
| L5 | original paper 或稳定 DOI/PMID/arXiv locator | 允许 external，运行时执行真实资源发现并记录结果 |

Manifest 不得包含 scientific expected values、rubric checks、score、expected verdict 或
故障注入原因。它描述被测系统在现实中可观察的材料事实，不描述如何得分。

## SubmissionBundle

被测系统执行结束后，adapter 生成 `submission.json`，所有路径相对于 submission 根目录。

```json
{
  "submission_id": "bench-001-20260719T120000Z",
  "bench_id": "bench-001",
  "system": {"name": "bio-reproducer", "version": "0.1.0"},
  "claimed_verdict": "REPRODUCED",
  "artifacts": [
    {"role": "result_table", "id": "treatment_vs_control", "path": "artifacts/deseq2_results.csv"},
    {"role": "figure", "id": "volcano", "path": "artifacts/volcano.png"},
    {"role": "run_log", "path": "artifacts/run.log"}
  ],
  "execution": {"duration_seconds": 42, "stages": []}
}
```

`claimed_verdict` 可缺省且不参与最终分数计算。Artifact role 允许扩展，但未知 role
必须被 evaluator 保留而非静默丢弃。同一 role 存在多个语义产物时必须提供稳定的 `id`
（例如 contrast 名称），oracle 可以声明正反 contrast 或合并表为等价证据，但不得改写系统原始产物。

已存在的 protocol v1 运行可执行 `bench-run submit --entry <id>`，从 `repro-data/`
补建 manifest，无需重新运行被测系统。随后执行 `bench-run eval --entry <id>`；原系统生成的
`result.json` 会保留为 `legacy-result.json`，新 `result.json` 仅由 evaluator 生成。

## OracleBundle

| 路径 | 必需 | 说明 |
|------|------|------|
| `claims.yaml` | 是 | 论文与数据的结构化科学事实 |
| `rubric.yaml` | 是 | 检查项、证据、比较器、容差和权重 |
| `expected-results/` | 否 | 参考表格、集合、图像特征或 checksum |
| `verify.py` | 否 | Entry 特定的纯评估逻辑 |

## EvaluationResult

Evaluator 独立生成 `result.json`：

```json
{
  "run_id": "bench-001-20260719T120000Z",
  "bench_id": "bench-001",
  "benchmark_version": "2.0.0",
  "submission_id": "bench-001-20260719T120000Z",
  "verdict": "REPRODUCED",
  "score": 87.5,
  "checks": [],
  "calibration": {"claimed_verdict": "REPRODUCED", "matches": true},
  "provenance": {"evaluator_version": "2.0.0", "oracle_version": "1.0.0"}
}
```

## 错误语义

| code | 含义 |
|------|------|
| `INVALID_INPUT` | InputBundle 不完整或损坏 |
| `INVALID_INPUT_PROVENANCE` | manifest、checksum、层级完整性或派生关系不合法 |
| `INVALID_SUBMISSION` | manifest 缺字段、路径越界或 artifact 不存在 |
| `INVALID_ORACLE` | rubric 或 verifier 配置错误 |
| `EXECUTION_BLOCKED` | 被测系统未完成执行 |
| `EVALUATION_ERROR` | evaluator 内部错误，不计为系统能力失败 |
