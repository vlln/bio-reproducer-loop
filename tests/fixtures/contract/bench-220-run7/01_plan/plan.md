# Paper: Do We Underestimate Risk of Cardiovascular Mortality due to Lead Exposure?

DOI: 10.1016/j.scitotenv.2024.171511

## Paper Understanding

### Research Question

该论文旨在回答一个核心流行病学问题：基于血铅水平（blood lead levels, BLLs）评估的铅暴露心血管死亡风险是否被低估了？

背景：既往大量前瞻性研究使用单次血铅测量作为暴露指标，发现血铅与心血管死亡率之间存在显著关联。然而，血铅主要反映近期暴露（半衰期数周），而骨骼中储存了人体 90-95% 的铅负担，半衰期长达数十年。骨骼铅水平通过 K-X-ray fluorescence (KXRF) 技术测量，但该技术需要专用设备和较长测量时间，难以在大规模人群研究中应用。作者团队此前开发了基于 Super Learner 算法预测骨骼铅水平的模型，利用血铅、年龄及其他社会经济和行为变量来估算胫骨铅（tibia lead）和髌骨铅（patella lead）浓度。

本研究将预测骨骼铅水平应用于 NHANES-III 队列，比较血铅与预测骨骼铅对全因死亡、心血管疾病（CVD）死亡和心脏病死亡的风险估计，评估基于血铅的风险评估是否低估了铅暴露的真实心血管死亡风险。

### Study Design

- **研究设计**：前瞻性队列研究（prospective cohort study）
- **数据来源**：NHANES-III（1988-1994 年基线调查）链接至 National Death Index (NDI) 死亡数据
- **研究人群**：11,628 名 ≥20 岁成人，经排除后（缺失血铅/死亡数据 n=3,779；缺失骨骼铅预测变量 n=1,953；缺失核心协变量 n=2,223；0 月随访 n=2；其他种族 n=465），代表 1.36 亿美国 20 岁及以上人群
- **随访时间**：中位随访 26.8 年，截至 2019 年 12 月 31 日（比 Lanphear et al. 2018 多 8 年随访）
- **暴露变量**：血铅（实测）、预测胫骨铅、预测髌骨铅（均由 Super Learner 模型预测）
- **结局变量**：全因死亡（n=4,900）、CVD 死亡（n=1,791）、心脏病死亡（n=1,471）
- **协变量**：年龄（作为时间尺度）、性别、种族/民族、家庭收入、BMI、吸烟状态、高血压、尿镉、饮酒、体力活动、健康饮食指数、血清胆固醇、糖化血红蛋白

### Method Overview

1. **骨骼铅预测**：使用 Wang et al. (2022) 开发的 Super Learner 集成算法（包含 8 种算法：线性回归、广义加性模型、岭回归、LASSO、弹性网络、CART、随机森林、XGBoost），基于 7 个预测变量（血铅浓度对数转换、年龄、教育程度、职业类型、BMI、吸烟状态、累计吸烟包年）预测胫骨铅和髌骨铅浓度。模型在 Normative Aging Study 队列中训练，预测性能（Pearson 相关系数）：胫骨铅 0.52，髌骨铅 0.58。

2. **统计分析**：
   - 使用 R 4.2.0 和 SAS 9.4
   - 调查加权 Cox 比例风险模型（svycoxph，R package survey）
   - 以 attained age 为时间尺度（年龄 = 基线年龄 + 随访时间）
   - 暴露变量经对数转换（log-transformed），胫骨铅因含负值加常数 9.607 后转换
   - HR 和 95% CI 计算比较第 90 百分位 vs 第 10 百分位（对数尺度）
   - 同时按 tertile 分析以捕捉非线性剂量反应关系
   - 线性趋势检验：将 tertile 变量作为序数变量拟合
   - 比例风险假设通过 Schoenfeld 残差验证

3. **人群归因分数（PAF）**：使用 Vander Hoorn et al. (2004) 方法，以第 10 百分位为理论最小风险暴露分布，计算若所有人暴露降至该水平可避免的死亡数。

