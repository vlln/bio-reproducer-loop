# ClaroAI 校准 run 失败分类学（bench-200 ~ bench-234）

> 分析对象：`/storeData/gs/claroai-calibration/runs/bench-2NN/`（35 个正规 run，`*-legacy-*` 目录已全部排除）
> 分析日期：本次分析为纯只读，未修改远端任何文件、未重跑任何 run、未 git commit。
> 数据来源：每个 run 的 `container.log` + `repro-data/` 各阶段产物。

---

## 1. 主表

列说明见文末「方法说明」。`关键证据` 均为 `container.log` 中实际存在的行（截断至 ≤120 字符）。

| entry | 终止阶段 | 走完7阶段 | 死因大类 | 死因细类 | 关键证据（container.log 原文，截断） | 降级配置 | 耗时(约) | 产物体积 |
|---|---|---|---|---|---|---|---|---|
| bench-200 | 完成(Package) | 是 | system_capability | DEG 结果严重偏离 | `**T1 未复现**：Normal DEGs 严重偏离（23 vs 1,390，偏差 98.3%），最可能原因包括 GEO 数据版本差异或论文未报告的预处理步骤` | 是 | 1.6h | 20M |
| bench-201 | 完成(Package) | 是 | 完成 | REPRODUCED 96.1 | `"verdict": "REPRODUCED"`；偏差仅镜像版本（`r-base:4.3.2 无法从 Docker Hub 拉取，所有镜像源均超时`） | 是 | 8.1h | 14G |
| bench-202 | Validate（阻塞源: Data） | 否 | external_blocked | 受控数据 + 代码仓库 404 | `**TrUE-Net 代码**：GitHub 仓库 v-sundaresan/TrUE-Net 返回 404，不可用。`（独立证据：真实 HTTP 404；ADNI/AIBL/OASIS3 受控为公开事实） | 否 | 4.0h | 4.6M |
| bench-203 | Validate（阻塞源: Provision） | 否 | external_blocked? | MATLAB 商业软件 + 镜像源全挂 | `**MATLAB 不可用** — 论文核心分析依赖 CSA-ODF Toolbox … MATLAB 是专有商业软件，当前环境无有效许可证`（歧义：同 log 有 `Docker Hub 和 quay.io 均不可达`，FSL 失败实为 infra） | 是 | 2.9h | 52M |
| bench-204 | Validate（阻塞源: Data） | 否 | infra | Figshare 全端点 403（环境出口） | `所有 Figshare 端点（web、API、下载）均返回 403。该数据集是论文声明的唯一公开数据源，目前无法从此环境访问`（歧义：403 为真实响应但仅在本环境复现，疑为出口 IP 被封） | 是 | 0.5h | 2.1M |
| bench-205 | Validate（阻塞源: Provision） | 否 | external_blocked | Stata 专有 + IRB 个体数据 | `该论文唯一的软件依赖为 Stata 18.0（专有商业统计软件），已穷尽所有查找路径…均无法获取`（部分独立证据：Stata 专有为可验证事实；IRB 限制仅 agent 自述） | 否 | 1.2h | 6.1M |
| bench-206 | Validate（阻塞源: Provision） | 否 | external_blocked | SAS/SUDAAN 商业软件 + 代码不公开 | `Phase 3 (Provision): BLOCKED — SAS 9.4, SUDAAN 11.0.4 are commercial software with no public Docker images`（独立证据：商业软件为可验证事实） | 是 | 1.0h | 20M |
| bench-207 | 完成(Package) | 是 | infra | 磁盘不足 + 工具部署失败 | `**全量 5,909 样本**: 估计 ~3.6 TB，磁盘仅 151 GB 可用，无法下载` | 是 | 4.3h | 1.5G |
| bench-208 | 完成(Package) | 是 | external_blocked | 论文自身数值不一致 | `VDAC1 和 VDAC3 的偏差来源于论文自身补充材料（mmc2.xlsx）数据与论文正文声称值之间的不一致，而非复现流程错误`（独立证据：agent 已下载 mmc2.xlsx 并重算） | 否 | 1.4h | 27M |
| bench-209 | 完成(Package) | 是 | 完成 | REPRODUCED 95.0 | `**T1** (H3K4me1 Mann-Whitney U): W = 9,346,573，与论文 9.35 × 10⁶ 偏差仅 0.037%` | 是 | 14.9h | 269M |
| bench-210 | 完成(Package) | 是 | system_capability | 大文件下载未完成 | `T1/T2：核数量验证因 h5ad 文件下载未完成（RNA 2.3%，ATAC 1.2%）无法执行` | 是 | 3.7h | 1.6G |
| bench-211 | 完成(Package) | 是 | 完成 | REPRODUCED 88.8（范围偏窄） | `**Verdict: REPRODUCED (88.8/100)**`；注：`原始测序数据（All of Us 受控访问…）不可用，验证仅限于已发表补充数据与论文表格的交叉比对` | 是 | 2.1h | 20M |
| bench-212 | 完成(Package) | 是 | 完成 | REPRODUCED 93.6（无 GPU，未跑训练） | `Phase 6 验证完成。**Verdict: REPRODUCED (93.6/100)**`；注：`本环境无 GPU，无法运行实际训练/推理` | 是 | 6.5h | 371M |
| bench-213 | Reader | 否 | infra | 容器无外网 + 无 PDF | `**关键问题**：容器环境没有外网连接（所有 curl 请求超时），且本地没有论文 PDF。MinerU API 和 paperutils 工具也都不可用。` | 是 | 0.2h | 284K |
| bench-214 | 完成(Package) | 是 | 完成 | REPRODUCED 97.75（基于预计算结果） | `验证完成。**Verdict: REPRODUCED**（97.75/100）`；注：`HiRID 原始数据不可用: 所有验证基于 Zenodo 预计算结果，未从头训练` | 否 | 3.0h | 1.7G |
| bench-215 | 完成(Package) | 是 | external_blocked | All of Us 受控访问 | `**All of Us 数据**：受控访问，需机构批准和 DUAs，个体水平数据不可公开下载`（独立证据：AoU Researcher Workbench 需机构批准为公开事实） | 是 | 2.9h | 12M |
| bench-216 | 完成(Package) | 是 | 完成 | REPRODUCED 91.1 | `**T1 高度一致**：新生儿 sepsis ensemble CSMF 58.7%（95% CI: 49.0%–70.2%），论文 58%（47%–68%），偏差仅 0.7pp` | 是 | 3.5h | 511M |
| bench-217 | Reader | 否 | external_blocked | DOI 全库无法解析 | `**DOI 10.3390/diagnostics16060571 在所有主要学术数据库中均不存在，论文完全无法访问。**`（独立证据：Crossref API 404 "Resource not found"、dx.doi.org 404；MDPI 403 疑为 IP 封锁） | 是 | 0.2h | 476K |
| bench-218 | Validate（阻塞源: Data） | 否 | external_blocked | 付费墙+embargo+专有 EHR | `**HCA Healthcare** — 专有 EHR 数据库，需与 HCA Healthcare 签订数据使用协议`；`PMC 全文 embargo 至 2026-09-22`（独立证据：embargo 日期与 DUA 要求可核实） | 否 | 1.3h | 3.5M |
| bench-219 | 完成(Package) | 是 | system_capability | 外部数据未获取即判 N/A | `10 个复现目标中仅 T1 有可评分结果；T2–T9 因外部数据（GWAS/MPRA/RNA-seq 等）未获取而 N/A；T10 因评估脚本缺失 blocked` | 是 | 6.0h | 6.4G |
| bench-220 | 完成(Package) | 是 | 完成 | REPRODUCED 97.3 | `复现判定（REPRODUCED, 97.3/100）`；仅 `T7（PAF 值）：3 个 CVD PAF 与论文有轻微偏差（0.3-0.9pp）` | 是 | 1.1h | 39M |
| bench-221 | 完成(Package) | 是 | 完成 | REPRODUCED 100 | `**Verdict: REPRODUCED (100/100)**` | 是 | 1.8h | 689M |
| bench-222 | 完成(Package) | 是 | 完成 | REPRODUCED 93.75（范围自定义偏窄） | `**Verdict: REPRODUCED (94/100)**。在定义的复现范围内…原始论文图表（Figure 1–4）全部因数据缺失 blocked，无法进行视觉比较` | 是 | 2.9h | 144M |
| bench-223 | 完成(Package) | 是 | 完成 | REPRODUCED 96.0 | `**T2**（PCa scATAC）：blocked — Zenodo 1.46 GB 归档下载失败，特征分组缺失`（次要目标，整体 REPRODUCED） | 是 | 9.2h | 311M |
| bench-224 | 完成(Package) | 是 | system_capability | 数据集时间范围选错致 HR 偏离 | `**HR 量级系统性偏低**：6 个关键 HR95%→5% 值中，2 个精确匹配（偏差 < 5%），4 个显著偏离（偏差 15-49%）` | 是 | 2.8h | 3.6G |
| bench-225 | 完成(Package) | 是 | system_capability | 为省时禁用穷举搜索 | `穷举特征搜索（255 组合）被禁用以控制运行时间（完整搜索需 ~40 CPU 天）…复现使用了固定特征集，本质上是不同实验` | 是 | 7.1h | 2.3G |
| bench-226 | 完成(Package) | 是 | system_capability | 数据集/包版本差异致次要偏差 | `根因明确为 Kaggle 数据集版本差异和 R/MICE 版本差异，不改变论文核心科学结论` | 是 | 15.6h | 2.5G |
| bench-227 | 完成(Package) | 是 | 完成 | REPRODUCED 89 | `验证完成。**Verdict: REPRODUCED**（得分 89/100）` | 是 | 9.3h | 271M |
| bench-228 | 完成(Package) | 是 | system_capability | GTEx 下载未完成 | `**5 个检查 blocked**：GTEx 数据下载不完整（FrontalCortex-BySex 147/253 MB，ByAge 未下载），导致 T6–T9 的 GTEx 相关目标无法验证` | 否 | 5.3h | 1.4G |
| bench-229 | 完成(Package) | 是 | 完成 | REPRODUCED 87 | `**Multiome**（T1）：GLMM OR 值精确匹配（PT_VCAM1: 1.46）`；注：`Docker Hub 不可达`已绕过 | 是 | 6.0h | 240M |
| bench-230 | 完成(Package) | 是 | infra | HuggingFace 网络不可达 | `主要阻塞根因：Hugging Face 不可达（Phase 4），导致 Genecorpus-30M、V1-30M 权重和下游标注数据全部无法获取` | 是 | 5.6h | 1019M |
| bench-231 | 完成(Package) | 是 | external_blocked? | HF gated 模型需审批（兼网络不可达） | `UNI 模型 (MahmoodLab/uni) 在 HuggingFace 上为 gated repository，需账号登录 + access token。即使通过 hf-mirror.com 镜像，下载也返回 403`（歧义：gated 为真实外部限制，但同 log 称 `huggingface.co 网络不可达`，无法区分） | 否 | 1.7h | 565M |
| bench-232 | Validate（阻塞源: Data） | 否 | infra | 无 GPU + 数据源不可达 | `**BLOCKED 原因**：Phase 5 未产生任何运行结果…核心阻断：GPU 缺失、6/7 医学数据集不可访问、iNat2021/SimCLR-v1/v2 模型链接失效`（存疑：称 `NIH ChestX-ray14: NIH Box 需申请访问权限`，该数据集实为公开可直接下载，疑为误判） | 是 | 3.8h | 815M |
| bench-233 | 完成(Package) | 是 | external_blocked | 纯湿实验论文，无计算代码 | `定量结果复现因论文为纯湿实验研究而完全阻塞——无作者代码、source data 为原始未量化图像、所有分析工具为商业软件`（独立证据：论文类型可核实；但 `Fiji…17 个镜像源探测失败` 属 infra） | 是 | 1.1h | 577M |
| bench-234 | 完成(Package) | 是 | system_capability | GEO 可下载但未下完 | `**12 个已发表纤维化疾病数据集**（~10 GB）：NCBI 网络不稳定（5-25 MB/min，频繁 SSL 断开），下载命令已记录…建议从网络更好的环境下载`（同一 run 已成功从 GEO 下载 992 MB，说明 GEO 可达） | 是 | 16.4h | 3.8G |

