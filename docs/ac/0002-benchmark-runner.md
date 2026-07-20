---
title: AC 002 — Benchmark Runner
description: benchmark 执行器的验收标准，覆盖 CLI、执行、评估、报告功能。
type: ac
status: active
created: 2026-07-15T00:00:00Z
---

# AC-0004: Runner CLI

验证 benchmark 执行器的命令行接口。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0004-N-1 | bench-001 论文包存在 | `bench-run run --entry bench-001 --runs 5` | 执行 5 次，产出 results/ 目录 | 自动化 |
| AC-0004-N-2 | 已有 submission 和私有 oracle | `bench-run eval --entry bench-001` | 独立检查 artifacts，输出 evaluator result | 自动化 |
| AC-0004-N-3 | 已有运行结果 | `bench-run report --date 2026-07-14` | 产出 summary.json | 自动化 |
| AC-0004-N-4 | 已有 protocol v1 `repro-data/` 和系统自评 | `bench-run submit --entry bench-001` 后执行 eval | 不重跑系统；旧自评保存为 `legacy-result.json`，新 result 由 evaluator 生成 | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0004-B-1 | 论文包不存在 | `bench-run run --entry not-exists` | 明确错误信息，退出码 2 | 自动化 |
| AC-0004-B-2 | 已有 3 次运行结果 | `bench-run run --entry bench-001 --runs 5` | 补充 2 次，不重复已有 | 自动化 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0004-E-1 | 输出目录不可写 | `bench-run run ...` | 明确错误信息 | 自动化 |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0004-F-1 | oracle/rubric.yaml 缺失 | `bench-run eval --entry bench-001` | 返回 INVALID_ORACLE，不生成伪结果 | 自动化 |

---

# AC-0005: Engine Adapter

验证引擎适配器将论文包映射为 loopflow 调用的正确性。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0005-N-1 | bench-001 InputBundle 完整 | 调用 adapter.run(input_bundle) | 返回标准 submission.json 和 artifacts | 自动化 |
| AC-0005-N-2 | bench-001 InputBundle 完整 | 调用 adapter | execution 中 stages 的 name 和 status 正确 | 自动化 |
| AC-0005-N-3 | entry 同时含 input/ 与 oracle/ | 调用 adapter | 被测进程工作目录中 oracle 不可见 | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0005-B-1 | InputBundle data/ 为空 | 调用 adapter | submission execution 记录 blocked/partial 或恢复后的 artifacts | 自动化 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0005-E-1 | loopflow 不可用 | 调用 adapter | 抛出明确错误，不静默失败 | 自动化 |