4. **敏感性分析**：
   - 限制随访至 2011 年 12 月 31 日（与 Lanphear et al. 一致）
   - 使用 time-on-study 替代 attained age 作为时间尺度
   - 评估预测骨骼铅在骨骼铅预测变量模型中的增加值

5. **分层分析**：按性别和种族/民族分层评估关联差异。

### Key Findings

1. **主要发现**：预测骨骼铅标志物与 CVD 死亡率的关联远大于血铅：
   - 血铅 CVD HR (90th vs 10th) = 1.63 (95% CI: 1.25-2.14)
   - 预测胫骨铅 CVD HR (90th vs 10th) = 3.32 (95% CI: 1.93-5.73)
   - 预测髌骨铅 CVD HR (90th vs 10th) = 2.42 (95% CI: 1.56-3.76)

2. 全因死亡率的关联在三种铅标志物之间相似（血铅 HR=1.21, 胫骨铅 HR=1.16, 髌骨铅 HR=1.24）。

3. **PAF 结果**：CVD 死亡 PAF 分别为 45.8%（胫骨铅）、33.1%（髌骨铅）、22.8%（血铅），对应每年可避免的 CVD 死亡数分别为 ~361,000、~261,000、~179,000。

4. 种族/民族分层：非西班牙裔黑人中铅与全因死亡关联更强，但 CVD 死亡分层中墨西哥裔美国人无显著关联。

5. 预测骨骼铅在已包含骨骼铅预测变量的模型中仍独立关联 CVD 死亡（胫骨铅 HR=4.81, 髌骨铅 HR=3.03, 血铅 HR=1.65）。

### Reproduction Target

| Target ID | 描述 | 优先级 | 来源 |
|-----------|------|--------|------|
| T1 | 复现血铅 CVD HR 数值 (90th vs 10th percentile) | 高 | Table 2 |
| T2 | 复现胫骨铅 CVD HR 数值 (90th vs 10th percentile) | 高 | Table 2 |
| T3 | 复现髌骨铅 CVD HR 数值 (90th vs 10th percentile) | 高 | Table 2 |
| T4 | 核实 NHANES-III 数据可定位和可下载 | 高 | Data Sharing Statement |
| T5 | 核实 NDI 死亡率数据可定位 | 中 | Methods |
| T6 | 核实代码仓库可用性 | 高 | Data Sharing Statement |

## Questions Mapping

| 问题清单 target_id（逐字） | 复现目标 | 说明 |
|---------------------------|----------|------|
| blood-lead-cvd-hr | T1 | 血铅 CVD 死亡率 HR (90th vs 10th) |
| tibia-lead-cvd-hr | T2 | 胫骨铅 CVD 死亡率 HR (90th vs 10th) |
| patella-lead-cvd-hr | T3 | 髌骨铅 CVD 死亡率 HR (90th vs 10th) |

## Paper Claims

### Analysis Steps

1. 数据获取：从 NHANES-III 获取基线调查数据（人口学、健康行为、体格检查、实验室检测），链接 NDI 死亡数据（截至 2019-12-31）
2. 人群筛选：排除年龄 <20、缺失血铅/死亡数据、缺失骨骼铅预测变量、缺失核心协变量、0 月随访、其他种族
3. 骨骼铅预测：使用 Super Learner 预测模型（Wang et al. 2022）计算每位参与者的预测胫骨铅和髌骨铅浓度
4. 描述性统计：计算基线特征，按血铅 tertile 分层
5. 生存分析：调查加权 Cox 比例风险模型，以 attained age 为时间尺度，暴露变量对数转换
6. HR 计算：比较第 90 vs 第 10 百分位（对数尺度），以及 tertile 分析
7. PAF 计算：使用 Vander Hoorn et al. (2004) 方法
8. 敏感性分析：限制随访时间、改变时间尺度、评估骨骼铅预测变量的增加值
9. 分层分析：按性别和种族/民族分层

### Code and Data Availability