---

## 2. 汇总统计

### 2.1 四类死因分布

| 死因大类 | run 数 | 占比 | entry |
|---|---|---|---|
| `完成` | 12 | 34.3% | 201, 209, 211, 212, 214, 216, 220, 221, 222, 223, 227, 229 |
| `external_blocked`（含 2 个带 `?`） | 10 | 28.6% | 202, 203?, 205, 206, 208, 215, 217, 218, 231?, 233 |
| `system_capability` | 8 | 22.9% | 200, 210, 219, 224, 225, 226, 228, 234 |
| `infra` | 5 | 14.3% | 204, 207, 213, 230, 232 |
| **合计** | **35** | **100%** | |

按引擎 verdict 交叉核对：REPRODUCED 12、PARTIAL 14、BLOCKED 9（35 总数一致）。

### 2.2 终止阶段分布（最常见的三个）

| 终止阶段 | run 数 | 说明 |
|---|---|---|
| 1. **完成 / Package** | 26 | 12 REPRODUCED + 14 PARTIAL，均产出 `README.md` + `run.sh` |
| 2. **Validate（Package 被引擎跳过）** | 7 | 202, 203, 204, 205, 206, 218, 232 — log 中均有 `[loopflow] 跳过 Package：verdict=BLOCKED` |
| 3. **Reader（01_plan）** | 2 | 213, 217 — 论文本身取不到，全流程只写阻塞记录 |

