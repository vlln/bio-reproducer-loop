# Plan 010 — Fixed Worker Formal Smoke

| 文件 | 类型 | 状态 |
|------|------|------|
| [01-plan-fixed-worker-formal-smoke.md](01-plan-fixed-worker-formal-smoke.md) | Plan | done |
| [01-report-fixed-worker-formal-smoke.md](01-report-fixed-worker-formal-smoke.md) | Report | complete |

状态：done（验收未通过）。该 TEST_INFRA 执行容器证明 fixed worker readiness 成立，但唯一
`bench-001` formal run 暴露了 runtime archive 的跨 Docker image-store identity 缺陷，loopflow
仍未启动。真实 BLOCKED submission 与独立诊断已记录；未运行其他 entry、未建立 baseline，
也未修改 Plan 009 的 blocked submission。修复和下一次 formal smoke 必须进入新的 Plan。

计划分支：`test/0010-fixed-worker-formal-smoke`
