---
title: Plan 014 - L3 Paired Differential Expression Benchmark
description: 新增一个构造的 L3 配对 RNA-seq 差异表达 entry，覆盖配对设计公式和 block-aware 结果验证。
type: plan
status: done
created: 2026-07-30T05:59:18Z
---

# Context

现有 L3 entries 覆盖独立两组、多工具、多组、环境漂移和交互场景，但没有一个小型、完全已知的
配对差异表达 entry。真实 Himes/airway 由 `bench-100` 的 L4 路径承载，仍需人工 fidelity
review；不能将其复制为未经审查的 L3。

# Request

创建 `bench-003`：构造论文、4 个 donor 的 matched control/treatment count matrix、私有
claims/rubric，以及 runner-only bundle lock。论文必须要求 `~ donor + condition` 设计，oracle
验证两项方向性结果、样本/数据形状、环境记录和 figure 产物。

# Constraints

- Entry 为 L3 constructed paper；所有运行期文件都在 `input/` 且由 `bundle.yaml` 精确声明。
- `bundle.yaml` 不包含 oracle、expected result、评分规则或故障注入意图；oracle 不得进入 InputBundle。
- 数据规模保持小于 10 KB，不依赖网络、GEO、容器下载或真实论文。
- 用显式 donor block 控制个体基线差异；不得将 paired design 退化为独立两组。
- 更新 entry-list 结构测试和 bundle validator 参数化列表。
- 只跑确定性 gate，不运行真实 LLM、baseline 或 formal benchmark。

# Acceptance

| ID | 条件 | 对应 AC |
|----|------|---------|
| PD-001 | `bench-003` bundle、metadata、input、oracle 均完整且 bundle validator 通过 | AC-0003-N-1/N-2 |
| PD-002 | 主论文、count matrix 和每个 bundled resource 的 SHA256 精确匹配 | Interface 0001 EntryBundle |
| PD-003 | 论文和 claims 明确声明 4 个 donor、8 个样本与 `~ donor + condition` | AC-0003-N-1 |
| PD-004 | Rubric 对 treatment-up、treatment-down、shape、environment 和 figure 具备实质断言 | AC-0003-N-2/F-2 |
| PD-005 | 新 entry 被确定性结构测试枚举，且全套 `pytest tests/` 与 lint 通过 | DEVELOP gate |
