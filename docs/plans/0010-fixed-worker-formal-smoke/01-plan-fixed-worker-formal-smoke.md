---
title: Plan 010 — Fixed Worker Formal Smoke
description: 使用严格验证 Docker provisioning 的 disposable VM worker，正式 smoke 一次 bench-001 并分类系统执行结果。
type: plan
status: pending
created: 2026-07-27T00:00:00Z
---

# Context

Plan 009 已构建 opaque bio-reproducer system artifact，但唯一正式 `bench-001` 在 loopflow
启动前因原 worker 缺少 Docker 返回 `BLOCKED`。根因是 cloud-init package 安装失败后旧配方
仍无条件写 ready marker。配方现已要求 `docker`、active daemon 和 `docker.io` package 全部
存在，独立 VM probe 已验证修复有效；尚缺一次 fixed-worker formal system smoke。

# Request

在 `gs` 的全新 Plan 专属目录中，从当前受控 source 重新构建 worker、runtime 和 system
artifact，通过 QEMU/KVM adapter 正式运行一次 `bench-001`。保留真实 submission、执行
envelope、release-check 分类与 teardown 证据，不把 system/scientific failure 伪装成成功。

# Constraints

- 本 Plan 最多正式运行一次 `bench-001`；不得重试、不得运行其他 entry。
- 不生成或更新 baseline，不修改 Plan 009 的历史 blocked 观测。
- 正式路径只能是 `formal/disposable-vm/qemu-kvm`，不得回退 Docker 或 host。
- Worker、runtime、artifact、input 和 secrets 均通过显式 staging；oracle、仓库和历史结果不进入 guest。
- Secret 只记录逻辑名称；value 不写入 artifact、submission、日志或 Report。
- 长时间远端构建使用 `background-task`，下载中不得仅因暂时无输出而终止。
- 不修改或清理远端 `~/bio-reproducer`；所有 Plan 资产位于新的 `/tmp` 目录。
- 只清理本 Plan 创建的远端路径、容器和镜像。
- 不 push；只有用户明确要求时才 push。

# Checkpoints

| 编号 | 终止条件 |
|------|----------|
| CP-1 | 本地确定性门禁通过，Plan source 可重建且 remote home 状态已记录 |
| CP-2 | Fixed worker、runtime 和 artifact 构建并通过 digest/self-check/qcow2 校验 |
| CP-3 | 一次 bench-001 formal run 产生真实 protocol-v2 submission，loopflow 已实际启动 |
| CP-4 | Release-check 分类、teardown、远端 residue audit 和最终本地门禁完成 |

若 worker readiness、digest、KVM、mount、secret staging 或 teardown 失败，分类为 infrastructure
defect并停止正式运行或发布判断。若基础设施成立后 system/scientific execution 返回 blocked、
failed 或 timeout，保留实际结果，不自动重跑。

# Steps

1. 运行普通 tests、Docker opt-in probes、lint 和六个 bundle validator。
2. 记录远端 `~/bio-reproducer` status hash，创建唯一 Plan 临时根目录并 stage 当前 commit。
3. 通过 background-task 构建并校验 control image、fixed worker、runtime 和 system artifact。
4. 在正式运行前确认 worker 内 Docker readiness、artifact digest、无残留 QEMU/container。
5. 通过 QEMU/KVM adapter 正式运行一次 `bench-001`，不得从失败点自动重试。
6. 对 submission 执行 release-check，审计 ExecutionEnvelope、artifacts 与 teardown。
7. 清理 Plan 专属远端资产，复核 home status hash 和本地全量门禁，完成 Report。

# Acceptance

| 编号 | 条件 | 对应 AC |
|------|------|---------|
| FS-001 | Worker ready 前验证 Docker CLI、daemon 和 package，qcow2 digest/check 有证据 | AC-0008-N-1/F-3 |
| FS-002 | Artifact/runtime 从固定输入重建并通过 manifest、tree 和 archive digest 校验 | AC-0008-N-4/E-2 |
| FS-003 | 唯一 run 为 formal/disposable-vm/qemu-kvm，且 loopflow 已实际启动 | AC-0008-N-1/N-2 |
| FS-004 | Submission 保留真实 success/blocked/failed/timeout 结果和 system/worker digest | AC-0008-N-3/N-4/F-1 |
| FS-005 | Release-check 给出与失败分类一致的接受或拒绝结果 | AC-0008-B-3/F-3 |
| FS-006 | Teardown 四项完整，Plan 路径、容器、镜像和 QEMU 无残留 | AC-0008-F-3 |
| FS-007 | 未运行其他 entry、未建立 baseline、未修改远端 home 项目 | DEVELOP gate |
| FS-008 | 普通 tests、Docker probes、lint、bundle validators 与 diff check 全部通过 | DEVELOP gate |
