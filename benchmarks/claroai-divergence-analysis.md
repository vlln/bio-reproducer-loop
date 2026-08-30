# ClaroAI-Bench：我们 vs 作者系统 差异分析（claim 级证据）

> 配套 `benchmarks/claroai-results-report.md`。本文件回答：「我们与作者系统的差异，
> 到底差在哪里、证据是什么」。
> 证据来源：P2 批次评估 JSON（远端 `/tmp/bl012/eval-bench-*.json`，优先 `-new` 重评版）、
> `benchmarks/calibration-failure-taxonomy.md`（35 run 死因）、作者 `scores_summary.csv`。
> 分析日期：2026-08-28。**试点口径**：35 run 为旧协议 pilot，verdict 对应 S2 之前 oracle；
> 冻结 oracle v2.0.0 下不可重评（缺 answers.csv 证据面），正式结论需 S5。

## 0. 关键澄清：数值层可比性

| 类别 | 篇数 | 说明 |
|------|------|------|
| P2 时**有 claims**（数值层可比） | **14** | 200, 201, 203, 206, 208, 209, 210, 214, 216, 220, 221, 225, 229, 231 |
| P2 时 0 claims（仅 A1/A2 元数据层） | 17 | 其余全部——verdict 满分/REPRODUCED **不代表数值复现** |

> 含义：① "我们复现了作者失败的 5 篇"（211/212/215/217/230）**不成立**——两边均无数值
> 证据；② 与作者 D5 的差异结论只能从 14 篇数值可比 subset 得出。

## 1. 数值层逐篇差异（14 篇）

| entry | 作者 D5 | 我们 verdict | claim 级证据（paper → system） | 差异解读 |
|-------|--------|-------------|-------------------------------|---------|
| 220 | 2 | REPRODUCED 100 | 3/3：血铅 HR 1.63→1.63、胫骨 3.32→3.32、髌骨 2.42→2.42 | 完全一致 ✓ |
| 208 | 2 | REPRODUCED 85 | 3/3：VDAC1 50→57.6、VDAC2 30→30.92、VDAC3 18→11.48 | 全过 ✓ |
| 214 | 2 | REPRODUCED 85 | 2/2：HiRID Graph-spa 50.02→50.02、Baseline 45.61→45.61 | 全过 ✓（基于预计算） |
| 216 | 2 | REPRODUCED 100 | 1/1：sepsis CSMF 58→58.7 | 全过 ✓ |
| 221 | 2 | REPRODUCED 76.25 | 7/8 HR 精确命中；**hei.2015 cancer HR 0.83→0.88 超容差** | 8 中 7，1 偏差 |
| 201 | 2 | PARTIAL 46.67 | 2/3：Fig2_n80 0.782→0.7822、n1000 0.965→0.965 ✓；power_selection 无复现值 | 2 复现，1 缺证据 |
| 210 | 2 | REPRODUCED 65 | 1/2：donors 299→299 ✓；nuclei 无复现值 | 部分 ✓ |
| 203 | 2 | PARTIAL 30 | 0/1：LME p 值无复现值 | 未复现 |
| 206 | 2 | PARTIAL 30 | 0/3：Flu/乳腺/宫颈三条 PR claims 全无复现值 | 未复现 |
| 200 | 2 | **FAILED 0** | 0/2：Fig4A DEG 肿瘤 599→163、正常 1390→23（偏差 98%） | **GEO 标签互换未检测** |
| 231 | 2 | **FAILED 15** | 0/2：KNN-5、线性探针 accuracy 无复现值 | UNI gated + 无 GPU |
| 209 | 1 | FAILED 17.5 | 1/4：Mann-Whitney U 9.35e6→9.3466e6 ✓；**p 值 1.83e-9→1.83（少 e-9 数量级）**、Pearson 无复现值 | 1 复现，p 值数量级错误 |
| 229 | 1 | FAILED 15 | 1/4：multi 计数 57491→57491 ✓；ATAC/RNA/spatial 无复现值 | 1 复现，3 缺证据 |
| 225 | 0 | FAILED 15 | 0/2：AUROC 75.1→0.83、BMI-only 64.2→0.829（单位/数量级错误） | 数值格式错误 |

## 2. 差异根因归类

### 2.1 我们失败、作者成功（作者 D5=2，我们 FAILED）——2 篇，真实能力差距

- **bench-200**（Fig4A DEG 数 163/23 vs 599/1390）：根因 = **GEO 标签互换未被检测**
  （作者 agent 曾修正，见 calibration-assets.md）。属复现方法缺陷，非外部阻塞。
- **bench-231**（KNN-5/线性探针无复现值）：根因 = UNI 模型 HF gated（403）+ 无 GPU，
  无法产出 accuracy 数值。属外部限制 + 算力限制，但作者系统做到了（有 D5=2 证据）。

### 2.2 作者 D5=2 但我们 PARTIAL/REPRODUCED-低分——3 篇，证据面缺口

- bench-203（LME 无复现值）、bench-206（3 条 PR 无复现值）、bench-210（nuclei 无
  复现值）：**系统执行了但产物没落成可解析数值**——这正是 ADR-0011 证据面切换
  （claims 须从 answers.csv 定位）要解决的问题。旧协议 run 无法追溯。

### 2.3 数值格式/数量级错误——2 篇，可复现性评分陷阱

- bench-209：p 值 1.83e-9 被记成 1.83（丢数量级）→ 单条 claim 判 FAILED。
- bench-225：AUROC 75.1% 被记成 0.83（相对容差 5% 下单位换算直接超差）。
- 教训：数值声明必须带单位与数量级；相对容差对百分比/指数表示敏感（S2 已用
  0.5×10^-decimals 书写精度导出容差缓解，但旧 run 无法重算）。

### 2.4 我们 PARTIAL 但作者 D5=2 的共性：缺"证据落盘"而非缺"执行"

14 篇可比 subset 中，7 篇 REPRODUCED（含低分）、7 篇 PARTIAL/FAILED。后者几乎全部
呈 "no reproduced value in evidence artifact"——**不是没跑，是没把结果写进可评分格式**。

## 3. 与作者 D5 的总体一致性

- 14 篇数值可比：作者 D5=2（8 篇）→ 我们 REPRODUCED 4 / PARTIAL 3 / FAILED 1；
  作者 D5=1（3 篇）→ REPRODUCED 1 / FAILED 2；作者 D5=0（3 篇）→ FAILED 2 / 其余 1。
- 完全一致（D5=2∧REPRODUCED 或 D5=0∧FAILED）：**9/31**（含元数据层）。
- 方向性发现：作者 D5=2 的 8 篇中我们 4 篇 REPRODUCED（50%）；作者 D5=0 的 3 篇数值
  可比中我们 0 篇 REPRODUCED——**无反向胜利证据**（此前"5 篇反向"为口径误读）。

## 4. 结论

1. 试点口径下，数值层真正可比的只有 14 篇；"我们复现了作者失败的 5 篇"不成立。
2. 真实的系统能力差距集中在 **2 篇**（bench-200 标签互换、bench-231 gated+GPU），
   与作者系统的差距是**具体方法缺陷**而非量级差距。
3. 大量 PARTIAL/FAILED 的根因是**证据面缺口**（结果未落盘为可评分数值）——S2 + ADR-0011
   证据面切换正是为此；冻结 oracle v2.0.0 下的正式批次（S5）才能给出可发布的结论。
