## 执行容器

| 容器 | 分支 | 状态 |
|------|------|------|
| [0001-benchmark-infra](0001-benchmark-infra/) | — | done |
| [0002-l4-l5](0002-l4-l5/) | — | pending |
| [0003-evaluation-boundaries](0003-evaluation-boundaries/) | `refactor/0003-evaluation-boundaries` + stacked closeout | done |
| [0004-input-bundle-fidelity](0004-input-bundle-fidelity/) | `refactor/0004-input-bundle-fidelity` | done |
| [0005-runtime-isolation](0005-runtime-isolation/) | `refactor/0005-runtime-isolation` | done |
| [0007-vm-runtime-boundary](0007-vm-runtime-boundary/) | `docs/0007-vm-runtime-boundary` | in progress |

当前阶段：DESIGN。Plan 006 在保留的 `spike/0006-vm-isolation` 分支验证了 KVM/QEMU、
VM-local Docker、I/O boundary、oracle 隔离和完整 teardown。Plan 007 正在把该结论传导
到正式 ADR、Spec、Interface 与 AC；设计冻结前不修改 runner。Plan 005 的 Docker sandbox
保留为开发/CI validation backend，不再作为可发布结果的正式边界。
