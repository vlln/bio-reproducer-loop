---
title: Report 024 — ClaroAI 批量校准（进行中）
description: BL-013 第一批（bench-220/222）校准运行状态：Reader/Bootstrap 完成，Provision 进行中（R 镜像拉取慢、libgl 依赖修复）。
type: report
status: draft
created: 2026-08-05T00:00:00Z
---

# 批量校准进展（BL-013，第一批）

## 运行状态

| entry | 论文 | 阶段 | 备注 |
|-------|------|------|------|
| bench-220 | SciTotalEnv epi (10.1016/j.scitotenv.2024.171511) | Provision（R 4.2.0 镜像 mip 拉取中） | Reader 完成（mineru 不可用 → pdfplumber fallback；补充材料 DOCX deferred）；Bootstrap 完成 |
| bench-222 | TorchXRayVision (arXiv:2111.00595) | Provision（torchxrayvision 镜像构建，libgl1-mesa-glx 依赖修复中） | Reader 完成（arXiv 论文 + 全文获取）；Bootstrap 完成（无 GPU 用 CPU、无 Nextflow） |

## 观测（真实世界复现）

1. **R 4.2.0 镜像拉取慢**：mip 加速拉取中，远端网络限制（与 BL-008 一致）
2. **libgl1-mesa-glx 不可用**：Debian Trixie 包变更，agent 修复 Dockerfile 中
3. **mineru-api 不可用**（同 bench-200）：agent fallback pdfplumber
4. 两篇均复用 bench-v3.sh（时间戳目录）+ runtime 镜像，并行无冲突

## 评估流程（运行完成后）

- evaluate_submission（已适配 verify.py：Markdown 表格解析）
- 校准对照：系统 verdict/审计判断 vs 作者 D1–D3 ground truth（claims.yaml calibration 段）
- 记录每篇 verdict、blocked 原因、时长

## 第一批校准结果（完成）

| entry | 论文 | 时长 | verdict（系统） | evaluator | 作者 calibration | 一致性 |
|-------|------|------|----------------|-----------|------------------|--------|
| bench-220 | SciTotalEnv epi | ~20h | REPRODUCED 100 | **REPRODUCED 100** | D1=2/D2=2/D3=2 | ✅ 数据/代码判断全一致 |
| bench-222 | TorchXRayVision | ~16h | REPRODUCED 100 | **REPRODUCED 100** | D1=2/D2=2/D3=2 | ✅ 数据/代码判断全一致 |

**校准发现**：
1. 第一批选 D2=2&D3=2 论文（数据+代码公开）→ 系统成功复现（与 bench-200 BLOCKED 对照，验证了"元数据分预测 D5"的 claroai-bench 结论）
2. verify 解析暴露并修复两个鲁棒性问题：a) 无 Status 列表格（bench-220 5 列格式）→ 表格解析泛化；b) accession 命名变体（NHANES III vs NHANES-III）→ 规范化模糊匹配
3. mip 被正确使用（mirrors/probe 正常，docker pull 是 mip 镜像源执行）；瓶颈是带宽非源选择

## 剩余

- 第一批其余 4 篇（bench-203/221/223/229）待批 1 完成后错峰启动
- 其余 28 篇（D2>0 之外）挂后续批次
