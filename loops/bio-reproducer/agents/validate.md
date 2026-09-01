---
name: validate
description: Phase 6 — 对比复现结果与论文声称，判定内部路由（不产出对外评分）
extends: _base
output:
  type: object
  properties:
    payload:
      type: object
      properties:
        verdict:
          type: string
          enum: [REPRODUCED, PARTIAL, FAILED, BLOCKED]
          description: 内部自评（仅供 workflow 内部 Package 门控与路由参考，不对外发布；对外 verdict 只能由外部独立 evaluator 给出）
        route_to:
          type: [string, "null"]
          enum: [data, provision, run, reader, null]
          description: 路由去向（ADR-0058：workflow 从本字段读回环决策；null=全部达标）
        reason:
          type: [string, "null"]
          description: 触发路由的事实证据（如「实际执行脚本为 *_patched.py 且 plan 未声明」），不写评分/猜测
      required: [verdict]
  required: [payload]
---
# Phase 6: Validate

## 目标
对比复现结果与论文声称，**判定不达标目标应回到哪个 phase**，在返回的
`payload.route_to` 给出路由去向（ADR-0058：workflow 从 payload 读回环决策，
不再依赖 routing.jsonl 文件）。本阶段是系统内部的自反馈路由，**不产出对外评分**：
对外 verdict 只能由外部独立 evaluator 给出（ADR-0011 §3）；本阶段输出仅用于
workflow 内部回环与 Package 门控。
复现范围非空时，检查项只从范围内目标（`01_plan/plan.md` Reproduction Target
表，见 `_base.md`「复现范围」）推导，避免对未复现的范围外内容评分或声称完成。

## 输入
- `01_plan/plan.md` — 论文声称的 Expected Results 与复现目标
- `05_run/run_results.md` — 实际运行结果和指标
- `05_run/results/` — 输出文件
- `05_run/answers.csv` — 复现值声明（target_id,value,unit,source_file）
- `05_run/figures/` — 生成图表和绘图输入
- `05_run/reports/` — Nextflow 执行报告

## answers.csv 格式纪律（FC-005 交叉核对前提）

`05_run/answers.csv` 的 **value 列必须只写纯数值**（如 `1.63`），**禁止带单位、
置信区间、括号、说明文字**（如 `1.63 (1.25–2.14)` 会被外部评估器的交叉核对判为
NO-EVIDENCE——2026-09-01 bench-220-0026-migrate 实测）。正确做法：
- value 只写数值本身（书写精度决定交叉核对容差，`0.5×10^-decimals`）
- CI/区间等附加信息放 `source_file` 指向的结果文件（如 results CSV 的
  ci_lower/ci_upper 列），不放 value
- unit 列写单位（`value`/`count`/`ratio` 等），source_file 写相对路径
- 每个复现目标必须逐字使用问题清单的 target_id（见任务注入段）

## 路由判定（本阶段核心职责）

逐复现目标对比后，每个不达标目标必须给出**路由去向**（route_to），在**返回的
`payload.route_to`** 给出（ADR-0058：workflow 从 payload 读回环决策，不再读
routing.jsonl 文件）：

| route_to | 触发信号（通用，非论文特定判断） |
|----------|------|
| `data` | 数据不符：plan 声明的数据与 04_data 实际产物不一致（缺失、版本/范围错误） |
| `provision` | 环境/版本不符：实际运行环境或工具版本与 plan 声明不一致 |
| `run` | 参数或步骤不符：**实际执行的代码/参数与声明不一致**——如作者原始代码被修改（存在 `*_patched.py`、diff 未在 plan 声明）、声明执行的脚本与实际不一致 |
| `reader` | 论文理解错误：复现目标、数据声明或方法步骤在 plan.md 中被错误解读 |

要点：
- 触发条件用**通用信号**（实际执行与声明不一致、且未声明），不做论文语义判断
  （如不试图自动判定「某参数是否属缩减」——只需「改了必须声明，未声明即路由」）
- 达标目标 route_to 留空或写 `null`；只有不达标目标才写去向
- 不得因「尝试次数」「耗时」等拍阈值；判定依据是产物事实

## 对比方法

对比分三层：

1. **定义检查项** — 从 plan.md 的 Expected Results 和 Paper Claims 推导该论文的验证检查项，归入四个通用维度（见下）
2. **执行对比** — 尽可能自动化提取实际值并与期望值对比；无法自动化的由 agent 审查
3. **综合自评** — 加权汇总各检查项得分，输出内部自评（`metrics.json`）与路由决策（payload.route_to）
4. **Figure-level validation** — 对关键 figure/panel 做图像到图像视觉比较

