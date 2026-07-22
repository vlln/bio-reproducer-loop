## 执行容器 0005 — Benchmark Runtime Isolation

| 文件 | 类型 | 状态 |
|------|------|------|
| [01-plan-runtime-isolation.md](01-plan-runtime-isolation.md) | Plan | done |
| [01-report-runtime-isolation.md](01-report-runtime-isolation.md) | Report | complete |

状态：done。Docker sandbox、三种 execution profile、host execution 禁用、env allowlist、
timeout 强制清理、真实 escape probe 与 CI gate 已实现。验证按隔离能力取样，不重复运行
全部 entry；具体 bio-reproducer/L4 image 仍由 Plan 002 负责。

计划分支：`refactor/0005-runtime-isolation`