9 个 BLOCKED run 的**阻塞根因阶段**分布：Data 4（202, 204, 218, 232）、Provision 3（203, 205, 206）、Reader 2（213, 217）。
注意：BLOCKED run 的 `01_plan`~`06_validate` 目录均存在，但 04/05 阶段内容多为阻塞记录；其中 202/205/218 用补充材料数据生成了替代图表（05_run 分别有 41/98/52 个文件），属降级产出而非论文结果复现。

### 2.3 `system_capability` 的重复失败模式（决定下一步改什么）

8 个 run 归为 4 类重复模式：

| 模式 | 出现次数 | entry | 具体表现 |
|---|---|---|---|
| **A. 数据"可下载但没下完"就宣告 blocked/N/A** | 4 | 210, 219, 228, 234 | 210 h5ad 只下了 RNA 2.3%/ATAC 1.2%；228 GTEx 147/253 MB 且 ByAge 未下；234 同一 run 已从 GEO 成功拉 992 MB，却把另外 12 个 GEO 数据集记为"建议从网络更好的环境下载"；219 直接把 T2–T9 记为"外部数据未获取而 N/A"。**这是最高频的系统性缺陷**——缺少断点续传/重试/超时预算管理，且缺少"未获取 ≠ 不可获取"的判定纪律。 |
| **B. 为控制耗时私自削减分析规模，导致核心数值不可比** | 1（后果最严重） | 225 | 穷举特征搜索 255 组合被禁用、插补分区缩减、训练循环手工取消注释；AUROC 0.830 vs 论文 0.751、0.829 vs 0.642，论文核心发现（多输入优于 BMI-only）直接被证伪。agent 自己承认"本质上是不同实验"。 |
| **C. 选错数据版本/时间范围导致定量偏离** | 2 | 224, 226 | 224 六个关键 HR 中 4 个偏差 15–49%，根因"数据集时间范围差异"；226 化学物计数 151 vs 147，根因 Kaggle 数据集版本差异 + R/MICE 版本差异。缺少数据版本锁定与论文样本口径对齐。 |
| **D. 分析跑通但结果严重不符，未触发回溯** | 1 | 200 | Normal DEGs 23 vs 1,390（偏差 98.3%），agent 直接归因"GEO 数据版本差异或论文未报告的预处理步骤"并结案，未回退重查预处理。 |

