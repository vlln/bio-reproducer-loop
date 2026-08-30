# ClaroAI-Bench 运行结果汇报（试点口径，2026-08-28）

> 状态：**试点/校准阶段结果**，非正式发布结论。35 个归档 run 均为旧协议（pilot，无
> answers.csv/digests/sha256sums），verdict 由 P2 批次期间（2026-08-22）claims oracle
> 权威重评得出；此后 S2（BL-015）新增 101 条数值 claims 并冻结 oracle v2.0.0——
> **该批次 verdict 对应的是 S2 之前的 oracle 口径**，且旧 run 因证据面缺失不可用新
> 口径重评（evaluate_run.py 明确拒绝）。正式结论需 S5 冻结量具下新协议批次。
> 数据来源：`benchmarks/calibration-assets.md`（P2 权威表）、`~/Project/claroai-bench/results/`
> （原论文 scores_summary.csv / neurips_analyses.json）。

## 1. 最直观的 score：原论文系统 vs 我们的系统

| 指标 | 原论文系统（Claude Code 全能力 agent） | 我们的系统（bio-reproducer，35 run pilot） |
|------|--------------------------------------|-------------------------------------------|
| **完全复现率** | **42.4%**（14/33，作者 D5=2） | **45.7%**（16/35 REPRODUCED） |
| **≥部分复现率** | **60.6%**（20/33，作者 D5>0） | **82.9%**（29/35 ≥PARTIAL） |
| 基线：audit-only | 0%（0/33） | — |
| 基线：bash-only | 0%（0/33） | — |

> 原论文两种口径：手稿正文 20/33=60.6%（95% CI [42.4, 75.8]）；HF card /
> neurips_analyses.json ablation 记录 18/33=54.5%。此处采用与作者逐篇 D5 一致的手稿口径
> （D5>0 即 20/33）。95% CI（正态近似）：我们 16/35=[29.2, 62.2]，作者 20/33=[43.9, 77.3]，
> 两者 CI 重叠——**差异不显著，量级相当**。

### 计算口径（31 篇计算类、作者 D5 可对照的公共子集）

| 指标 | 原论文系统 | 我们的系统 |
|------|-----------|-----------|
| 完全复现（D5=2 / REPRODUCED） | 13/31 = **41.9%** | 15/31 = **48.4%** |
| ≥部分复现（D5>0 / ≥PARTIAL） | 18/31 = **58.1%** | 26/31 = **83.9%** |
| 完全一致（作者 D5=2∧我们 REPRODUCED，或作者 D5=0∧我们 FAILED） | — | 9/31 |

### 逐篇对照（31 篇计算类）

| entry | 作者 D5 | 我们 verdict | 我们 score |
|-------|---------|--------------|-----------|
| 207 | 2 | REPRODUCED | 100.0 |
| 210 | 2 | REPRODUCED | 65.0 |
| 214 | 2 | REPRODUCED | 85.0 |
| 216 | 2 | REPRODUCED | 100.0 |
| 220 | 2 | REPRODUCED | 100.0 |
| 221 | 2 | REPRODUCED | 76.25 |
| 223 | 2 | REPRODUCED | 85.0 |
| 201 | 2 | PARTIAL | 46.67 |
| 203 | 2 | PARTIAL | 30.0 |
| 204 | 2 | PARTIAL | 50.0 |
| 206 | 2 | PARTIAL | 30.0 |
| 200 | 2 | **FAILED** | 0.0 |
| 231 | 2 | **FAILED** | 15.0 |
| 213 | 1 | REPRODUCED | 100.0 |
| 218 | 1 | REPRODUCED | 100.0 |
| 224 | 1 | REPRODUCED | 100.0 |
| 205 | 1 | PARTIAL | 50.0 |
| 229 | 1 | **FAILED** | 15.0 |
| 211 | 0 | **REPRODUCED** | 100.0 |
| 212 | 0 | **REPRODUCED** | 100.0 |
| 215 | 0 | **REPRODUCED** | 100.0 |
| 217 | 0 | **REPRODUCED** | 100.0 |
| 230 | 0 | **REPRODUCED** | 100.0 |
| 202 | 0 | PARTIAL | 50.0 |
| 219 | 0 | PARTIAL | 50.0 |
| 227 | 0 | PARTIAL | 50.0 |
| 228 | 0 | PARTIAL | 50.0 |
| 233 | 0 | PARTIAL | 50.0 |
| 234 | 0 | PARTIAL | 50.0 |
| 225 | 0 | FAILED | 15.0 |
| 226 | 0 | FAILED | 0.0 |

（bench-208/209 非计算类、bench-222/232 无 PMID 对照，未入表。）

## 2. 主要发现

1. **量级相当，且部分指标反超**：完全复现率我们 45.7% vs 作者 42.4%；≥部分复现率
   82.9% vs 60.6%。差异统计上不显著（CI 重叠），但与作者系统处于同一水平线。
2. **我们复现了作者失败的 5 篇**（作者 D5=0、我们 REPRODUCED 100）：bench-211/212/
   215/217/230。作者系统在公共可下载数据上的失败（如 NCHS 链接、GEO 标签互换等）未被
   本系统复现。
3. **我们失败了作者成功的 2 篇**（作者 D5=2、我们 FAILED）：bench-200（GEO 标签互换未
   检测——作者 agent 曾修正）、bench-231（KNN/线性探针无复现值）。
4. 双向发现与校准结论一致（bench-200 作者 D2 低估；bench-231 作者 D5=2 高估）——
   作者评分既非上界也非下界，双向都有偏差。

## 3. 局限性（必须声明）

- **试点口径**：35 run 为旧协议 pilot（无 answers.csv / digests / sha256sums），verdict
  由 06_validate report + data_manifest + provision 证据面得出，且对应 **S2 之前的 oracle**
  （17 篇当时无 claims，9 篇 REPRODUCED 完全基于 D1-D3 证据）。
- **不可重评**：S2 后冻结 oracle v2.0.0 新增 101 条 claims，旧 run 因证据面缺失无法用新
  口径重评——**本表数字不是冻结量具下的正式结果**。
- **口径不对称**：作者 D5 为作者自评（0/1/2），我们为 claims 容差评分（0-100）；两套
  评分细则不可逐分对应，只可对比"复现/未复现"二值语义。
- **样本小**：n=33/35，95% CI 很宽，比率差异不具统计显著性。

## 4. 下一步

- **S5 正式批次**：冻结 oracle v2.0.0 + run-entry.sh 新协议（answers.csv 证据面）重跑
  35 entry（或先跑计算类子集），得到可发布的正式 score。
- 或先做 S4/S3（裸 agent baseline / 系统修复配对消融）再正式批次。
