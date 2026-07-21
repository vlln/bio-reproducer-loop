---
title: Plan 005 — Benchmark Runtime Isolation
description: 为 benchmark 被测系统建立 OS/container 级文件系统边界，证明其无法越过 staged InputBundle 读取 control plane 或其他运行资产。
type: plan
status: pending
created: 2026-07-21T00:00:00Z
---

# 目标

将 Plan 004 的 staging contract 扩展为可验证的运行时隔离：被测系统只能读取本次 staged
`input/` 和必要运行时，只能向指定 submission/work 目录写入，不能读取仓库中的
`bundle.yaml`、`metadata.yaml`、`oracle/`、其他 entry、历史结果或宿主机敏感路径。

# 实施范围

1. 选择并记录 container/sandbox 边界、只读挂载、工作目录和 UID/GID 策略。
2. 将 adapter 的运行输入收敛为显式 mount 与环境变量，不传入宿主仓库路径。
3. 定义网络策略；允许在线发现的 level 与完全离线 level 使用不同 profile。
4. 添加恶意探针测试，尝试读取 entry control plane、相邻 entry、Git 历史和宿主路径。
5. 验证 submission artifact 仍可收集，失败与超时仍能生成协议化结果。

# 非目标

- 不修改 InputBundle resource inventory 或 private oracle 内容。
- 不在本 Plan 冻结 bench-100 的历史生物信息学工具链；该工作属于 Plan 002。
- 不建立或发布 benchmark baseline。

# 完成条件

- 自动测试证明被测进程不能读取 staged input 与允许运行时之外的文件。
- control-plane escape probe 在本地与 CI 目标环境均被拒绝。
- 网络策略与 L3/L4/L5 level 约束一致且有失败场景覆盖。
- Report 记录平台限制、性能开销和无法完全隔离的宿主能力。
