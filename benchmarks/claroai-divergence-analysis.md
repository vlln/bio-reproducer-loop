# ClaroAI-Bench：我们 vs 作者系统 差异分析（claim 级证据，v2 修订版）

> 配套 `benchmarks/claroai-results-report.md`。本文件回答：「我们与作者系统的差异，
> 到底差在哪里、证据是什么」。
> 证据来源：P2 批次评估 JSON（远端 `/tmp/bl012/eval-bench-*.json` + `reval35.txt`，
> **优先 `-new`/`final` 重评版**）、`benchmarks/calibration-failure-taxonomy.md`
> （35 run 死因）、作者 `scores_summary.csv`（DOI 为键）。
> 分析日期：2026-08-28 初版；2026-08-30 经对抗性审查修订（v2）。
> **试点口径**：35 run 为旧协议 pilot，verdict 对应 S2 之前 oracle；冻结 oracle v2.0.0
> 下不可重评（缺 answers.csv 证据面），正式结论需 S5。

## 0. 关键澄清：数值层可比性

P2 权威时点（git 7257846）oracle 计数：**35 篇中 16 篇有 claims（46 条）**，19 篇无。

| 类别 | 篇数 | 说明 |
|------|------|------|
| P2 时**有 claims**（数值层可比） | **16** | 200, 201, 203, 206, 208, 209, 210, 214, 216, 220, 221, 222, 223, 225, 229, 231 |
| P2 时 0 claims（仅 A1/A2 元数据层） | 19 | 其余全部——verdict 满分/REPRODUCED **不代表数值复现** |

> 含义：① "我们复现了作者失败的 5 篇"（211/212/215/217/230）**不成立**——两边均无数值
> 证据（作者 D5=0 亦然）；② 与作者 D5 的差异结论只能从 16 篇数值可比 subset 得出。
> 注意 208/209 为 wet-lab 非计算类（作者 D5 n/a），但 P1-2 为其补了 claims 故在 16 篇内；
> 222（5 条）、223（AUROC 1 条）在 P2 时点即有 claims，属 claim 级评分。

## 1. 数值层逐篇差异（16 篇）

| entry | 作者 D5 | 我们 verdict | claim 级证据（paper → system） | 差异解读 |
|-------|--------|-------------|-------------------------------|---------|
| 220 | 2 | REPRODUCED 100 | 3/3：血铅 HR 1.63→1.63、胫骨 3.32→3.32、髌骨 2.42→2.42 | 完全一致 ✓ |
| 221 | 2 | REPRODUCED 76.25 | 7/8 HR 精确命中；**hei.2015 cancer HR 0.83→0.88 超容差** | 8 中 7，1 偏差 |
| 223 | 2 | REPRODUCED 85 | 1/1：AUROC best 0.95→0.9961（≥0.95 OK） | 通过 ✓ |
| 214 | 2 | REPRODUCED 85 | 2/2：HiRID Graph-spa 50.02→50.02、Baseline 45.61→45.61 | 全过 ✓（基于预计算） |
| 208 | n/a（wet-lab） | REPRODUCED 85 | 3/3：VDAC1 50→57.6、VDAC2 30→30.92、VDAC3 18→11.48 | 全过 ✓（作者 D5 不适用） |
| 216 | 2 | REPRODUCED 100 | 1/1：sepsis CSMF 58→58.7 | 全过 ✓ |
| 210 | 2 | REPRODUCED 65 | 1/2：donors 299→299 ✓；nuclei 无复现值 | 部分 ✓ |
| 201 | 2 | PARTIAL 46.67 | 2/3：Fig2_n80 0.782→0.7822、n1000 0.965→0.965 ✓；power_selection 无复现值 | 2 复现，1 缺证据 |
| 222 | 2 | PARTIAL 30 | 0/5：两个参数量 + 3 个 AUROC 均无复现值 | **数值全败，仅靠 A1/A2** |
| 203 | 2 | PARTIAL 30 | 0/1：LME p 值无复现值 | 未复现 |
| 206 | 2 | PARTIAL 30 | 0/3：Flu/乳腺/宫颈三条 PR claims 全无复现值 | 未复现 |
| 200 | 2 | **FAILED 0** | 0/2：Fig4A DEG 肿瘤 599→163（偏差 72.8%）、正常 1390→23（偏差 98.3%） | **GEO 标签互换未检测** |
| 231 | 2 | **FAILED 15** | 0/2：KNN-5、线性探针 accuracy 无复现值 | UNI gated + 无 GPU |
| 209 | n/a（wet-lab） | FAILED 17.5 | 1/4：Mann-Whitney U 9.35e6→9.3466e6 ✓；**p 值 1.83e-9→1.83（少 e-9 数量级）**、Pearson 无复现值 | 1 复现，p 值数量级错误 |
| 229 | 1 | FAILED 15 | **0/4**：multi/ATAC/RNA/spatial 均无复现值（P2 最终） | 全部缺证据 |
| 225 | 0 | FAILED 15 | 0/2：AUROC 75.1→0.83、BMI-only 64.2→0.829（VIOLATED） | **实验削减致不同实验** |

