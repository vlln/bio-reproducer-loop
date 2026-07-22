---
title: Report 007 — VM Runtime Boundary Design
description: 记录 disposable VM 正式边界的设计传导、内容审查、测试结果和待审核项。
type: report
status: draft
created: 2026-07-22T00:00:00Z
---

# 当前状态

设计草案与跨文档一致性检查已完成，等待用户内容审查。该 Report 不声称 VM runner 已经
实现；Plan/Report 在冻结前继续保持 `pending`/`draft`。

# 设计传导

| 文档 | 目标变化 | 状态 |
|------|----------|------|
| ADR-0009 | 采用 disposable VM，Docker sandbox 降为 validation backend | proposed |
| Spec 0001 v4 | 增加正式执行环境与发布规则 | proposed |
| Interface 0001 | 增加 ExecutionEnvelope、生命周期和错误语义 | proposed |
| AC-0004 | 增加 VM runtime 正常/边界/异常/失败验收 | proposed |
| ADR-0008 | 保留 taxonomy/resource reuse，将 runtime 表述指向 ADR-0009 | revised |

# 验证结果

| Gate | 结果 | 证据 |
|------|------|------|
| 确定性测试 | PASS | `73 passed, 4 skipped` |
| Bundle validator | PASS | bench-001/002/004/005/006/100 全部 `VALID` |
| YAML/frontmatter lint | PASS | `make lint` 无错误或 warning |
| Diff hygiene | PASS | `git diff --check` 无错误 |
| Runtime implementation | NOT RUN | 本 Plan 明确不实现 VM runner |

# 待审核

1. Runner-owned worker image + opaque system artifact 是否足以保持系统黑盒与跨系统兼容。
2. `offline` / `controlled-egress` 是否只表达网络策略，而不会重新形成多 runtime 路径。
3. Validation-only Docker backend 是否应长期保留在同一 CLI，还是后续移入测试工具。
4. Teardown 失败使整个 run 不可发布，而不是只产生 warning。

# 冻结后动作

内容审查通过后：

1. 将 ADR-0009 从 `proposed` 提升为 `accepted`。
2. 将 Spec 0001 v4、Interface 0001 与 AC-0004 从 `proposed` 提升为 `active`。
3. 将 Plan/Report 更新为 `done`/`complete`，同步 README 与 CHANGELOG。
4. 合并 design 文档分支后，另建 TEST_INFRA 执行容器实现最小 VM worker backend。
