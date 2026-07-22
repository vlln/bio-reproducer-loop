---
title: Plan 007 — Formalize Disposable VM Runtime Boundary
description: 将已验证的 disposable VM 决策传导到 ADR、Spec、Interface、AC 与项目状态，不在本 Plan 实现 runner。
type: plan
status: pending
created: 2026-07-22T00:00:00Z
---

# 目标

把 Plan 006 spike 的可行性结论转化为可审查的正式设计：公开 benchmark 只有一个正式
disposable VM runtime；被测系统在 guest 内可自由使用 Pixi、Docker 或其他工具链；可信
control plane 留在 VM 外。完成设计冻结后再创建 TEST_INFRA Plan 实现 VM runner。

# 实施范围

1. 新增 ADR-0009，比较 host Docker、Docker socket、多 runtime 路径与 disposable VM。
2. 将 Spec 0001 升至 v4，增加 FormalExecution 数据模型、业务规则和非功能指标。
3. 修订 Interface 0001，定义 VM lifecycle、ExecutionEnvelope、provenance 与错误语义。
4. 新增 AC-0004，覆盖正常、边界、异常和失败场景。
5. 修订 ADR-0008 中受影响的 runtime 表述，但保留 taxonomy 与资源复用决策。
6. 更新各级 README 状态和索引，明确项目从 TEST_INFRA 退回 DESIGN。
7. 执行内容一致性审查、frontmatter 检查和现有确定性测试。

# 非目标

- 不实现 QEMU/KVM、VM provider、image builder 或 scheduler。
- 不修改 `benchmarks/runner/`、CLI 或现有 Docker integration tests。
- 不构建 bio-reproducer 完整镜像，不运行六个 benchmark entry。
- 不删除 Plan 005；其 Docker sandbox 作为 validation backend 保留。
- 不 merge Plan 006 spike 分支，不 push 任一分支。

# 验收条件

| 编号 | 条件 |
|------|------|
| VD-001 | ADR 明确只有 disposable VM 能生成正式结果 |
| VD-002 | Pixi/OCI 是 guest 内实现细节，不进入 entry/runtime enum |
| VD-003 | Interface 明确 control plane、I/O、network、deadline 与 teardown |
| VD-004 | AC 覆盖 VM-local Docker、oracle escape、output 回收和残留 worker |
| VD-005 | Docker validation result 不能进入 baseline |
| VD-006 | Spec、Interface、ADR、AC 和 README 状态无冲突 |
| VD-007 | `git diff --check` 与现有确定性测试通过 |

# 审查门禁

本 Plan 先将 ADR、Spec、Interface 和 AC 置为 `proposed`。用户完成内容审查后才可将
ADR 标记为 `accepted`，将 Spec/Interface/AC 标记为 `active`，并把 Plan/Report 收尾。
