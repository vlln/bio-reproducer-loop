---
title: Plan 003 — 独立评估与测试分域
description: 迁移 benchmark 信任边界、重建确定性测试，并将真实 LLM 用例迁移到内部 eval harness。
type: plan
status: done
created: 2026-07-19T00:00:00Z
---

# 实施路线

> 本 Plan 仅在 Spec v2、Interface 0001、ADR-0005/0006 通过设计审查后执行。

## 阶段 1: 信任边界

- 定义 `submission.json`、oracle rubric 和 evaluator result schema
- Runner 只 stage `input/`，验证被测进程不可读取 `oracle/`
- Adapter 生成 artifact manifest，不再生成权威 score/verdict
- Evaluator 直接检查 CSV、图像、日志和脚本等实际产物

## 阶段 2: 确定性测试

- 建立 fake executor 和 `tests/contract/`
- 重写 runner、adapter、evaluator 单元测试，禁止真实 LLM 与网络
- 增加伪造 claimed score、路径越界、缺失产物和非零退出的 negative tests
- 将确定性测试加入 CI 必过门禁

## 阶段 3: 内部行为评测

- 建立 `evals/component/` 与 `evals/handoff/`
- 将现有 Phase 用例迁移为 capability case、behavior checks 和上游状态 fixture，不再使用多用途 golden
- 记录模型、Prompt、工具和环境版本，由 execution profile 控制重复运行并输出分布报告
- 缺失产物、Phase skip 和进程非零必须记为失败或基础设施错误

## 阶段 4: Entry 迁移

- 将现有 entry 迁移为 `input/` 与 `oracle/`
- 把 metadata 中 baseline 移到 `benchmarks/baselines/`
- 为自动检查项声明 evidence、comparison、tolerance 和 weight
- 旧协议结果归档并标明不可与 v2 直接比较
