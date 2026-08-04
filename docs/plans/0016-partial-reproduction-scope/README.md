# 0016-partial-reproduction-scope

## 子任务状态表

| Plan | 状态 | Report |
|------|------|--------|
| [01-plan-partial-reproduction-scope.md](01-plan-partial-reproduction-scope.md) | done | [01-report-partial-reproduction-scope.md](01-report-partial-reproduction-scope.md) |

## 概述

新增 `scope` 部分复现范围入口：paper-01 试跑暴露"只复现部分 figure"无 prompt 入口的
缺口。loop 层新增可选 arg（空=全论文），Reader 的 Reproduction Target 表、Data/Run 的
执行、Validate 的检查项、Package 的交付都只覆盖范围内目标；benchmark adapter 通过
metadata 可选 `scope` 字段透传（物化 ADR-0008 的 entry 单一 scored scope）。