### 2.4 `external_blocked` 的真值可信度

10 个 `external_blocked` 中：

| 证据强度 | run 数 | entry | 说明 |
|---|---|---|---|
| **有独立证据** | 6 | 202, 206, 208, 215, 217, 218 | 202 真实 GitHub 404 + ADNI/AIBL/OASIS3 受控为公开事实；206 SAS/SUDAAN 专有可验证；208 agent 已下载 mmc2.xlsx 并重算，证明是论文正文与补充材料自相矛盾；215 AoU Researcher Workbench 需机构批准为公开事实；217 Crossref API 与 dx.doi.org 双双 404（真实 HTTP 响应）；218 PMC embargo 日期 2026-09-22 可核实。 |
| **部分独立 / 主要靠自述** | 2 | 205, 233 | 205 "Stata 专有"可验证，但"个体患者数据受 IRB 限制"仅 agent 自述，论文未见数据可用性声明的独立佐证；233 "纯湿实验、无计算代码"可从论文类型核实，但"所有分析工具为商业软件"未逐一验证，且 Fiji 部署失败其实是网络问题。 |
| **存疑（标 `?`）** | 2 | 203, 231 | 203 声称 MATLAB 是决定性阻塞，但同一 log 显示 Docker Hub/quay.io 全不可达、FSL conda channel 404——自由软件 FSL 本应可装，无法排除 infra 才是真因；231 UNI 为 HF gated repo（真实外部限制）与 huggingface.co 网络不可达（infra）同时成立，log 无法区分谁是决定性因素。 |

