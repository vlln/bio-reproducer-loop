---
title: Plan 008 — QEMU/KVM Worker Test Infrastructure
description: 实现 disposable VM executor contract、QEMU/KVM 最小 backend、formal provenance/release gate，并在 gs 上完成真实 worker smoke。
type: plan
status: done
created: 2026-07-22T00:00:00Z
---

# 目标

依据 ADR-0009、Interface 0001 与 AC-0004，建立后续业务开发可依赖的 VM worker 测试基础：
formal run 只有 QEMU/KVM disposable VM；Docker sandbox 仍可快速验证，但其 submission
必须是 `validation-only`。本 Plan 使用极小 fake system 验证 worker，不解决完整
bio-reproducer system artifact 的构建与 entry 科学执行。

# 实施范围

1. 抽取 executor request/result/provenance contract，保留 Docker backend 兼容性。
2. 实现 QEMU/KVM backend：preflight、digest、fresh qcow2 overlay、virtiofs/9p attach、SSH
   readiness、deadline、QMP/ACPI shutdown 和残留审计。
3. 定义 runner-owned worker image 与 system directory 的最小 guest contract。
4. 让 adapter 写出 protocol v2 ExecutionEnvelope；Docker 标记 `validation-only`，VM 标记
   `formal` + `disposable-vm` + `qemu-kvm`。
5. 实现 release gate，拒绝缺少 completed teardown 或来自 validation backend 的 baseline。
6. 先以 fake process/provider 测试全部错误和清理分支，再在 `gs` 运行真实 VM smoke。
7. 将真实 VM smoke 做成显式 opt-in，不放进无 KVM 的普通单元测试。

# 非目标

- 不构建完整 bio-reproducer、MinerU、R/Bioconductor 或全部 benchmark 工具环境。
- 不运行六个 benchmark entry，不生成 baseline。
- 不实现 Firecracker、libvirt、snapshot restore 或 provider fallback。
- 不把 host Docker socket 暴露给 guest 或被测系统。
- 不修改 private evaluator 的科学评分规则。

# 验收条件

| 编号 | 条件 | 对应 AC |
|------|------|---------|
| WI-001 | Formal worker 固定 QEMU/KVM，KVM 不可用时稳定失败且无 fallback | AC-0008-E-1/E-5 |
| WI-002 | Worker/system digest 不匹配时 guest 不启动 | AC-0008-E-2 |
| WI-003 | Input 只读，workspace/output 可写，control plane 不可见 | AC-0008-N-2/F-2 |
| WI-004 | VM-local Docker 可运行 fake system container | AC-0008-N-1 |
| WI-005 | 成功/非零/timeout 都生成正确 provenance 并完成 teardown | AC-0008-N-3/N-4/F-1/F-3 |
| WI-006 | Docker result 为 validation-only，release gate 拒绝 | AC-0008-B-4 |
| WI-007 | 真实 worker cold boot 小于 60 秒 | AC-0008-N-1 |
| WI-008 | 普通确定性测试、bundle/lint 与真实 opt-in smoke 通过 | TEST_INFRA gate |

# 完成规则

全部 fake/contract tests 必须先通过。真实 smoke 只有在 `gs` 上证明 KVM、nested Docker、
I/O、oracle canary、artifact checksum 与 teardown 后才能将 Plan/Report 标为 done/complete。
