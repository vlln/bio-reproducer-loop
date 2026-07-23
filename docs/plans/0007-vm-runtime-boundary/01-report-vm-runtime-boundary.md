---
title: Report 007 — VM Runtime Boundary Design
description: 记录 disposable VM 正式边界的设计传导、内容审查、测试结果和待审核项。
type: report
status: complete
created: 2026-07-22T00:00:00Z
---

# 当前状态

设计草案、跨文档一致性检查与用户内容审查已完成。ADR-0009、Spec v4、Interface 0001
与 AC-0004 已冻结；该 Report 不声称 VM runner 已经实现。

# 设计传导

| 文档 | 目标变化 | 状态 |
|------|----------|------|
| ADR-0009 | 采用 QEMU/KVM disposable VM，Docker sandbox 降为 validation backend | accepted |
| Spec 0001 v4 | 增加正式执行环境与发布规则 | active |
| Interface 0001 | 增加 ExecutionEnvelope、生命周期和错误语义 | active |
| AC-0004 | 增加 VM runtime 正常/边界/异常/失败验收 | active |
| ADR-0008 | 保留 taxonomy/resource reuse，将 runtime 表述指向 ADR-0009 | revised |

# 验证结果

| Gate | 结果 | 证据 |
|------|------|------|
| 确定性测试 | PASS | `73 passed, 4 skipped` |
| Bundle validator | PASS | bench-001/002/004/005/006/100 全部 `VALID` |
| YAML/frontmatter lint | PASS | `make lint` 无错误或 warning |
| Diff hygiene | PASS | `git diff --check` 无错误 |
| Runtime implementation | NOT RUN | 本 Plan 明确不实现 VM runner |

# 用户审查结论

1. 接受 disposable VM 作为唯一正式边界；旧 Docker/protocol v1 结果只作历史观测。
2. 接受最小 worker image：Ubuntu 基础设施、control/I/O 支持与预装 VM-local Docker；不含
   bio-reproducer、论文工具、entry input、oracle 或 secret。
3. 接受所有 entry 使用同一 VM runtime；`offline` / `controlled-egress` 只表达网络策略。
4. 接受 teardown 失败使本次 run 无效但不扣系统科学能力分数，可以清理后重试。
5. 接受当前 backend 为 QEMU/KVM、fresh qcow2 overlay、virtio/virtiofs 与 QMP，cold boot
   目标小于 60 秒；暂不引入 Firecracker、snapshot restore 或其他 provider。

Docker validation backend 最终保留在正式 CLI 还是移入测试工具属于 Plan 008 实现边界，
不影响其 `validation-only` 协议语义。

# 后续动作

合并 design 文档分支后，另建 TEST_INFRA 执行容器实现最小 VM worker backend。实现必须先
覆盖 AC-0008 的 fake provider/contracts，再在 `gs` 上完成 QEMU/KVM cold boot、nested
Docker、I/O、timeout 和 teardown smoke。
