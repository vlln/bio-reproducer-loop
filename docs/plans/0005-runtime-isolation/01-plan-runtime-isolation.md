---
title: Plan 005 — Benchmark Runtime Isolation
description: 为 benchmark 被测系统建立 OS/container 级文件系统边界，证明其无法越过 staged InputBundle 读取 control plane 或其他运行资产。
type: plan
status: done
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

# 隔离设计

Runner/Curator 与 private evaluator 属于可信宿主控制面，被测系统只在 Docker container
内执行。Container 仅挂载 `/input`（只读）、`/workspace`（可写）和 `/output`（可写）；
仓库、其他 entry、历史结果、`.git`、private oracle 和 Docker socket 均不挂载。根文件系统
只读，进程使用宿主非 root UID/GID，移除全部 capabilities，启用 `no-new-privileges`，
并限制 CPU、memory、PID、timeout。`/tmp` 与 sandbox HOME 使用有容量限制的 tmpfs。

Runner 不继承完整宿主环境。只有 `--pass-env NAME` 或
`BIO_REPRODUCER_SANDBOX_PASS_ENV` 明确列出的变量名可进入 container。未配置
`--sandbox-image`/`BIO_REPRODUCER_SANDBOX_IMAGE` 时直接拒绝执行，不回退到宿主运行。

| Profile | 网络 | 用途 |
|---------|------|------|
| `offline` | `none` | 输入与运行依赖均已冻结，不允许外部发现 |
| `discovery` | Docker bridge | 允许论文、数据或其他外部资源发现 |
| `tool-runtime` | Docker bridge | 允许模型/API 网络，但科学工具必须预装在被测镜像中 |

Profile 由 entry 的执行契约选择，不由 L3/L4/L5 编号单独推导。L5 通常需要
`discovery`；L3/L4 可按材料和任务使用 `offline` 或 `tool-runtime`。三种 profile 均禁止
挂载宿主 Docker socket。

# Threat Model

本 Plan 防止被测程序通过绝对路径、相对路径、相邻目录、工作目录或历史结果读取
control plane，也限制其修改 staged input、container root 和非指定宿主目录。它不承诺
防御 container runtime/kernel 漏洞，也不防御已被显式传入凭据的恶意程序经允许网络
外传凭据；联网 profile 的 API key 只应授予最小权限和独立额度。

# 非目标

- 不修改 InputBundle resource inventory 或 private oracle 内容。
- 不在本 Plan 冻结 bench-100 的历史生物信息学工具链；该工作属于 Plan 002。
- 不建立或发布 benchmark baseline。
- 不构建包含完整 loopflow 与特定论文历史工具链的发布镜像。

# 完成条件

- 自动测试证明被测进程不能读取 staged input 与允许运行时之外的文件。
- control-plane escape probe 在真实 Docker 环境通过，并接入 CI 独立 gate。
- 三种 profile 的网络与 runtime mount 策略均有自动化覆盖。
- Report 记录平台限制、性能开销和无法完全隔离的宿主能力。
