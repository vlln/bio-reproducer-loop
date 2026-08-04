---
title: Plan 013 - Tagged Runtime Formal Smoke
description: 使用已验证的 tagged runtime archive 和 fixed worker，正式 smoke 一次 bench-001 并保留真实结果。
type: plan
status: pending
created: 2026-07-29T11:22:43Z
---

# Context

Plan 011 的 fixed-worker formal smoke 证明 VM 和 Docker readiness 成立，但 runtime archive
使用构建机 image ID，导致 guest 在 loopflow 启动前返回 `BLOCKED`。Plan 012 已让 archive
携带固定内部 tag，结构化校验 tag/config binding，并在 fresh Docker 29 daemon 中通过
load/run probe。当前仍缺一次使用最新 `develop`、fixed worker 和 tagged runtime 的正式
system smoke。

# Request

在 `gs` 的全新 Plan 专属目录中 stage 当前受控 source，重新构建并验证 worker、runtime 和
opaque system artifact，然后通过 QEMU/KVM adapter 正式运行一次 `bench-001`。确认 loopflow
实际启动，保留真实 SubmissionBundle、ExecutionEnvelope、release-check 分类和 teardown
证据；system 或 scientific failure 不得伪装为成功。

# Output Format

- `01-report-tagged-runtime-formal-smoke.md`：记录 source、worker、runtime、artifact digest，
  门禁结果，唯一 formal submission，release-check，teardown 和 residue audit。
- 历史 Plan 009/011 的 blocked submission 保持不变；本 Plan 产生新的 submission ID。
- Report 必须逐项标记 Acceptance 的 PASS/FAIL，并把每项定位到命令输出或产物路径。

# Constraints

- 本 Plan 最多正式运行一次 `bench-001`；不得自动重试，不得运行其他 entry。
- 不生成或更新 baseline，不覆盖任何历史 submission。
- 正式路径只能是 `formal/disposable-vm/qemu-kvm`，不得回退 Docker 或 host。
- 使用 Plan 012 定义的 schema 1.1 tagged archive；launcher 只能使用校验后的内部 tag。
- Worker、runtime、artifact、InputBundle 和 secrets 通过显式 staging；oracle、仓库、其他
  entry、历史结果和 host runtime socket 不进入 guest。
- Secret 只记录逻辑名称；value 不写入 artifact、submission、日志或 Report。
- 长时间远端构建使用 `background-task`；不得因暂时无输出提前终止。
- 不修改远端 `~/bio-reproducer`；所有资产位于新的 Plan 专属 `/tmp` 根目录。
- 只清理本 Plan 创建的远端路径、容器、镜像、overlay 和进程。
- 不 push；只有用户明确要求时才 push。

# Checkpoints

| 编号 | 终止条件 |
|------|----------|
| CP-1 | 受控 source 已 stage，远端 home 状态已记录，确定性与 Docker 门禁通过 |
| CP-2 | Fixed worker、tagged runtime 和 artifact 通过 digest、archive、self-check 与 qcow2 校验 |
| CP-3 | 唯一 `bench-001` formal run 已产生 protocol-v2 submission，且有 loopflow 实际启动证据 |
| CP-4 | Release-check 分类完成，teardown 完整，Plan 资产清理且 remote home hash 未变化 |

若 worker readiness、digest、KVM、mount、secret staging、tag binding 或 teardown 失败，分类为
infrastructure defect，并在消费唯一 formal run 前尽量阻断。若 formal run 已开始后返回
blocked、failed 或 timeout，保留真实结果并停止，不在本 Plan 内重跑。

# Steps

1. 记录本地与远端 source commit、远端 home status hash，创建唯一 Plan 临时根目录。
2. 在 staged source 上运行确定性测试、显式 Docker probes、lint、bundle validators 和
   `git diff --check`。
3. 通过 `background-task` 构建并校验 fixed worker、tagged runtime 和 system artifact；记录
   worker qcow2、runtime archive、runtime reference、config ID 与 artifact tree digest。
4. 使用 fresh daemon load/run probe 再次确认 archive tag 可作为 guest locator，并检查正式
   运行前无残留 QEMU、container 或 overlay。
5. 通过 QEMU/KVM adapter 正式运行一次 `bench-001`，记录 loopflow 启动证据，不得自动重试。
6. 校验 SubmissionBundle 和 ExecutionEnvelope，执行 release-check，并分类真实业务结果。
7. 完成 teardown、清理 Plan 专属资产、复核 remote home hash，填写 Report 并关闭 Plan。

# Acceptance

| 编号 | 条件 | 对应 AC |
|------|------|---------|
| TF-001 | Worker ready、qcow2 digest/check、runtime tag/config/archive binding 全部通过 | AC-0008-N-1 |
| TF-002 | 唯一 run 为 formal/disposable-vm/qemu-kvm，InputBundle 边界成立 | AC-0008-N-1/N-2 |
| TF-003 | loopflow 实际启动；submission 保留真实 success/blocked/failed/timeout 与 artifacts | AC-0008-N-3/F-3 |
| TF-004 | ExecutionEnvelope 记录 worker/system digest、network、deadline 和 teardown | AC-0008-N-4 |
| TF-005 | Release-check 结果与 provenance、blocked 原因和 teardown 状态一致 | AC-0008-F-1/F-3 |
| TF-006 | Guest 无法看到 oracle、repository、host Docker socket 或其他 control-plane 资产 | AC-0008-F-2 |
| TF-007 | 未运行其他 entry、未建立 baseline、未修改历史 submission 或远端 home 项目 | DEVELOP gate |
| TF-008 | 合并态确定性测试、Docker probes、lint、bundle validators 与 diff check 全绿 | DEVELOP gate |
