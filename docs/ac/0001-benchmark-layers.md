---
title: AC 001 — 基准测试分层
description: 五层测试体系（L1-L5）的验收标准，覆盖各层的核心能力验证。
type: ac
status: proposed
created: 2026-07-15T00:00:00Z
---

# AC-0001: L1 单 Agent 可靠性

验证单个 Phase Agent 在给定输入下的行为可靠性和稳定性。

## L1 异常判定的机制

L1 测试通过 loopflow 的 mock 模式运行，不依赖真实 LLM。Mock 模式根据 output schema 自动生成合规数据——**它不处理输入内容**。因此，L1 的异常场景判定分为两类：

**A 类：可自动化判定的**
- 产出是否遵循 output schema（status 字段有效、必填字段存在）
- Agent 是否崩溃（exit code ≠ 0）
- 多次运行产出的 status 是否一致

**B 类：需构造输入 + 真实 LLM 判定的**
- Agent 对异常输入的语义处理是否合理
- 这类场景由 L3 黑盒测试覆盖，L1 不做

L1 的边界/异常/失败场景只验证 A 类：Agent 不崩溃、产出 schema 合规、status 字段反映了异常状态。不对"Agent 是否真正理解了异常"做判断。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0001-N-1 | golden_plan.md 存在且有效 | 运行 Reader agent，传入论文 PDF 路径 | 产出符合 output schema，status 为 completed | 自动化 |
| AC-0001-N-2 | 构造的 Bootstrap 输入 | 运行 Bootstrap agent | 正确检测系统环境，产出符合 schema | 自动化 |
| AC-0001-N-3 | 同一输入、同一 Phase | 连续运行 5 次 | 5 次 status 一致，关键决策点一致 | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 | 判定类别 |
|------|---------|---------|---------|---------|---------|
| AC-0001-B-1 | 论文 PDF 路径指向不存在的文件 | 运行 Reader agent | Agent 不崩溃，产出 status 为 blocked 或 failed | 自动化（exit code + status 字段） | A |
| AC-0001-B-2 | 上游产出中某些必填字段缺失 | 运行下游 Phase agent | 不崩溃，产出 schema 中 status 正确 | 自动化（schema 校验） | A |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 | 判定类别 |
|------|---------|---------|---------|---------|---------|
| AC-0001-E-1 | 输入参数类型错误（如 paper_path 传入数字而非字符串） | 运行任意 Phase agent | Agent 不崩溃，产出标记异常的 status | 自动化（exit code + status 字段） | A |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 | 判定类别 |
|------|---------|---------|---------|---------|---------|
| AC-0001-F-1 | loopflow 后端不可用 | 运行任意 Phase agent | 抛出 AgentError，不静默失败 | 自动化（exit code） | A |

---

# AC-0002: L2 跨 Phase 信息流

验证 Phase 之间的信息传递正确性和非完美上游的处理能力。

## L2 异常判定的机制

与 L1 相同，L2 的异常场景只验证 A 类（自动化可判定）：Agent 不崩溃、产出 schema 合规、status 字段反映了上游的异常状态。语义正确性（如"下游是否做了正确的降级决策"）由 L3 黑盒测试覆盖。

构造异常输入的方式：手工创建带缺陷的上游产出文件（如 Data Requirements 为空的 plan.md、工具 status 为 failed 的 provision.md），喂给下游 Agent。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0002-N-1 | golden_plan.md 包含完整 Data Requirements | 运行 Data agent | 正确提取所有 accession，产出 data_manifest.md | 自动化 |
| AC-0002-N-2 | golden_plan.md + golden_provision.md 存在 | 运行 Run agent | 正确引用已部署工具和参数 | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 | 判定类别 |
|------|---------|---------|---------|---------|---------|
| AC-0002-B-1 | plan.md 中 Data Requirements 表为空 | 运行 Data agent | 不崩溃，产出 status 为 partial 或 blocked | 自动化（exit code + status） | A |
| AC-0002-B-2 | provision.md 中某工具 status 为 failed | 运行 Run agent | 不崩溃，产出 status 反映异常，payload 含 missing 记录 | 自动化（status + schema 校验） | A |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 | 判定类别 |
|------|---------|---------|---------|---------|---------|
| AC-0002-E-1 | 上游产出 status 为 blocked | 运行下游 Phase agent | 不崩溃，产出 status 为 blocked | 自动化（exit code + status） | A |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 | 判定类别 |
|------|---------|---------|---------|---------|---------|
| AC-0002-F-1 | 上游产出文件不存在 | 运行下游 Phase agent | 不崩溃，报告前置条件不满足 | 自动化（exit code + status） | A |

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