# Plan 013 - Tagged Runtime Formal Smoke

| 文件 | 类型 | 状态 |
|------|------|------|
| [01-plan-tagged-runtime-formal-smoke.md](01-plan-tagged-runtime-formal-smoke.md) | Plan | pending |
| 01-report-tagged-runtime-formal-smoke.md | Report | - |

状态：pending。使用 Plan 012 已验证的 tagged runtime archive 和 fixed worker，在 disposable
QEMU/KVM VM 中正式运行一次 `bench-001`，证明 loopflow 实际启动并保留真实 submission、
release-check 与 teardown 证据。本 Plan 不运行其他 entry，也不建立 baseline。

计划分支：`test/0013-tagged-runtime-formal-smoke`