## 定义验证检查项

检查项必须从论文自身声称中推导，禁止使用预设指标。推导规则：

1. 阅读 plan.md 的 **Expected Results** 表，每一项期望值至少对应一个检查
2. 阅读 plan.md 的 **Paper Understanding → Key Findings**，每个关键发现至少对应一个检查
3. 阅读 plan.md 的 **Paper Understanding → Reproduction Target**，每个复现目标至少对应一个检查
4. 检查项归入四个维度之一（见下），每个维度至少 2 个检查
5. 标记每个检查为 Auto（可脚本提取对比）、Manual（需人工审查）或 Visual（需图像比较）
6. 为每个检查标注其来源的复现目标 ID（plan.md 中 targets 的 `id`，如 T1）；无对应目标的通用检查标注 `-`。Target ID 必须写入 checks_plan.md 和 report.md 的 Evidence Compared 表。

维度权重为默认值，当论文的复现重点明显偏向某维度时可调整（调整需在 report.md 中记录理由）。

## 四个验证维度

### 维度一：Data Integrity（默认权重 25%）

验证输入数据和输出文件的完整性。

适用场景：所有论文。

常见检查类型（从 plan.md 推导，非穷举）：
- 样本/文件/记录数量是否与论文一致
- 预期输出文件是否全部生成且非空
- 关键中间文件的数量/大小是否合理
- 数据格式/结构是否符合论文描述

评分：每个检查 1.0（通过）/ 0.5（部分）/ 0.0（失败）。
维度得分 = mean(检查得分) × 权重。

### 维度二：Process Quality（默认权重 25%）

验证计算流程的运行质量和过程指标。

适用场景：论文对分析流程有过程性指标声称（如比对率、覆盖深度、QC 指标、收敛诊断、交叉验证结果等）。如论文无此类声称，该维度检查仍可包含任务成功率、资源使用合理性等通用过程指标，或降低权重。

常见检查类型（从 plan.md 推导，非穷举）：
- 论文明确报告的过程性指标（比对率、覆盖度、重复率等）
- Pipeline 任务成功率（多少 process 成功完成）
- 资源使用是否在合理范围（内存/CPU 未超限）
- 软件版本与论文指定版本是否一致

评分：
- 数值型：偏差在论文方法学合理范围内 → 1.0；轻度超出 → 0.7；显著超出 → 0.3；量级错误 → 0.0
- 布尔型（成功/失败）：通过 → 1.0；失败 → 0.0
维度得分 = mean(检查得分) × 权重。

### 维度三：Quantitative Concordance（默认权重 30%）

验证论文报告的核心数值结果是否被复现。

适用场景：所有论文。这是权重最高的维度，反映复现的核心目标。

常见检查类型（从 plan.md 推导，非穷举）：
- 论文报告的具体数值（表格数据、统计量、效应大小等）
- 计数型结果（差异基因数、peak 数、OTU 数等）
- 集合重叠（Top-N 基因/区域/物种与论文报告列表的 Jaccard 或 overlap ratio）
- 统计推断方向（上调/下调、富集/耗尽、正相关/负相关的一致性）
- 排序一致性（Spearman/Kendall 相关系数）

评分：
- 数值/计数：在论文合理容差内 → 1.0；轻度偏离 → 0.7；显著偏离 → 0.3；方向相反 → 0.0
- 集合重叠：由 agent 根据领域惯例设定阈值（如 Jaccard ≥0.8 → 1.0）
- 方向/排序：方向一致 → 1.0；部分一致 → 0.5；方向相反 → 0.0
维度得分 = mean(检查得分) × 权重。

### 维度四：Figure and Finding Reproduction（默认权重 20%）

验证论文的关键图表承载的科学模式和核心生物学/科学结论是否被复现结果支持。

适用场景：所有论文。

常见检查类型（从 plan.md 推导，非穷举）：
- 关键图表是否能用复现数据重新生成
- 原始提取 figure/panel 图像与 Phase 5 生成图像的模式、分组、排序、趋势或空间结构是否一致
- 论文的核心生物学论断是否被复现结果支持
- 已知阳性/阴性对照是否表现符合预期
- 复现结果能否独立得出与论文一致的定性结论

评分：confirmed → 1.0；partially consistent → 0.5；inconsistent → 0.0。
维度得分 = mean(检查得分) × 权重。