**真值存疑合计 4 个**（205, 233 部分存疑 + 203, 231 明确存疑）。另有 1 个非 external_blocked 类但含误判的案例：**bench-232** 称 "NIH ChestX-ray14 需申请访问权限"，该数据集实际为公开可直接下载，属可获取性误判。

### 2.5 降级配置（技能不可用）清单

**降级配置 = 是：28 个（80.0%）**
200, 201, 203, 204, 206, 207, 209, 210, 211, 212, 213, 215, 216, 217, 219, 220, 221, 222, 223, 224, 225, 226, 227, 229, 230, 232, 233, 234

**降级配置 = 否：7 个（20.0%）**
202, 205, 208, 214, 218, 228, 231

这 7 个 log 中虽也提到 mineru-api 未执行，但均明确归因于"PDF 被付费墙 / Cloudflare / embargo 挡住，没有输入文件"，而非技能本身缺失，故按证据严格判定为 否。

主要缺失技能（按出现频次）：
- `mineru-api`（`MINERU_API_URL` 未配置/未设置/为空）—— 25 个 run，全部回退到 pymupdf / pdfplumber / PyPDF2 / PMC XML，代价是**表格与公式无法结构化提取、原始图表无法做 panel 级视觉对比**（209、214、221 等多个 run 明确因此扣分）。
- `paperutils` CLI 未安装且 pip 不可用 —— 12 个 run（203, 206, 209, 211, 213, 217, 219, 224, 225, 227, 229, 234），回退到直接调 Crossref / Europe PMC API。
- biocontainers / quay 技能路径 DNS 解析失败 —— 6 个 run（200, 203, 210, 214, 218, 227），导致预构建镜像查找退化为手工探测镜像代理（`mip probe`）。

### 2.6 其他横向观察（非任务要求，但对决策有用）

- **Docker-in-Docker 挂载缺陷是普遍现象**：18 个 run（200, 205, 207, 209, 211, 214, 215, 216, 218, 219, 220, 221, 225, 226, 229, 230, 231, 234）明确记录 DinD 导致 Nextflow Docker executor 无法挂载 work 目录，一律手工降级为 `docker run` + `docker cp`。这不影响单次结果的正确性，但意味着**产物里的 `main.nf` 在超过半数 run 中从未真正被 Nextflow 执行过**，Package 阶段交付的 `run.sh` 复现路径的真实性存疑。典型原文（bench-220）：`Nextflow Docker executor 因 DinD 环境不可用（无 ps 命令），使用 docker run + docker cp 替代`。
- **无 GPU 被 6 个 run 明确列为阻塞或降级因素**：212（`本环境无 GPU，无法运行实际训练/推理`）、219（`GPU 不可用：TREDNet 模型推理使用 CPU 模式`）、230（`无 GPU 硬件，无法执行预训练或全量微调`）、231（`GPU 缺失（nvidia-smi 不可用）— 这是主要风险`）、232（`核心阻断：GPU 缺失`）、234（`GPU: 不可用 ❌ — scvi-tools 将退化为 CPU 训练`）。
- **付费墙 / Cloudflare / PoW / reCAPTCHA 阻断论文与补充材料获取极为普遍**：20 个 run（200, 201, 202, 203, 204, 205, 208, 209, 214, 215, 216, 218, 220, 223, 226, 227, 228, 230, 231, 234）。但绝大多数靠 PMC JATS XML / BioC JSON 成功绕过正文获取，**只有补充材料（Supplementary Tables/Figures）是真正拿不到的**——这才是反复扣分的项（216 的 Tables S1–S2、219 的 Tables S1–S6、226 的 Supplementary Tables 1-10、231 的 Supplementary Tables 1-73 均获取失败）。

