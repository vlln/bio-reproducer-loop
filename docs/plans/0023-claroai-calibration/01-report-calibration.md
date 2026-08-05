---
title: Report 023 — ClaroAI 校准运行（进行中）
description: bench-200 校准运行状态：全链路打通（Reader/Bootstrap/Provision/Data 阶段真实执行），审计判断与作者 ground truth 吻合；Data 阶段受参考基因组下载瓶颈，运行完成待续。
type: report
status: draft
created: 2026-08-05T00:00:00Z
---

# 校准运行进展（BL-012）

## 已完成的基建打通（本轮）

| 环节 | 结果 |
|------|------|
| Runtime 镜像重建 | `bio-reproducer-runtime:system`（2.09GB，build-runtime.sh） |
| System artifact | `/tmp/bl012/system-artifact`（loop 源 + 7 技能 + launcher，validate 通过） |
| 远端技能修复 | 解引用 4 个 skit symlink + 补 3 技能 + 权限修复 |
| LLM 凭据注入 | `~/.claude/settings.json` 复制进容器 HOME（deepseek-v4-pro via dashscope） |
| loop 挂载 | LOOPFLOW_LOOPS_DIR + RUNS_DIR 解决 HOME 权限问题 |
| Docker CLI | agent 自主 pixi 安装（Bootstrap 自愈） |

## bench-200 校准运行（docker 模拟 VM 边界，`/tmp/bl012/run-bench-200-1785919086`）

| 阶段 | 状态 | 关键产物/证据 |
|------|------|--------------|
| Reader | ✅ 完成 | `01_plan/plan.md`（25KB，T1/T2 目标 + out-of-scope 标注）；L5 自行获取论文 PDF（7.8MB）+ PMC 全文 + mmc1.pdf |
| Bootstrap | ✅ 完成 | `02_bootstrap/bootstrap.md`；Java 23/Nextflow 26.04.6/Docker 验证；Docker Hub+quay 可达性测试 |
| Provision | ✅ 完成 | `03_provision/provision.md`；10 工具部署（复用 8 镜像 + 构建 2），Nextflow 10/10 进程通过 |
| Data | ⏳ 进行中 | `04_data/data_manifest.md`（8KB）；GSE308855 COMPLETED；SRA 清单全枚举；GRCm39 参考基因组下载中（~600MB/~3GB，~200KB/s） |

## 关键审计发现（与作者 ground truth 对照）

data_manifest.md 显示系统对 paper_01 的 D1/D2 审计判断：
- **Figure 源数据 NOT_AVAILABLE**（IVIS/肺重/肿瘤数据未公开）→ 与作者 D2=0（数据不可获取）一致
- **GitHub 仓库无 Figure 1/3 源数据**（仅 RNAseq/Methylation 文件）→ 与作者 D3=1（代码空壳/不全）一致
- **SRA WGS 数据 AVAILABLE**（32 条目 ~1.2TB）→ 数据可定位（D1）
- mmc1.pdf BLOCKED（PMC/ScienceDirect 不可达）→ 外部依赖真实阻碍

## 运行状态

- 总时长 ~21h（真实 agent 逐步执行 + 远端网络慢速）
- 运行健康（每阶段真实产出，无卡死）
- watcher 已部署（`/tmp/bl012/watch.sh`，完成时标记 run-done.txt）
- 运行完成后续：评估（evaluate_submission）+ 校准对照表 + 抽样 bench-201~205

## 环境发现（已解决或记录）

1. qemu 未装 + 无 KVM 权限 → docker 模拟 VM 边界（容器隔离 + controlled 网络，与 VM launcher 同构）
2. Docker Hub 被墙（registry-1.docker.io 超时）→ agent 用本地镜像复用 + pip 替代
3. mineru-api 未配置 → agent fallback PyPDF2 + PMC HTML
4. 参考基因组下载慢（~200KB/s）→ Data 阶段瓶颈
