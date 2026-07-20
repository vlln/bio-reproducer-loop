---
title: Interface 001 — Benchmark 输入、提交与评估协议
description: 定义引擎无关的 input bundle、submission bundle 和 evaluator result 协议及其信任边界。
type: interface
status: active
created: 2026-07-19T00:00:00Z
---

# Interface 001: Benchmark 输入、提交与评估协议

## InputBundle

Runner 将 `entries/<id>/input/` 复制到隔离工作目录，并只向被测系统提供该目录。

| 字段/路径 | 必需 | 说明 |
|-----------|------|------|
| `paper.pdf` 或 `paper.md` | 是 | 被复现论文 |
| `data/` | 否 | 允许使用的本地数据 |
| `supplementary/` | 否 | 允许使用的补充材料 |

`oracle/`、baseline 和其他系统的历史结果不属于 InputBundle。

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
| `INVALID_SUBMISSION` | manifest 缺字段、路径越界或 artifact 不存在 |
| `INVALID_ORACLE` | rubric 或 verifier 配置错误 |
| `EXECUTION_BLOCKED` | 被测系统未完成执行 |
| `EVALUATION_ERROR` | evaluator 内部错误，不计为系统能力失败 |