| Resource | URL/Identifier | Purpose | Location in Paper |
|----------|---------------|---------|-------------------|
| NHANES-III 数据 | https://wwwn.cdc.gov/nchs/nhanes/Default.aspx | 基线调查数据 | Data Sharing Statement |
| NDI 死亡率链接数据 | https://www.cdc.gov/nchs/datalinkage/mortality-public.htm | 死亡随访数据 | Methods ("public-use mortality file") |
| 分析数据与 R 代码 | https://github.com/um-mpeg/Bone-lead-mortality | 完整分析数据和 R 代码 | Data Sharing Statement |
| 骨骼铅预测模型 | https://github.com/XinWangUmich/Bone-Lead-Prediction-Models | 胫骨铅和髌骨铅预测模型 | Methods ("Bone Lead Prediction") |
| 补充材料 | NIHMS2048738-supplement-Supplementary_Material.docx (PMC) | Suppl Figure S1, Suppl Tables S1-S4 | "Refer to Web version on PubMed Central for supplementary material" |

### System Requirements

| Component | Requirement | Notes | Location in Paper |
|-----------|------------|-------|-------------------|
| 操作系统 | Not specified | R 和 SAS 均可跨平台运行 | N/A |
| R | version 4.2.0 | 使用 survey 包 (svycoxph) | Statistical Analysis |
| SAS | version 9.4 | 辅助分析 | Statistical Analysis |

### Environment Requirements

| Software | Version | Purpose | Source in Paper |
|----------|---------|---------|-----------------|
| R | 4.2.0 | 主要统计分析 | Statistical Analysis |
| R package survey | Not specified | 调查加权 Cox 模型 (svycoxph) | Statistical Analysis |
| SAS | 9.4 | 辅助分析 | Statistical Analysis |
| Super Learner (R package) | Not specified | 骨骼铅预测模型构建 | Bone Lead Prediction (Wang et al. 2022) |

### Data Requirements

