---
title: AC 001 — 基准测试分层
description: 五层测试体系（L1-L5）的验收标准，覆盖各层的核心能力验证。
type: ac
status: proposed
created: 2026-07-15T00:00:00Z
---

# AC-0001: L1 单 Agent 可靠性

验证单个 Phase Agent 在给定输入下的业务逻辑正确性。

## L1 的定位

L1 测的是 Agent 的**业务决策**是否正确，不是 schema 是否合规。Schema 合规（字段类型、枚举值、JSON 格式）是 loopflow workflow 运行时的基础设施保证，不属于 benchmark 测试范围。

L1 通过真实 LLM 调用运行单个 Phase Agent，对比其产出与 golden fixture 的关键业务字段：

- 不比较全文，只比较结构化关键字段（status、tool list、accession 列表、关键决策点）
- 不测 schema 合规（那是 loopflow 的事）
- 语义正确性（提取的基因对不对、参数准不准）是 L1 的核心关注点

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0001-N-1 | golden_plan.md 存在 | 运行 Reader agent，传入论文 PDF 路径 | 产出的 tool list、accession 列表与 golden 一致 | 自动化（结构化字段对比） |
| AC-0001-N-2 | plan.md 包含完整 Environment Requirements | 运行 Provision agent | 产出的工具→镜像映射与 golden 一致 | 自动化（结构化字段对比） |
| AC-0001-N-3 | 同一输入、同一 Phase | 连续运行 5 次 | 关键决策点（status、tool list）一致 | 自动化（分布统计） |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0001-B-1 | 论文 PDF 路径指向不存在的文件 | 运行 Reader agent | status 为 blocked 或 failed，missing 列表说明原因 | 自动化（结构化字段对比） |
| AC-0001-B-2 | 上游产出中 Data Requirements 表为空 | 运行 Data agent | status 为 partial 或 blocked，不编造 accession | 自动化（字段检查：accession 列表为空） |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0001-E-1 | plan.md 中 Environment Requirements 写的是不存在的工具名 | 运行 Provision agent | status 为 partial 或 blocked，missing 列表记录该工具 | 自动化（结构化字段对比） |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0001-F-1 | loopflow 后端不可用 | 运行任意 Phase agent | 抛出 AgentError，不静默失败 | 自动化（异常捕获） |

---

# AC-0002: L2 跨 Phase 信息流

验证 Phase 之间的信息传递正确性和非完美上游的处理能力。

## L2 的定位

与 L1 相同，L2 测的是**业务逻辑**——Phase 之间的信息流是否自洽，下游对上游异常的处理决策是否正确。不测 schema 合规（那是 loopflow 的事）。

L2 通过真实 LLM 调用运行多个 Phase Agent。构造带缺陷的上游产出（如 Data Requirements 为空的 plan.md、工具 status 为 failed 的 provision.md），喂给下游 Agent，检查其业务决策是否正确。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0002-N-1 | golden_plan.md 包含完整 Data Requirements | 运行 Data agent | 产出的 accession 列表与 golden_plan.md 一致 | 自动化（结构化字段对比） |
| AC-0002-N-2 | golden_plan.md + golden_provision.md 存在 | 运行 Run agent | 产出的工具引用与 golden_provision.md 一致，参数与 golden_plan.md 一致 | 自动化（结构化字段对比） |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0002-B-1 | plan.md 中 Data Requirements 表为空 | 运行 Data agent | status 为 partial 或 blocked，不编造 accession | 自动化（accession 列表为空） |
| AC-0002-B-2 | provision.md 中某工具 status 为 failed | 运行 Run agent | 产出中该工具标记为不可用，missing 列表记录原因 | 自动化（结构化字段对比） |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0002-E-1 | 上游产出 status 为 blocked | 运行下游 Phase agent | 下游 status 为 blocked，不继续执行 | 自动化（status 字段） |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0002-F-1 | 上游产出文件不存在 | 运行下游 Phase agent | 报告前置条件不满足 | 自动化（异常捕获） |

---

# AC-0003: L3 能力基准

验证构造论文的端到端黑盒测试能力。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0003-N-1 | bench-001 论文包完整 | 运行完整 7 Phase 复现，重复 5 次 | 5 次 verdict 分布中 REPRODUCED ≥ 60% | 自动化 |
| AC-0003-N-2 | bench-001 论文包完整 | 运行 benchmark runner | 产出标准 result.json，字段完整 | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0003-B-1 | 论文包中 data/ 目录为空 | 运行 benchmark | 系统产出 BLOCKED 或 PARTIAL，不崩溃 | 自动化 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0003-E-1 | expected.yaml 格式错误 | 运行 evaluator | 报告配置错误，不崩溃 | 自动化 |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0003-F-1 | loopflow 执行超时 | 运行 benchmark | 记录超时，标记为 BLOCKED | 自动化 |