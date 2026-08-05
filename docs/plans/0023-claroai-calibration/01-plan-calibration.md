---
title: Plan 023 — ClaroAI 校准运行
description: 重建 system artifact/runtime，在远端 gs disposable VM 中跑 bench-200~205 审计模式 entry，产出确定性评分 vs 作者分数的校准观测（BL-012）。
type: plan
status: pending
created: 2026-08-04T00:00:00Z
---

# Context

BL-011 已交付 35 个 L5 审计 entry（bench-200~234），本地确定性验证全过（136 测试、
35-entry 评分冒烟）。正式校准需在 disposable VM 真实跑 loopflow 7 阶段，但 Plan 013
后 system artifact/runtime 已清理（formal backend 报 WORKER_UNAVAILABLE）。本 Plan 按
Plan 013 流程重建并跑抽样校准。

# Request

1. 远端 `gs` 重建 tagged runtime（`build-runtime.sh` → `bio-reproducer-runtime:system`）
   与 opaque system artifact（`build_system_artifact`，loop=loops/bio-reproducer）
2. 校验 worker（既有 worker.qcow2 e18b50a8）、runtime、artifact digest
3. 跑 bench-200~205（6 篇抽样，覆盖多模态）formal VM 校准，`--network-policy controlled-egress`
4. 评估 submission（`bench-run eval`），对照 `claims.yaml` 的 calibration 段（作者分数）
   产出校准观测

# Output Format

- `/tmp/bl012/` 构建资产（runtime tar、artifact 树、summary）
- `benchmarks/results/bench-2xx/run_01/submission.json` + result.json
- 本容器 Report：校准对照表（独立 verdict/score vs 作者 D1–D3）

# Constraints

- 正式路径只能是 formal/disposable-vm/qemu-kvm，不回退 Docker/host
- 不生成/覆盖 baseline；不 push
- 每 entry 最多正式运行 1 次，不自动重试
- Secret 只记录逻辑名；远端构建用后台任务（nohup），不得因无输出提前终止

# Checkpoints

| 编号 | 终止条件 |
|------|----------|
| CP-1 | runtime/artifact 构建校验通过（digest、tag binding、validate-system） |
| CP-2 | bench-200 首个 formal run 产生 protocol-v2 submission 且有 loopflow 启动证据 |
| CP-3 | bench-201~205 抽样完成或记录 blocked 原因 |
| CP-4 | 校准对照表完成，teardown 完整 |

# Steps

1. 记录远端 source commit，创建 /tmp/bl012
2. 构建 runtime（后台）→ 构建 system artifact → validate
3. formal run bench-200（观察 loopflow 启动）→ 评估
4. 抽样 bench-201~205 → 评估
5. 对照 calibration 段写校准表，Report，清理