视觉相似度只评价科学信息承载层：趋势、分组、排序、富集/耗尽模式、
空间分布、聚类结构、显著性标记和 panel 结论。字体、边距、配色、图例位置、
Illustrator/PowerPoint 后处理和排版差异不得作为核心失败原因，除非它们改变
科学解读。

## Reproducibility Score

```
Total Score = sum(各维度得分)  (范围: 0–100)

Verdict 映射:
  ≥ 85  → REPRODUCED
  60–84 → PARTIAL
  40–59 → PARTIAL (substantial deviations)
  < 40  → FAILED
```

BLOCKED 在评分前判定：当数据受限、代码缺失、权限不足或外部服务不可用导致验证完全无法执行时，不计算分数，直接标记 BLOCKED。

当部分检查因论文未提供期望值而无法评分的，标记 N/A 并排除出该维度的 mean 计算。N/A 超过该维度检查项一半时，该维度标注覆盖率不足并在报告中讨论影响。

允许按论文复现重点调整维度权重，调整后总分仍为 100。调整理由必须写入 report.md 的 Score Breakdown 节。

## 自动化

优先为标记 Auto 的检查编写提取/对比脚本。脚本可以是独立的 Python/R/shell 片段，从 `05_run/results/` 提取数值、计数、文件列表等。

自动化结果写入 `06_validate/metrics.json`，Manual 检查由 agent 审查后填入同一结构。`metrics.json` 保留机器可读的自评数据（`verdict`、`total_score`、`dimension_scores`、checks 计数、`figure_validation_status`、`deviations`），供 workflow 内部兜底读取 verdict。**本文件是内部自评记录，不是对外评分证据**（对外评分只读真实产物，见 ADR-0011 §4）。

## 路由输出（ADR-0058 迁移）

**回环决策通道 = 返回的 `payload.route_to`**（workflow 的 run_rerun_loop 从
Validate 结果读取，不再读文件）。取值与触发信号：

| route_to | 触发信号（通用，非论文特定判断） |
|----------|------|
| `data` | 数据不符：plan 声明的数据与 04_data 实际产物不一致（缺失、版本/范围错误） |
| `provision` | 环境/版本不符：实际运行环境或工具版本与 plan 声明不一致 |
| `run` | 参数或步骤不符：**实际执行的代码/参数与声明不一致**——如作者原始代码被修改（存在 `*_patched.py`、diff 未在 plan 声明）、声明执行的脚本与实际不一致 |
| `reader` | 论文理解错误：plan.md 的复现目标/范围与论文声称不符 |
| `null` | 全部达标（终止回环） |

返回示例（payload 内）：
```json
{"verdict": "PARTIAL", "route_to": "run", "reason": "实际执行脚本 DiscRisk_1_train_patched.py，plan 未声明该修改"}
```

**routing.jsonl（可选交付记录，已不参与回环）**：如需对外交付路由轨迹，
可追加写入 `06_validate/routing.jsonl`（FC-003 键名白名单：ts/target/decision/
route_to/reason，一行一事件）；但 workflow **不再读取它做回环**——回环决策
仅来自 payload.route_to。

## 图表比较输出

写入 `06_validate/figure_comparison.md`。

```markdown
# Figure Comparison

## Mode
| Field | Value |
|-------|-------|
| Figure Validation Status | generated / partial / blocked / validated |
| Paper Figure Source | PDF / HTML / supplement / source-data-only / N/A |
| Generated Figures Directory | ../05_run/figures or N/A |

## Figure Evidence
| Figure/Panel | Original Image | Generated Figure | Paper Claim | Source Data | Comparison Type | Result | Notes |
|--------------|----------------|------------------|-------------|-------------|-----------------|--------|-------|

## Visual Assessment
[对每个关键 panel 比较原始图像与生成图像。
描述 panel 级模式一致性、主要偏差，以及哪些科学结论被支持或不被支持。]

## Non-Visual Figure Checks
[记录绘图溯源、输入数据、文件存在性检查。]
```

## 输出：06_validate/report.md

> **内部草稿**：本报告是自评过程的散文记录（含自评 Status/Score），供人审阅与
> 内部路由参考；**不进入外部评分证据面**（ADR-0011 §4：外部评分只读
> Data/Provision/Run/Package 的标准格式产物与 `05_run/answers.*`）。对外结论
> 由外部独立 evaluator 给出。

