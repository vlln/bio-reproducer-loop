# Plan 007 — VM Runtime Boundary Design

| 文件 | 类型 | 状态 |
|------|------|------|
| [01-plan-vm-runtime-boundary.md](01-plan-vm-runtime-boundary.md) | Plan | pending |
| [01-report-vm-runtime-boundary.md](01-report-vm-runtime-boundary.md) | Report | draft |

状态：in progress。该执行容器只完成 disposable VM 正式运行边界的 ADR、Spec、Interface
与 AC 设计传导，不实现 VM runner。设计审查通过并冻结后，由后续 TEST_INFRA 执行容器
实现 worker backend。

计划分支：`docs/0007-vm-runtime-boundary`
