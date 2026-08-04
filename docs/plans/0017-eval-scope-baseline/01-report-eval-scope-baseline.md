---
title: scope 语义 component eval 基线执行报告
description: reader-scoped-targets 真实 LLM 运行 PASSED，plan.md 证据展示 scope 语义正确生效
type: report
status: complete
created: 2026-08-04T00:00:00Z
---

# scope 语义 component eval 基线执行报告

## 结果

范围完成。`pytest tests/unit` 124 通过；`test_reader_scoped_targets` 真实 LLM
smoke 运行 **PASSED**（96.25s，1 run，deepseek-v4-pro via claude CLI）。

## 证据（plan.md 关键节）

```markdown
### Reproduction Target
| ID | Target | ... |
*Scope note: Reproduction scope is `figures=figure1`. T1 is included as a
prerequisite for generating the volcano plot. All other paper claims
(conclusions, data availability URLs) are out-of-scope for this reproduction run.*

## Decision Record
| Scope filtering | `figures=figure1` | User specified reproduction scope as
  `figures=figure1`. T1 (DEG table) included as prerequisite for T2 (volcano plot). |
```

断言全部通过：contains `figure1`、contains_any `[Decision Record, decision,
复现范围]`、not_contains `[figure2, figure3]`。

## 语义验证结论

1. **范围限定生效**：Reproduction Target 表只列 figure1 目标，其余声明显式标注
   out-of-scope；
2. **前置依赖合理保留**：T1（DEG 表）作为 T2（volcano）的输入前置被保留——符合
   0016 设计（范围内目标的依赖不被误删）；
3. **Decision Record 留痕**：scope 决策原文与解读写入 plan.md，可追溯。

## 测试资产

- `evals/cases/component/reader-scoped-targets/case.yaml`（bench-001，scope=figures=figure1）
- `evals/component/test_components.py::test_reader_scoped_targets`
- `evals/coverage.yaml` 新增 `partial_reproduction_scope` capability
- `evals/schemas/case.schema.json` 增加可选 `scope` 字段

## 遗留

- handoff 级 scope 语义（跨 phase 范围传递）未覆盖：建议后续用真实论文（如
  paper-01）完整 scope 运行观察 data/run/validate 的范围行为（0016 遗留 item 2
  的远端 paper-01 scope 运行正在执行）