> 注：229 早期评估（eval-bench-229-new.json）曾记录 multi 计数 57491→57491 ✓
> （PARTIAL 32.5）；P2 最终重评（eval-b229-final.json / reval35.txt）为 **0/4**，
> 以最终版为准。222 的 P2 最终评估仅存在于 reval35.txt（0/5），`/tmp/bl012` 无对应
> JSON 文件——评估产物追溯缺口，建议补登 calibration-assets。
> 另注：reval35.txt 中 `bench-223|PARTIAL|50.0|0/0` 为 **AUROC claim 恢复前的过期快照**
> （权威 P2 表与 eval-bench-223-new.json 均为 REPRODUCED 85，AUROC 0.9961≥0.95）；
> 引用 reval35 时须以本注区分，勿误引 223 行。

## 2. 差异根因归类

### 2.1 我们失败、作者成功（作者 D5=2，我们数值全败）——3 篇，真实能力差距

- **bench-200**（Fig4A DEG 数 163/23 vs 599/1390）：根因 = **GEO 标签互换未被检测**
  （作者 agent 曾修正，见 calibration-assets.md）。属复现方法缺陷，非外部阻塞。
- **bench-231**（KNN-5/线性探针无复现值）：根因 = UNI 模型 HF gated（403）+ 无 GPU，
  无法产出 accuracy 数值。属外部限制 + 算力限制，但作者系统做到了（有 D5=2 证据）。
- **bench-222**（0/5 数值 claims 全无复现值）：TorchXRayVision 参数量/AUROC 均未产出
  可解析数值，verdict PARTIAL 30 全靠 A1/A2 元数据。属"执行了但结果未落盘"。

### 2.2 作者 D5=2 但我们 PARTIAL——3 篇，证据面缺口

- bench-201（2/3：Fig2 两条复现，power_selection 无复现值）、bench-203（LME 无复现
  值）、bench-206（3 条 PR 无复现值）：**系统执行了但产物没落成可解析数值**——这正
  是 ADR-0011 证据面切换（claims 须从 answers.csv 定位）要解决的问题。旧协议 run
  无法追溯。
- 注：bench-210 虽属 D5=2 且含 1 条 claim 缺口（nuclei 无复现值），但其 verdict 为
  REPRODUCED 65.0（donors 299 复现），归 §1 表而非本节。

### 2.3 有值但错 / 数值异常——2 篇

> 注：bench-200 同为"有值但错"（Fig4A VIOLATED），但其根因已在 §2.1 归类为 GEO 标签
> 互换，此处不重复计入；"有值但错"共 3 篇（200/209/225），见 §2.4。

- bench-209：p 值 1.83e-9 被记成 1.83（丢数量级）→ 单条 claim 判 FAILED（wet-lab，
  作者 D5 n/a，此失败不影响"我们 vs 作者计算类"比较）。
- bench-225：**根因是实验削减**（禁用 255 组合穷举搜索，"本质上是不同实验"，见
  taxonomy §2.3 模式 B），AUROC 0.83 vs 75.1、BMI-only 0.829 vs 64.2 的差异（>18pp）
  无法用单位换算解释——归因"单位/数量级错误"为误诊，已修正。

### 2.4 我们 PARTIAL/FAILED 的共性：缺"证据落盘"而非缺"执行"

16 篇可比 subset 分布：**7 篇 REPRODUCED**（208, 210, 214, 216, 220, 221, 223）、
**4 篇 PARTIAL**（201, 203, 206, 222）、**5 篇 FAILED**（200, 209, 225, 229, 231）。
非 REPRODUCED 的 9 篇中 6 篇呈 "no reproduced value in evidence artifact"（203/206/
222/229/231 全无值，201 缺 1 值）——**不是没跑，是没把结果写进可评分格式**；例外为
200（有值但错 VIOLATED）、209（p 值数量级错误）、225（实验削减致不同实验），即
"有值但错"占 3/9。

## 3. 与作者 D5 的总体一致性（16 篇 claims 集合）

按 scores_summary.csv（DOI 键）与 P2 表 verdict 交叉：

- 16 篇中作者 D5 分布：**D5=2 共 12 篇**（200,201,203,206,210,214,216,220,221,222,
  223,231）、**D5=1 共 1 篇**（229）、**D5=0 共 1 篇**（225）、n/a 2 篇（208,209）。
- D5=2 的 12 篇中我们：REPRODUCED **6**（210,214,216,220,221,223）、PARTIAL **4**
  （201,203,206,222）、FAILED **2**（200,231）。
- D5=1 的 229：FAILED；D5=0 的 225：FAILED；n/a 的 208/209：REPRODUCED/FAILED。
- **结论方向**：作者 D5=2 的 12 篇中我们 6 篇数值复现（50%）；作者 D5=0 仅 225 一篇
  （我们 FAILED，0 篇 REPRODUCED）——**无反向胜利证据**（此前"5 篇反向"为口径误读）。
- 完全一致（含元数据层，33 计算类口径）：9/33（作者 D5=2∧我们 REPRODUCED 7 篇 +
  作者 D5=0∧我们 FAILED 2 篇）。

## 4. 结论

1. 试点口径下，数值层真正可比的只有 16 篇；"我们复现了作者失败的 5 篇"不成立。
2. 真实的系统能力差距集中在 **3 篇**（bench-200 标签互换、bench-231 gated+GPU、
   bench-222 数值全败），与作者系统的差距是**具体方法/落盘缺陷**而非量级差距；
   另有 3 篇（201/203/206）为证据面缺口（结果未落盘为可评分数值；210 同含 1 条
   claim 缺口但整体 REPRODUCED 65）。
3. 大量 PARTIAL/FAILED 的根因是**证据面缺口**——S2 + ADR-0011 证据面切换正是为此；
   冻结 oracle v2.0.0 下的正式批次（S5）才能给出可发布的结论。
