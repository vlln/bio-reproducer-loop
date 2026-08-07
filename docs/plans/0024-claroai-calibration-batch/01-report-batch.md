---
title: Report 024 — ClaroAI 批量校准（第一批总结）
description: BL-013 第一批（D2=2&D3=2 六篇）校准完成：4 篇 REPRODUCED 100 与作者一致；2 篇 BLOCKED 根因经方法学审查后修正（系统参数/环境因素，非纯论文问题），已启动重跑验证。
type: report
status: complete
created: 2026-08-05T00:00:00Z
---

# 批量校准总结（BL-013，第一批 D2=2&D3=2 六篇）

## 结果表

| entry | 论文 | 系统 verdict | evaluator | 作者 cal | 校准 |
|-------|------|-------------|-----------|----------|------|
| bench-220 | SciTotalEnv epi | REPRODUCED 100 | REPRODUCED 100 | 222 | ✅ 一致 |
| bench-222 | TorchXRayVision | REPRODUCED 100 | REPRODUCED 100 | 222 | ✅ 一致 |
| bench-203 | MRI diffusion | REPRODUCED 100 | REPRODUCED 100 | 222 | ✅ 一致 |
| bench-221 | Cancer Control | REPRODUCED 100 | REPRODUCED 100 | 222 | ✅ 一致（首次失败重启后） |
| bench-223 | BLOCKED | — | 222 | ⚠️ **根因待验证**（见下） |
| bench-229 | BLOCKED | PARTIAL 50 | 222 | ⚠️ **根因混合**（见下） |

## 校准结论（经方法学审查修正）

> **修正前**："作者评分高估可复现性（2/6 系统受阻）"。
> **修正后**：4/6 REPRODUCED 100 与作者一致（数据+代码公开 → 可复现，结论可靠）；2/6 BLOCKED
> 的根因经审查**不能简单归因作者高评**：

### bench-223（scMKL）——系统参数路径问题，非论文 bug（审查证据）

- 系统 run 脚本 `run_mcf7_multimodal.py` 使用 `alpha_list = np.geomspace(0.05, 1.0, 10)`——
  **alpha=1.0 是系统自己选择的参数范围**（论文方法学未明确指定），触发 scMKL 0.1.6 的
  `'list' object has no attribute 'tolist'` 崩溃
- 原结论"作者 D3=2 vs 论文代码 bug"**不成立**——是复现系统未找到正确参数路径
- **验证**：已启动重跑（新 run），观察 agent 是否从论文方法学得出正确 alpha 范围

### bench-229（Genome Biol）——系统网络限制 + 真实数据限制混合

- GEO SSL 断连（GSE232222 13.5GB 大文件）：**系统远端网络限制**（数据实际可下载，下载中断），
  非数据不可得——系统环境因素
- KPMP Atlas 需浏览器注册：**真实访问限制**（论文数据受控）
- GSE220289 仅提供 FASTQ 无处理矩阵：**论文数据公开不完整**（论文问题）
- evaluator PARTIAL 50 的 2 个剩余 FAIL：KPMP UUID / Zenodo DOI 变体 = verify 命名对齐的
  已知极限（claims 用 UUID/DOI 号，系统 manifest 用名字）

## verify 迭代（校准驱动，5 轮）

Markdown 表格/属性-值表/URL 行/状态词/大小写归一化/out-of-scope NA/命名变体模糊匹配。
结论：verify 能可靠解析真实系统产物；命名语义对齐有极限（UUID/DOI 变体），已知限制记录。

## 重跑状态（验证根因 + 补产物）

| entry | 状态 | 目的 |
|-------|------|------|
| bench-200 | 重跑中（Reader 完成） | 补全丢失产物（镜像缓存） |
| bench-220 | 重跑中（Provision） | 补全丢失产物 |
| bench-222 | 重跑中（Provision，复用缓存镜像） | 补全丢失产物 |
| bench-223 | 重跑中（Reader） | 验证 scMKL alpha 参数路径 |

## 资产状态

- 已归档：`/storeData/gs/claroai-calibration/runs/{bench-203,221,223,229}`（完整产物）
- 丢失后重跑：bench-200/220/222（首次批量归档误操作）
- 规范：`benchmarks/calibration-assets.md` + `evaluate_run.py`（入库）+ AGENTS.local.md 目录约定
