# Plan 010 — Fixed Worker Formal Smoke

| 文件 | 类型 | 状态 |
|------|------|------|
| [01-plan-fixed-worker-formal-smoke.md](01-plan-fixed-worker-formal-smoke.md) | Plan | pending |
| [01-report-fixed-worker-formal-smoke.md](01-report-fixed-worker-formal-smoke.md) | Report | draft |

状态：pending。该 TEST_INFRA 执行容器使用已修复 provisioning contract 的 worker，重新构建
opaque system artifact，并正式运行一次 `bench-001`，补足 Plan 009 未能证明的 loopflow
启动路径。它不运行其他 entry，不建立 baseline，也不修改 Plan 009 的 blocked submission。

计划分支：`test/0010-fixed-worker-formal-smoke`
