---
title: Plan 024 — ClaroAI 批量校准运行
description: 其余 34 篇 entry 的完整 loopflow 校准（BL-013）：复用 runtime/artifact + bench-v3.sh，按 D2>0 优先，第一批 D2=2&D3=2 论文并行校准，对照作者 D1–D3 ground truth。
type: plan
status: pending
created: 2026-08-05T00:00:00Z
---

# Context

bench-200 校准已验证全链路（docker 模拟 VM 边界，~27h/篇，verdict BLOCKED 与作者一致）。
BL-013：其余 34 篇 entry 完整校准。单篇 ~27h → 并行分批；优先作者 D2>0 的 18 篇，
其中 D2=2&D3=2 的 6 篇（数据+代码都可用）复现判定最有意义，作为第一批。

# Request

1. 复用远端 runtime（bio-reproducer-runtime:system）+ bench-v3.sh（参数化 entry），
   并行启动第一批校准（2-3 篇/批，避免压垮远端——背景 28 容器）
2. 每篇产出：完整 7 阶段产物 + verdict + 审计判断（data_manifest/provision/validate report）
3. 运行完成后评估（evaluate_submission + 校准对照），对照 claims.yaml calibration 段
4. 记录每篇 verdict、blocked 原因、时长、审计判断 vs 作者分数

# 第一批（D2=2&D3=2，6 篇优先）

| entry | paper | 论文 | 预期 |
|-------|-------|------|------|
| bench-220 | paper_21 | SciTotalEnv epi (10.1016/j.scitotenv.2024.171511) | 数据公开，可复现路径清晰 |
| bench-222 | paper_23 | TorchXRayVision (arXiv:2111.00595) | pip 包 + 开放数据集，最快候选 |
| bench-203 | paper_04 | MRI diffusion (10.1002/mrm.70258) | MATLAB 代码 + NITRC 数据 |
| bench-221 | paper_22 | Cancer Causes Control (10.1007/s10552-024-01868-2) | 调查数据 |
| bench-223 | paper_24 | Comm Biol genomics (10.1038/s42003-025-08533-7) | 计算基因组 |
| bench-229 | paper_30 | Genome Biol single-cell (10.1186/s13059-024-03173-2) | 单细胞多组学 |

# Constraints

- 复用 bench-v3.sh（时间戳目录避免清理问题）；每篇独立 run 目录
- 并行 ≤3 篇（远端 24 核/755GB 内存/224GB 磁盘，背景有其他项目）
- 每篇最多正式运行 1 次，不自动重试；blocked 保留真实结果
- 评估用已适配的 verify.py（Markdown 表格解析，c5212ee 后）

# Checkpoints

| 编号 | 终止条件 |
|------|----------|
| CP-1 | 第一批 6 篇全部启动（3 篇/批 × 2 批） |
| CP-2 | 每篇产出 submission 级产物 + verdict |
| CP-3 | 校准对照表完成（6 篇 verdict/blocked 原因 vs 作者 D1–D3） |
| CP-4 | Report 024 完成，BL-013 进度记录（剩余 28 篇挂后续） |

# Steps

1. 验证 bench-v3.sh 参数化（远端）
2. 启动批 1（bench-220 + bench-222 并行）
3. 启动批 2（bench-203 + bench-221）等批 1 完成或错峰
4. 每篇完成后评估 + 校准对照
5. Report 024 + 更新 BL-013 状态