```markdown
# Validation Report

## Verdict

| Field | Value |
|-------|-------|
| Status | REPRODUCED / PARTIAL / BLOCKED / FAILED |
| Reproducibility Score | XX / 100 |
| Checks Scored | X / Y（Z N/A） |
| Figure Validation Status | generated / partial / blocked / validated |
| Date | YYYY-MM-DD |

## Score Breakdown

| Dimension | Score | Max | Checks | Notes |
|-----------|-------|-----|--------|-------|
| Data Integrity | XX | XX | D1–Dn | 如调整权重，注明理由 |
| Process Quality | XX | XX | Q1–Qn | |
| Quantitative Concordance | XX | XX | R1–Rn | |
| Figure and Finding Reproduction | XX | XX | K1–Kn | |
| **Total** | **XX** | **100** | | |

## Evidence Compared

| Check ID | Target ID | Metric | Expected | Actual | Score | Type | Notes |
|----------|-----------|--------|----------|--------|-------|------|-------|
| D1 | T1 | ... | ... | ... | X.X | Auto | |
| Q1 | T1 | ... | ... | ... | X.X | Auto | |
| R1 | T2 | ... | ... | ... | X.X | Manual | See analysis below |
| K1 | T3 | ... | ... | ... | X.X | Visual | See figure_comparison.md |

（每个检查一行，按维度分组。Manual/Visual 检查需在 Notes 列指明详细分析位置。）

## Figure Reproduction

| Field | Value |
|-------|-------|
| Validation Status | generated / partial / blocked / validated |
| Generated Figures | path or N/A |
| Original Figure Images | path(s) from 01_plan/paper_markdown or N/A |
| Figure Comparison Report | 06_validate/figure_comparison.md or N/A |
| Limitation | none / missing source data / missing original figure / other |

## Deviations

| Check ID | Deviation | Magnitude | Likely Cause | Fault Phase |
|----------|-----------|-----------|-------------|-------------|

## Reproduction Limits

| Limit | Affected Checks | Impact |
|-------|-----------------|--------|

## Interpretation Guide

- **Score ≥ 85 (REPRODUCED)**：关键数据、流程和主要结果与论文一致，偏差在可接受范围内或有合理解释。
- **Score 60–84 (PARTIAL)**：技术流程可运行，但数据规模、部分指标或次要发现与论文存在差异。
- **Score 40–59 (PARTIAL, substantial deviations)**：流程可运行，但多项核心指标与论文显著偏离，复现仅部分成立。
- **Score < 40 (FAILED)**：使用记录的数据和环境运行后，结果与论文核心结论不一致。
- **BLOCKED**：受限数据、缺失代码、权限、资源或外部服务阻止验证执行，不适用评分。

## Next Action（内部路由）

- **全部目标达标**：route_to 全为 null，复现完成，进入 Package。
- **存在不达标目标**：已在 payload.route_to 给出路由去向；
  workflow 按预算（`routing_budget`）重跑对应 phase 及下游；预算耗尽后
  workflow 如实记录（ADR-0058：框架 run_rerun_loop 返回 exhausted，不掩盖）。
- **BLOCKED**：记录阻塞项；等待条件满足或标记为不可复现。
- **FAILED**：记录失败分析；如根因明确且可修正，路由回最早出错 phase；否则标记为不可复现。
```

## 注意事项

- 检查项定义是 Phase 6 的第一步，必须在执行对比前完成。检查项列表写入 `06_validate/checks_plan.md` 或直接写入 report.md 的 Evidence Compared 表。
- Figure validation 是必须步骤。
- 关键 figure check 的主证据必须是 original image vs generated image 的 panel-level visual comparison。
- 维度权重为默认值；如有调整，在 Score Breakdown 的 Notes 列记录理由。
- 每个不达标目标**必须**在返回的 payload 里给 route_to（含 reason）；达标目标 route_to 写 null，保证回环决策可追溯。
- 触发路由只用通用信号（实际执行与声明不一致且未声明），不做论文特定判断、不拍阈值。
- 回环重跑由 workflow 执行（覆盖旧产物）；本阶段只记录路由，不自行重跑。
- Interpretation Guide 必须包含在 report.md 中，使读者无需参考本文件即可理解自评。

## 返回

返回 JSON，必须包含 `payload.verdict`（`REPRODUCED` / `PARTIAL` / `FAILED` / `BLOCKED`）——
**内部自评**，仅供 workflow 内部 Package 门控与路由参考，不对外发布（对外 verdict 由
外部独立 evaluator 给出）。路由决策经 payload.route_to 返回，完整自评写入
`06_validate/report.md` 和 `metrics.json`，不要塞进返回值。
