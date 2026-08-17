---
title: Report 025 — scored_scope 删除与 ClaroAI claims 模式落地
description: 删除 scored_scope 机制（字段/adapter 透传/CC-002/verify 锚点），ClaroAI entry 恢复 claims 模式（D5 数值声明转录 + 容差 comparator），6 篇校准 run 离线重评并与作者 D5 校准对照。
type: report
status: complete
created: 2026-08-12T00:00:00Z
---

# 实现结论

## 背景与动机

1. **迁移任务降级**：转换时把 ClaroAI-Bench 原始任务（D5 结果匹配的 claim 级复现）
   改写成了 D1–D3 元数据审计（`scored_scope=d1_d3_audit`）。"可复现性审计"只是
   claims 缺失时的临时形态——正确做法是补齐 claims（论文定量声明），而非改任务。
2. **评估设计泄漏**：`scored_scope` 是评分维度代码，经 adapter 原样注入被测系统
   prompt，泄漏了评估设计；且被测系统不理解该代码（bench-221 误读为"膳食模式
   D1/D3"，bench-223 误读为"MCF-7 + SLL 数据集"），导致越界重活与慢运行。
3. **claims 本可转录**：`scores.json` D5 evidence 包含 `pub=/repr=` 等论文数值声明
   （31/35 篇有），converter 可半自动转录为数值 ground truth。

## 交付物

| 项 | 内容 |
|----|------|
| converter v0.2.0 | 删除 `scored_scope`/`audit_scope` 发射；新增 `reproduction_target=result_verification` + 自然语言 `task`；D5 claims 从 scores.json evidence 转录（4 种格式解析：pub=repr / reproduced=published / 单行 HR= / match paper 计数）；rubric 生成 A1/A2（D1–D3 证据，各 15）+ C* claims checks（check_claim，合计 70）；verify.py 模板新增 `check_claim`（relative/absolute 容差 + gte/lte 阈值 + JSON/Markdown 两种 evidence 解析） |
| entries（35 个 bench-200+） | 全部重生成（数据引用/代码引用/校准分/input 与旧版逐字段一致，零漂移验证）；`scored_scope` 移除，`reproduction_target` + `task` 补齐；bench-223 手工补 AUROC>0.95 阈值 claim |
| bench-100 | `scored_scope` 自然语言描述迁移为 `reproduction_target` + `task` |
| adapter | 不再透传 `scored_scope`；改读 `metadata.task` 翻译为 loop `scope` 参数 |
| validator | CC-002 rev.：bench-200+ 必须声明 `reproduction_target` + 非空 `task`，禁止 `scored_scope`；CC-003/004 保留 |
| evaluate_run.py | 支持 `--claims-evidence`（legacy run 手工映射）与 `06_validate/report.md` 自动装载（role=validate_report） |
| 测试 | converter/validator/adapter 测试更新 + 新增回归（维度代码禁入系统侧、check_claim 容差、scored_scope 拒绝）；全量 **141 passed, 4 skipped**；42 个 entry 全部通过 bundle gate |
| 文档 | ADR-0010 修订块、Interface 0002 v2、Spec 0001（接入段/BR-018/术语）、AC-0005、本 Report |

## 6 篇校准 run 离线重评（claims 模式 vs 作者 D5 校准）

对已归档 run 只取证据文件（data_manifest/provision/validate report），不改动 run，
离线跑独立 evaluator；bench-220/221 的 claims evidence 从各自 validate 报告逐条手工映射
（跨语言指标名无法自动对齐，已作为 legacy-run 证据提取步骤记录）。

