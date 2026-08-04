---
title: Report 014 - L3 Paired Differential Expression Benchmark
description: 记录 bench-003 的构造论文、paired count matrix、bundle lock、oracle 和确定性门禁。
type: report
status: complete
created: 2026-07-30T05:59:18Z
---

# Conclusion

Plan 014 完成。新增 `bench-003` L3 entry，使用四个 donor 的 matched Control/Treatment
样本和六个基因的本地 count matrix，明确要求 `~ donor + condition`，覆盖现有 L3 未覆盖的
paired differential-expression 能力。它不依赖外部数据，也未改变 `bench-100` 的 L4 fidelity
review 边界。

# Entry

| 项目 | 结果 |
|------|------|
| ID / level | `bench-003` / L3 |
| InputBundle | `input/paper.md`, `input/data/counts.csv` |
| Design | 4 donors, 8 matched samples, 6 genes |
| Required method | DESeq2 with `~ donor + condition` |
| Oracle | paired design claim, Gene_P induction, Gene_Q repression, shape, environment, volcano |
| Commits | `855aaeb` (Plan), `f1eedfe` (entry implementation) |

# Gates

```text
bench-run validate-entry --entry bench-003: VALID
targeted bundle/structure tests: 27 passed
full deterministic tests: 114 passed, 4 skipped
make lint: PASS
git diff --check: PASS
bundle validators: bench-001/002/003/004/005/006/100 VALID
```

The first full test invocation was blocked by sandbox localhost bind permission in three existing
QEMU worker unit tests. The same test layer was rerun with the required elevated permission; all
three passed. No benchmark run, LLM eval, baseline, or external download was performed.

# Acceptance

| ID | Status | Evidence |
|----|--------|----------|
| PD-001 | PASS | `bench-run validate-entry --entry bench-003`; 27 targeted tests |
| PD-002 | PASS | Bundle SHA256 checks for paper and count matrix |
| PD-003 | PASS | Paper, claims and matrix declare four donor pairs and eight samples |
| PD-004 | PASS | Private rubric contains substantive shape, environment, direction, significance and figure checks |
| PD-005 | PASS | 114 deterministic tests, lint and all bundle validators pass |
