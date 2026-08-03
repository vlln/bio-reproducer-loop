# 0015-loopflow-028-migration

## 子任务状态表

| Plan | 状态 | Report |
|------|------|--------|
| [01-plan-loopflow-028-migration.md](01-plan-loopflow-028-migration.md) | done | [01-report-loopflow-028-migration.md](01-report-loopflow-028-migration.md) |

## 概述

loopflow 更新至 0.28.0 后的引擎耦合兼容检查与迁移：eval harness 从已删除的 `--only-phase` 迁移到 0.26.0 单 agent 运行入口（BL-001 闭环，workflow PHASES 注册表单一事实来源），benchmark adapter 以 `--work-dir /output` 对齐"agent 产物写当前工作目录"的新契约，并核对本地/远端/运行时镜像三处 loopflow 版本。