| Database | Accession | Samples | Type | Location in Paper |
|----------|-----------|---------|------|-------------------|
| NHANES-III | Public (https://wwwn.cdc.gov/nchs/nhanes/Default.aspx) | 20,050 adults (initial), 11,628 (final) | 横断面基线调查 + 前瞻性死亡随访 | Methods |
| NDI Mortality | Public-use linked mortality file (https://www.cdc.gov/nchs/datalinkage/mortality-public.htm) | 截至 2019-12-31 | 死亡登记链接数据 | Methods |
| Normative Aging Study | Not publicly available (model training data) | 社区暴露男性队列 | 前瞻性队列（用于训练预测模型） | Bone Lead Prediction |
| 分析数据 | https://github.com/um-mpeg/Bone-lead-mortality (pbmort3.rda) | 11,628 | 处理后分析数据集 | Data Sharing Statement |

### Parameters

| Tool | Parameter | Value | From |
|------|-----------|-------|------|
| 血铅 LOD | 低于检测限填补 | LOD/√2 (0.7 μg/dL) | Methods |
| 胫骨铅常数 | 对数转换前加常数 | 9.607 (abs(min) + 1) | Statistical Analysis |
| 血铅 LOD 值 | 检测限 | 1 μg/dL | Methods |
| 时间尺度 | Cox 模型 | attained age | Statistical Analysis |
| 暴露对比 | 百分位 | 90th vs 10th | Statistical Analysis |
| 统计显著性 | α 阈值 | <0.05 | Statistical Analysis |
| 对数转换 | 暴露变量 | log-transformed | Statistical Analysis |

### Expected Results

| Output | Figure/Table | Expected Value |
|--------|-------------|----------------|
| 血铅 CVD HR (90th vs 10th) | Table 2 | 1.63 (95% CI: 1.25-2.14) |
| 胫骨铅 CVD HR (90th vs 10th) | Table 2 | 3.32 (95% CI: 1.93-5.73) |
| 髌骨铅 CVD HR (90th vs 10th) | Table 2 | 2.42 (95% CI: 1.56-3.76) |
| 血铅全因死亡 HR (90th vs 10th) | Table 2 | 1.21 (95% CI: 1.04-1.40) |
| 胫骨铅全因死亡 HR (90th vs 10th) | Table 2 | 1.16 (95% CI: 0.89-1.52) |
| 髌骨铅全因死亡 HR (90th vs 10th) | Table 2 | 1.24 (95% CI: 1.01-1.51) |
| 血铅心脏病死亡 HR (90th vs 10th) | Table 2 | 1.76 (95% CI: 1.36-2.28) |
| 胫骨铅心脏病死亡 HR (90th vs 10th) | Table 2 | 3.35 (95% CI: 1.91-5.88) |
| 髌骨铅心脏病死亡 HR (90th vs 10th) | Table 2 | 2.39 (95% CI: 1.52-3.76) |
| CVD PAF (血铅) | Table 3 | 22.8% (95% CI: 10.4-33.8) |
| CVD PAF (胫骨铅) | Table 3 | 45.8% (95% CI: 28.1-59.4) |
| CVD PAF (髌骨铅) | Table 3 | 33.1% (95% CI: 18.1-45.8) |
| 中位随访年数 | Table 1 | 26.8 年 |
| 全因死亡数 | Table 1 | 4,900 |
| CVD 死亡数 | Table 1 | 1,791 |
| 心脏病死亡数 | Table 1 | 1,471 |
| 血铅几何均值 | Table 1 | 2.69 μg/dL (95% CI: 2.54-2.84) |
| 预测胫骨铅几何均值 | Table 1 | 6.73 μg/g (95% CI: 6.22-7.25) |
| 预测髌骨铅几何均值 | Table 1 | 16.3 μg/g (95% CI: 15.9-16.8) |

### Figure Reproduction Inventory

| Figure/Panel | Original Image | Caption/Source | Scientific Claim | Plot Type | Required Data | Author Plotting Code/Notebook | Expected Pattern | Source |
|-------------|---------------|----------------|------------------|-----------|---------------|------------------------------|-----------------|--------|
| Figure 1 | 01_plan/paper_markdown/paper/images/img_002.jpg | Hazard ratios (95% CIs) of mortality from all-causes and CVD comparing the 90th vs 10th percentiles of lead biomarkers by sex and race/ethnicity. | 种族/民族分层分析：非西班牙裔黑人全因死亡关联更强，墨西哥裔美国人 CVD 死亡关联不显著 | Forest plot (HR + 95% CI) | 分层 Cox 回归 HR 和 95% CI（按性别和种族/民族） | Not specified (可在 Bone-lead-mortality 仓库的 R 代码中查找) | 按性别(NHW/NHB/MA)和种族/民族分层的 HR 森林图，分全因死亡和 CVD 死亡 | Results, Figure 1 |
| Figure S1 | 仅在补充材料中 | 人群筛选流程图 | Flow chart | 筛选流程数据 | Not specified | 从 20,050 → 11,628 的逐级排除流程图 | Supplementary Material |

**注**：Table 1, 2, 3, 4 为文本表格，非图形。Table 2 为复现目标 T1-T3 的核心数据来源。

## Source Files Reviewed

| File/URL | Type | Local Path | Status | Notes |
|----------|------|------------|--------|-------|
| 论文 PDF (Europe PMC) | PDF | 01_plan/paper.pdf | Downloaded | 703,965 bytes, 通过 Europe PMC PDF render 获取 |
| 论文 Markdown (MinerU) | Markdown | 01_plan/paper_markdown/paper/paper.md | Converted | 通过 mineru-api 转换，提取 7 张图片 |
| 提取图片 | Images | 01_plan/paper_markdown/paper/images/ | Downloaded | 7 张图片: img_001.jpg - img_007.jpg |
| Europe PMC 页面 | Article page | https://europepmc.org/articles/PMC11753055 | Accessed | 获取了 PDF 全文 |
| PMID 元数据 | API | PMID: 38453073 | Resolved | 通过 paperutils 获取 |
| 补充材料 DOCX | Supplementary | NIHMS2048738-supplement-Supplementary_Material.docx | URL found; deferred | PMC CDN 需要 JavaScript，curl 无法直接下载 (51.9KB) |
| 骨骼铅预测模型仓库 | GitHub repo | https://github.com/XinWangUmich/Bone-Lead-Prediction-Models | URL found; inventoried | R 语言，包含 RData 预测模型文件 (~13MB) |
| 分析代码与数据仓库 | GitHub repo | https://github.com/um-mpeg/Bone-lead-mortality | URL found; inventoried | R 语言，包含分析代码和 pbmort3.rda 数据 (~2.8MB) |
| 出版商页面 (ScienceDirect) | Publisher page | https://doi.org/10.1016/j.scitotenv.2024.171511 | 403 Forbidden | Cloudflare 保护，curl 无法访问 |
| PMC 页面 | Article page | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11753055/ | Accessed | 获取 XML 全文，确认补充材料存在 |

## Supplementary Materials Inventory

| Item | Type | URL/Path | Mentioned In | Status | Notes |
|------|------|----------|-------------|--------|-------|
| Suppl Figure S1 | Figure | 补充材料 DOCX 内 | Methods (Study Population) | URL found; deferred | 人群筛选流程图，需从补充材料 DOCX 中提取 |
| Suppl Table S1 | Table | 补充材料 DOCX 内 | Results (sensitivity analyses) | URL found; deferred | 敏感性分析结果表 |
| Suppl Table S2 | Table | 补充材料 DOCX 内 | Results (stratified analyses) | URL found; deferred | 分层分析结果表 |
| Suppl Table S3 | Table | 补充材料 DOCX 内 | Discussion | URL found; deferred | 按血铅类别分层的预测骨骼铅分布 |
| Suppl Table S4 | Table | 补充材料 DOCX 内 | Discussion | URL found; deferred | 按种族/民族分层的铅浓度 |
| Supplementary_Material.docx | Document | https://pmc.ncbi.nlm.nih.gov/articles/instance/11753055/bin/NIHMS2048738-supplement-Supplementary_Material.docx | "Refer to Web version on PubMed Central for supplementary material" | URL found; deferred | 51.9KB, PMC CDN 需 JavaScript 下载，暂未获取 |

## Resource Locations

| Resource | Type | URL/Identifier | Purpose | Location in Paper | Access Notes |
|----------|------|---------------|---------|-------------------|-------------|
| NHANES-III 公开数据 | 调查数据 | https://wwwn.cdc.gov/nchs/nhanes/Default.aspx | 基线调查数据（人口学、实验室、问卷） | Data Sharing Statement | 公开可下载，无需申请 |
| NDI 死亡率链接数据 | 死亡登记数据 | https://www.cdc.gov/nchs/datalinkage/mortality-public.htm | 死亡随访结局数据 | Methods | 公开使用文件，需申请或下载 |
| Bone-lead-mortality 仓库 | 代码 + 分析数据 | https://github.com/um-mpeg/Bone-lead-mortality | 完整分析 R 代码和 cleaned 分析数据集 pbmort3.rda | Data Sharing Statement | 公开 GitHub 仓库，Apache 2.0 许可 |
| Bone-Lead-Prediction-Models 仓库 | 预测模型 | https://github.com/XinWangUmich/Bone-Lead-Prediction-Models | 骨骼铅预测 R 模型文件 | Methods (Bone Lead Prediction) | 公开 GitHub 仓库，包含 .RData 预测模型和示例代码 |
| CDC WONDER | 死亡率统计 | https://wonder.cdc.gov/ | PAF 计算中使用的年均死亡人数 | References | 公开数据库 |
| CDC Leading Causes of Death | 死亡率统计 | https://wisqars.cdc.gov/fatal-leading | PAF 计算中使用的年均死亡人数 | References | 公开数据库 |
| Normative Aging Study | 队列数据 | Not publicly available | 骨骼铅预测模型的训练数据 | Bone Lead Prediction + Wang et al. 2022 | 非公开，仅限授权研究者使用 |

## External Identifier Records

| Identifier | Database | Resolved Type | Title/Description | Linked IDs | Source API | Retrieved At |
|------------|----------|---------------|-------------------|------------|------------|-------------|
| 10.1016/j.scitotenv.2024.171511 | Crossref | Journal Article | Do We Underestimate Risk of Cardiovascular Mortality due to Lead Exposure? | PMID: 38453073, PMCID: PMC11753055 | paperutils (Crossref + Europe PMC) | 2026-08-28 |
| 38453073 | PubMed | Journal Article | Do We Underestimate Risk of Cardiovascular Mortality due to Lead Exposure? | DOI: 10.1016/j.scitotenv.2024.171511, PMCID: PMC11753055 | paperutils | 2026-08-28 |
| PMC11753055 | PubMed Central | Author Manuscript (NIHMS2048738) | Do We Underestimate Risk of Cardiovascular Mortality due to Lead Exposure? | PMID: 38453073, DOI: 10.1016/j.scitotenv.2024.171511 | paperutils + NCBI E-utilities | 2026-08-28 |
| 10.1016/j.chemosphere.2022.137125 | Crossref | Journal Article | Predicting cumulative lead (Pb) exposure using the Super Learner algorithm (Wang et al. 2022) | PMID: 36347347 | paperutils | 2026-08-28 |
| 10.1016/S2468-2667(18)30025-2 | Crossref | Journal Article | Low-level lead exposure and mortality in US adults: a population-based cohort study (Lanphear et al. 2018) | Not resolved | paperutils | 2026-08-28 |

## Source Conflicts And Gaps

| Item | Paper Statement | External Record | Issue |
|------|----------------|-----------------|-------|
| 补充材料 | "Refer to Web version on PubMed Central for supplementary material" | PMC supplementary material 存在但无法通过 curl 下载 | PMC CDN 要求 JavaScript 执行，curl/wget 无法直接获取 51.9KB DOCX 文件。浏览器可访问。 |
| 出版商正式版 | 论文发表于 Sci Total Environ 2024 May 01; 923: 171511 | ScienceDirect 返回 403 Forbidden (Cloudflare) | 出版商页面受 Cloudflare 保护，无法以非浏览器方式访问。仅通过 PMC author manuscript 版本获取全文。 |
| 版本一致性 | 本工作区使用 PMC NIHMS author manuscript 版本 | 存在正式 published version (ScienceDirect) | Author manuscript 与 version of record 内容可能一致，但排版不同。本分析基于 PMC author manuscript。 |
| 代码仓库版本 | 论文引用 Bone-lead-mortality 仓库 | 仓库最后更新于 2023-07-14，单一版本，无 release/tag | 无版本号，无 Zenodo/Figshare DOI 存档 |

## Uncertainties

| Item | Issue | Source |
|------|-------|--------|
| 补充材料内容 | 无法通过命令行下载补充材料 DOCX，内容尚未审查 | PMC CDN 限制 |
| pbmort3.rda 数据范围 | 仓库中的分析数据是否包含 NHANES-III 原始变量还是仅处理后的分析变量，尚未确认 | 仓库文件清单 |
| 预测模型输入数据 | 骨骼铅预测模型需要血铅数据，但 NHANES-III 公开数据是否包含血铅的完整测量值尚未确认 | 数据可用性页面未检查 |
| NDI 数据版本 | 公开使用 NDI 链接死亡率文件可能有多个版本，论文使用的具体版本年份未明确 | Methods |
| 尝试复现方法 | 论文代码使用 R 4.2.0 + SAS 9.4，若仅有 R 代码且 SAS 部分不可获取，可能需要调整 | 代码仓库仅含 R 文件 |

## Decision Record

| Decision | Rationale | Date |
|----------|-----------|------|
| 复现范围 | 仅复现 Blood lead CVD HR、Tibia lead CVD HR、Patella lead CVD HR 三个关键定量结果，并核实数据可定位/可下载和代码仓库可用性。不要求复现全部分析和图表。 | 2026-08-28 |
| 产出语言 | zh（中文） | 2026-08-28 |
| PDF 转换 | 使用 mineru-api 将 PDF 转为 Markdown，成功提取 7 张图片 | 2026-08-28 |
| 补充材料 | 标记为 "URL found; deferred"，因 PMC CDN 需要 JavaScript 无法通过 curl 下载；Phase 2 可尝试浏览器下载 | 2026-08-28 |
| 版本选择 | 使用 PMC NIHMS author manuscript 作为主论文来源；出版商正式版因 Cloudflare 无法访问 | 2026-08-28 |
| 资源获取范围 | 仅获取和登记轻量资源（PDF、Markdown、GitHub 仓库信息）；不下载分析规模数据 | 2026-08-28 |