---

## 3. 方法说明

### 3.1 判定规则

| 列 | 判定方法 |
|---|---|
| **终止阶段** | 以 `container.log` 末尾为准。26 个 run 末尾为 `[loopflow] Done: <run-id>` 且 Package 产物齐全 → 记「完成(Package)」。9 个 run 末尾为 `[loopflow] 跳过 Package：verdict=BLOCKED` → 记「Validate」，并在括号内标注**阻塞根因阶段**（log 中首个宣告 BLOCKED 且被下游继承的 Phase）。213/217 因 Phase 1 即阻塞、后续阶段产物全为阻塞记录（plan.md 仅 3.2 KB / 7.9 KB），记为「Reader」。 |
| **是否走完 7 阶段** | 同时满足 `repro-data/06_validate/report.md` 存在 **且** `repro-data/README.md` + `repro-data/run.sh` 存在。实测结果与 verdict 完全对应：9 个 BLOCKED run 全部缺 Package 产物，其余 26 个全部齐全。 |
| **死因大类** | 按任务定义严格区分。判定优先级：以 log 中 agent 自己写明的「阻塞根因 / BLOCKED 原因 / 根因」段落为起点，再用独立事实（HTTP 状态码、同 run 内的反例、公开可核实的软件/数据属性）校正。凡结论完全依赖 agent 自述且存在合理反证的，加 `?` 标注。 |
| **死因细类** | ≤20 字自由文本，取 log 原文语义，不做推断性扩写。 |
| **关键证据** | 用 `grep -n` 从 `container.log` 定向取真实行，截断至 ≤120 字符。所有引号内内容均为 log 中实际存在的文本。`external_blocked` 行额外在括号内标注证据强度（"独立证据" / "仅 agent 自述" / "歧义"）。 |
| **降级配置** | `grep -E "(mineru-api\|paperutils\|MinerU\|MINERU_API_URL\|技能)...(不可用\|未安装\|未配置\|未设置\|为空)"`。仅当 log 表明**技能/工具本身缺失**时记「是」；若明确归因于外部原因（PDF 被付费墙挡住导致 mineru 无输入）则记「否」。 |
| **耗时** | **估算值**。取 `stat -c%Y <run>/input`（run 起始时创建）到 `stat -c%Y <run>/container.log`（最后一次写入）的差值。注意：不能用 `find <run> -type f` 全量 mtime 极值——下载的数据文件会继承上游服务器时间戳，导致 bench-214 算出 18029h、bench-228 算出 13141h 的荒谬值。本表已改用上述方法。 |
| **产物体积** | `du -sh <run目录>`，含 `input/`、`workspace/`、`repro-data/` 全部内容。 |

### 3.2 反自述纪律（按任务要求执行）

本分析**不采信 agent 的可获取性自述**。具体做法：

1. **同 run 内反例优先**：若同一个 run 中某数据源被成功访问过，则该源的其他"不可获取"声明降级为 `system_capability`。典型：bench-234 从 GEO 成功下载 992 MB 后又称另外 12 个 GEO 数据集"网络不稳定"→ 判 `system_capability` 而非 `external_blocked`。
2. **要求真实 HTTP 证据**：只有 log 中出现真实状态码（404 / 403 / 500）或真实注册页内容，才认定为独立证据。bench-217 的 Crossref 404 + dx.doi.org 404、bench-202 的 GitHub 404、bench-231 的 hf-mirror 403 属此类。
3. **可核实的软件/数据属性**：MATLAB / SAS / SUDAAN / Stata 为专有商业软件、All of Us Researcher Workbench 需机构批准、PMC embargo 有明确日期 —— 这些是可独立核实的外部事实，接受为独立证据。
4. **已知误报模式复查**：历史上 bench-200 曾谎报 GEO 不可下载、bench-229 曾谎报 GSE220289 无处理矩阵。本次逐条复查了所有"数据不可得"声明，发现 1 例新的可获取性误判（bench-232 的 NIH ChestX-ray14）。

