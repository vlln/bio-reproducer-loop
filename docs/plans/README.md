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
| [0009-system-artifact](0009-system-artifact/) | `feat/0009-system-artifact` | pending |

当前阶段：DEVELOP。Plan 006 在保留的 `spike/0006-vm-isolation` 分支验证了 KVM/QEMU、
VM-local Docker、I/O boundary、oracle 隔离和完整 teardown；Plan 007 已将结论冻结到
ADR-0009、Spec v4、Interface 0001 与 AC-0004。Plan 005 的 Docker sandbox 保留为开发/CI
validation backend，不再作为可发布结果的正式边界。Plan 008 已实现最小 QEMU/KVM
worker contract、fake tests、release gate 与 `gs` 真实 VM smoke。Plan 009 正在构建 opaque
bio-reproducer system artifact，并以一个构造 entry 验证正式 adapter 路径。
