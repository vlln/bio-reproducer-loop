## 执行容器

| 容器 | 分支 | 状态 |
|------|------|------|
| [0001-benchmark-infra](0001-benchmark-infra/) | — | done |
| [0002-l4-l5](0002-l4-l5/) | — | pending |
| [0003-evaluation-boundaries](0003-evaluation-boundaries/) | `refactor/0003-evaluation-boundaries` + stacked closeout | done |
| [0004-input-bundle-fidelity](0004-input-bundle-fidelity/) | `refactor/0004-input-bundle-fidelity` | done |
| [0005-runtime-isolation](0005-runtime-isolation/) | `refactor/0005-runtime-isolation` | done |
| [0007-vm-runtime-boundary](0007-vm-runtime-boundary/) | `docs/0007-vm-runtime-boundary` | done |
| [0008-vm-worker-backend](0008-vm-worker-backend/) | `test/0008-vm-worker-backend` | done |
| [0009-system-artifact](0009-system-artifact/) | `feat/0009-system-artifact` | done |
| [0010-fixed-worker-formal-smoke](0010-fixed-worker-formal-smoke/) | `test/0010-fixed-worker-formal-smoke` | done (acceptance failed) |
| [0011-runtime-archive-reference](0011-runtime-archive-reference/) | `test/0011-runtime-archive-reference` | done |

当前阶段：DEVELOP。Plan 006 在保留的 `spike/0006-vm-isolation` 分支验证了 KVM/QEMU、
VM-local Docker、I/O boundary、oracle 隔离和完整 teardown；Plan 007 已将结论冻结到
ADR-0009、Spec v4、Interface 0001 与 AC-0004。Plan 005 的 Docker sandbox 保留为开发/CI
validation backend，不再作为可发布结果的正式边界。Plan 008 已实现最小 QEMU/KVM
worker contract、fake tests、release gate 与 `gs` 真实 VM smoke。Plan 009 已构建 opaque
bio-reproducer system artifact；唯一正式 `bench-001` run 暴露并推动修复了 worker
provisioning 缺陷。修复后的 worker 已独立通过 VM 验证，新的正式 smoke 留给后续执行容器。
Plan 010 证明 fixed worker readiness 成立，但唯一 formal smoke 暴露 runtime archive 在不同
Docker image store 中加载为不同 image ID，因而 loopflow 仍未启动。Plan 011 已改用 archive
内固定 tag 作为 guest 运行引用，并完成 archive metadata 校验与 fresh-daemon load/run gate；
下一步才可提出新的最小 formal smoke。