### 3.3 已知局限

- 部分 run 的 `repro-data/` 子目录属主为容器 uid 1000，但本次分析所需的 `container.log`、各阶段 `.md` 产物、`metrics.json` 均可读，**未遇到 Permission denied**，无"无法读取"的字段。
- 耗时为墙钟估算，包含 agent 思考、下载、构建全部时间，不区分有效计算时间。
- `external_blocked` vs `infra` 的边界在"外部站点从本环境返回 403/超时"这一情形下本质模糊（bench-204、231 最典型）。本表按"该阻断是否只在本环境复现"来切分：只在本环境复现的归 `infra`，普遍存在的归 `external_blocked`；无法判断的加 `?`。

---

## 4. 结论要点

1. **系统本身的能力缺陷（`system_capability`，8/35 = 22.9%）集中在数据获取的"最后一公里"**：4 个 run 属于"数据其实拿得到，但没拿完就宣告 blocked"。这不是外部世界的问题，是缺少断点续传、重试预算和"未获取 ≠ 不可获取"的判定纪律。
2. **`infra` 类（5/35）对 `system_capability` 类的判定造成污染**：DinD 挂载缺陷（18 个 run 受影响）、镜像源不可达、无 GPU（6 个 run）、容器无外网（bench-213 直接 0.2h 全线阵亡）—— 这些噪声会把系统真实能力评分压低，也会给 agent 提供"甩锅给网络"的现成借口，进而制造更多伪 `external_blocked`。
3. **`external_blocked` 中有 4 个真值存疑**（203, 231 明确存疑；205, 233 部分存疑），加上 bench-232 的 ChestX-ray14 误判，说明当前系统的"不可获取"判定还不能直接采信，benchmark 打分需要独立可获取性预言机（oracle）。
4. **26/35 走完 7 阶段、12/35 判 REPRODUCED**，但其中 211、212、214、222 的 REPRODUCED 是在**自行收窄的复现范围**内取得的（原始数据受控 → 只比对补充表；无 GPU → 不跑训练；图表全 blocked 仍判 94 分）。这提示评分口径需要引入"范围覆盖率"惩罚项，否则 REPRODUCED 率会被系统性高估。

---

## 独立核对（2026-08-22，主 agent 复验）

按校准方法论的独立验证原则，对本文档中后果最大的三条结论做了远端复核：

| 结论 | 复核方法 | 结果 |
|------|---------|------|
| 9 个 BLOCKED run 跳过 Package | `grep -l "跳过 Package" bench-2NN/container.log \| wc -l` | ✓ 精确为 9 |
| bench-234 已成功下载 992 MB 后放弃另 12 个数据集 | grep 原文 | ✓ 原文「主 CLAD 数据集（总共 992 MB）已就绪」+ GSE289881_RAW.tar 629 MB / processed 249 MB / GSE224210 114 MB 明细俱在 |
| 18 个 run 的 Nextflow 降级为手工 `docker run` | 逐 run grep DinD/降级关键词 | ✓ 实为 **19 个 run** 命中（原表 18 为下界，结论不变） |

**对「模式 A」根因的修正（重要）**：bench-234 放弃的是 ~10 GB 数据，log 记录的实测速率为
`5-25 MB/min` 且「频繁 SSL 断开」——即 7~33 小时的下载耗时。这说明模式 A **不是纯粹的系统
能力缺陷，而是与远端出口网络质量强耦合**（参见 BL-008：远端对 Docker Hub / NCBI 直连长期
受限）。因此修复方案应是双侧的：

- 系统侧：断点续传 + 重试预算 + 显式超时声明；产物中区分「未获取」与「不可获取」（当前一律
  写成后者，这才是真正的系统缺陷——判定纪律，而非下载能力）
- 基建侧：改善正式批次的出口网络，或在 ExecutionEnvelope 中显式声明网络条件，使跨批次结果可比

在网络条件未声明的前提下，把模式 A 全部归因为被测系统能力是不成立的；但「未获取即宣告
不可获取」的判定错误与网络无关，系纯系统缺陷（bench-232 把公开可下载的 NIH ChestX-ray14
称为需申请访问，是同一类判定错误的独立佐证）。
