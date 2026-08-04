---
title: AC 001 — 测试、评测与基准分域
description: 确定性软件测试、内部 LLM 行为评测和公开 benchmark 的验收标准。
type: ac
status: active
created: 2026-07-15T00:00:00Z
---

# AC-0001: 确定性软件测试

验证 runner、adapter、evaluator 和 workflow 契约在无真实 LLM、网络与工具部署时可重复运行。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0001-N-1 | fake executor 返回合法 submission | 运行 evaluator 单元测试 | 按 oracle 计算 check、score 和 verdict | 自动化 |
| AC-0001-N-2 | 相同 fixture 与随机种子 | 断网连续运行 `pytest tests/` 两次 | 收集项和结果完全一致 | 自动化 |
| AC-0001-N-3 | Phase 返回 partial/blocked | 运行契约测试 | workflow 按契约传播或停止 | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0001-B-1 | submission 缺少可选 claimed_verdict | 运行 evaluator | 正常评分，calibration 标为 unavailable | 自动化 |
| AC-0001-B-2 | 某 optional artifact 缺失 | 运行 evaluator | 仅对应 check 为 NA/partial，不崩溃 | 自动化 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0001-E-1 | manifest 路径越界或 artifact 不存在 | 运行 evaluator | 返回 INVALID_SUBMISSION，不读取工作区外文件 | 自动化 |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0001-F-1 | fake executor 非零退出且无产物 | 运行测试 | 测试失败，不得通过或 skip | 自动化 |

---

# AC-0002: 内部 LLM 行为评测

验证单 Phase 业务能力和跨 Phase 语义传递，真实 LLM 运行结果用分布表达。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0002-N-1 | Reader fixture + claims oracle | 同配置运行 Reader 5 次 | 报告 claims precision/recall、幻觉数及分布 | 自动化评测 |
| AC-0002-N-2 | 完整上游 fixture | 运行下游 Phase 5 次 | 报告关键信息保留率与成功率 | 自动化评测 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0002-B-1 | 上游 partial 且字段缺失 | 运行 handoff eval | 报告正确降级率和编造率 | 自动化评测 |
| AC-0002-B-2 | 工具状态 failed | 运行 Run eval | 不可用工具不应被报告为成功执行 | 自动化评测 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0002-E-1 | LLM 后端不可用 | 运行 eval | 记录 infrastructure_error，不计为业务失败 | 自动化评测 |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0002-F-1 | Phase 无产物或进程非零退出 | 运行 eval | 本次 run 明确失败，不得视为可接受输出 | 自动化评测 |

---

# AC-0003: L3 能力基准

验证构造论文的端到端黑盒测试能力。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0003-N-1 | bench-001 input 与 oracle 完整且隔离 | 运行完整复现 5 次并独立评估 | evaluator verdict 分布达到 rubric 阈值 | 自动化 |
| AC-0003-N-2 | submission bundle 完整 | 运行 benchmark evaluator | evaluator 产出带 provenance 的标准 result.json | 自动化 |
| AC-0003-N-3 | 正确产物但 claimed_verdict 为 FAILED | 运行 evaluator | 按实际产物评分，claimed verdict 只影响 calibration | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0003-B-1 | input/data/ 目录为空 | 运行 benchmark | evaluator 根据实际恢复产物或阻塞证据判定，不崩溃 | 自动化 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0003-E-1 | oracle/rubric.yaml 格式错误 | 运行 evaluator | 返回 INVALID_ORACLE，不计为系统能力失败 | 自动化 |
| AC-0003-E-2 | submission artifact 路径越界 | 运行 evaluator | 返回 INVALID_SUBMISSION，拒绝读取 | 自动化 |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0003-F-1 | loopflow 执行超时 | 运行 benchmark | 记录超时，标记为 BLOCKED | 自动化 |
| AC-0003-F-2 | 系统 claimed score=100 但产物错误 | 运行 evaluator | 独立检查失败，最终 score 不采用 claimed score | 自动化 |