| entry | 系统 verdict（新） | 系统旧 verdict | 作者 D5 | 解读 |
|-------|-------------------|----------------|---------|------|
| bench-220 | **REPRODUCED 100** | REPRODUCED 100 | 2 | 3 个 HR claims 全部匹配；与作者一致 ✓ |
| bench-221 | **REPRODUCED 65** | REPRODUCED 100 | 2 | 8 个 claims 中 4 个被复现（fs_enet/pc2 × 全因/癌症），pc1/hei.2015 未报告；旧审计评分高估 |
| bench-222 | REPRODUCED 100（无 claims） | REPRODUCED 100 | 2 | paper_23 scores.json 无 D5 evidence，无数值 claims 可转录；仅 D1–D3 证据评分，作者 D5=2 不可对照 |
| bench-203 | **PARTIAL 30** | REPRODUCED 100 | 2 | A1/A2 通过；LME p 值 claim 未复现（run 为审计形态） |
| bench-200 | **FAILED 0** | REPRODUCED 90 | 2 | Fig4A DEG claims 未复现（run 未做 DEG 分析）；A1 因作者 D2=0 低估与系统实际下载成功冲突而失败 |
| bench-223 | **FAILED 15** | BLOCKED | 2 | AUROC claim 未复现（scMKL alpha bug 阻塞）；A1 失败 |
| bench-229 | **FAILED 15** | BLOCKED | 1 | 4 个 barcode count claims 未复现（run 阻塞）；A1 失败 |

结论：
- **claims 评分闭环端到端可用**（无需重跑，直接消费既有 run 产物）；
- 修正了审计模式的高估：bench-200 旧 REPRODUCED 90 → FAILED 0（未复现论文声明）；
  bench-203 旧 REPRODUCED 100 → PARTIAL 30；bench-221 旧 100 → 65；
- 与作者 D5 校准的对照扩展到 D5 维度：bench-200/203/223 作者 D5=2 而系统未复现
  claims——作者 D5 高估/系统能力差距双向可见（与 bench-200 D2 低估同属校准双向发现）。

## 端到端验证（2026-08-17，bench-220 claims 模式正式重跑）

| 链路环节 | 证据 |
|----------|------|
| 新任务说明 → loop | run.json `"scope": "复现该论文报告的关键定量结果（Blood lead CVD HR...）"`；`d1_d3_audit` 计数=0（含 bench-v3.sh 硬编码修复） |
| → Reader 解读 | plan.md Reproduction Target = T1–T3 三个 HR claims + 数据/代码核查，out-of-scope 明确 |
| → 系统执行 | ~1 小时完成（上次 8h23m）：provision 复用 bone-lead-mortality 镜像（7m），Run 产出 Table 2/3 真实结果 |
| → claims 复现 | validate R1–R6 HR 精确匹配（血铅 1.633903784 vs 1.63），PAF 偏差 ≤0.9pp |
| → 自动解析评分 | evaluate_run.py 纯自动（含中文表头/数值邻近匹配修复）：**REPRODUCED 100**，5/5 checks PASS |
| 作者 D5 对照 | 作者 D5=2 → 系统 100，一致 ✓ |

结论：claims 模式端到端链路成立；scope 语义修复同时消除越界重活（8x 提速）。
归档：`/storeData/gs/claroai-calibration/runs/bench-220`（旧 run 存 legacy 目录），
calibration-assets.md 已登记。

## 遗留

1. **无 D5 evidence 的 4 篇**（paper_09/10/23/26 → bench-208/209/222/225）：claims 需
   从论文表格人工补全（bench-222 属已校准 6 篇，D5 校准对照不可用）。
2. **claims evidence 自动解析已打通**（后续补丁 fix(0025)-2）：`_normalize` 保留
   CJK、千位分隔符解析、`_match_row` 数值邻近回退——bench-220/221 的 legacy run 用
   原始 validate 报告即可自动评分（无需手工映射）；bench-223 的 AUROC 0.992 也从
   run 报告自动命中（0.992 ≥ 0.95，与作者同值）。仍建议后续 run 产出结构化
   claims evidence JSON（role=validate_report）作为首选契约，Markdown 解析为回退。
3. **全 35 篇的 claims 转录质量**需逐篇 fidelity review（尤其格式 4 `match paper`
   计数与阈值型声明）。
4. 系统侧运行时的越界重活（provision 全量环境等）属 loop 执行层问题，不在本
   Plan 范围（见 docs/plans/README 后续 backlog 建议）。
