---
title: Plan 001 — 基准测试体系实施
description: 基准测试体系（L1-L5）的实施计划，按优先级分阶段执行。
type: plan
status: pending
created: 2026-07-15T00:00:00Z
---

# 实施路线

## 阶段 1: L3 基础

- 设计 bench-001 构造论文（基础图表复现型）
- 实现 benchmark runner（支持多次运行、输出分布）
- 标注 golden fixtures（粗粒度，关键字段）

## 阶段 2: L1 + L2

- 基于 L3 的 golden fixtures，实现单 Phase 和多 Phase 测试
- L2 包含非完美上游产出的测试用例
- 集成到 CI

## 阶段 3: Baseline 建立

- 首次完整运行 L3，记录 verdict 分布作为 baseline
- 之后每次改动，对比 baseline 看变化方向

## 阶段 4: L4 工程基准

- 将 paper-entries.md 中的论文结构化
- 先选 Tier 1 论文（airway 等，工程复杂度极低）作为过渡
- 实现环境冻结，预烘焙 benchmark 环境

## 阶段 5: L3 扩展

- 增加更多构造论文，覆盖数据复现型、结论复现型、流程复现型

## 阶段 6: L5 生产基准

- 定期采样新论文，长期追踪真实世界复现率