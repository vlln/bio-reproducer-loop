# bio-reproducer E2E Benchmark 论文清单

用于 end-to-end 测试的生物信息学论文列表，按复杂度递增排列。

## 选文标准

- 数据可公开下载（GEO / Bioconductor），且尽量小（< 50 MB）
- 运行环境简单（R + Bioconductor 即可）
- 计算快（秒级到分钟级）
- PDF 可获取（开放获取或 PMC 免费）
- 分析流程有标准答案可对照（Bioconductor vignette 的经典示例）

---

## Tier 1: 最小可行（基线测试）

### 1. Himes et al. 2014

| 字段 | 值 |
|------|-----|
| title | RNA-Seq transcriptome profiling identifies CRISPLD2 as a glucocorticoid responsive gene that modulates cytokine function in airway smooth muscle cells |
| doi | 10.1371/journal.pone.0099625 |
| pmid | 24926665 |
| pmcid | PMC4057123 |
| journal | PLOS ONE, 2014 |
| open_access | true |
| organism | Homo sapiens |
| geo_accession | GSE52778 |
| bioconductor_pkg | airway |
| n_samples | 8 |
| design | 2 groups (treated vs control), paired by cell line |
| analysis | DESeq2 差异表达 |
| analysis_type | differential_expression |
| data_format | count matrix (RangedSummarizedExperiment) |
| data_size_mb | ~10 |
| env | R + DESeq2 + airway |
| computation_time | < 1 min |
| known_answer | DESeq2 vignette 有标准结果，7 个已知的 dexamethasone 响应基因可校验 |
| notes | DESeq2 官方 vignette 示例数据集，最经典的入门案例 |

### 2. Bottomly et al. 2011

| 字段 | 值 |
|------|-----|
| title | Evaluating gene expression in C57BL/6J and DBA/2J mouse striatum using RNA-Seq and microarrays |
| doi | 10.1371/journal.pone.0017820 |
| pmid | 21455293 |
| pmcid | PMC3063777 |
| journal | PLOS ONE, 2011 |
| open_access | true |
| organism | Mus musculus |
| geo_accession | GSE26024 |
| bioconductor_pkg | compcodeR (bottomly dataset) |
| n_samples | 21 (RNA-seq: 10 B6 + 11 D2) |
| design | 2 groups (strain comparison) |
| analysis | DESeq2 / edgeR / limma 差异表达 |
| analysis_type | differential_expression |
| data_format | count matrix |
| data_size_mb | ~20 |
| env | R + DESeq2 / edgeR / limma |
| computation_time | < 2 min |
| known_answer | 常用教学示例，多工具可交叉验证 |
| notes | 两株系比较，适合测试多工具一致性 |

### 3. Brooks et al. 2011

| 字段 | 值 |
|------|-----|
| title | Conservation of an RNA regulatory map between Drosophila and mammals |
| doi | 10.1101/gr.108662.110 |
| pmid | 20921232 |
| pmcid | PMC3032923 |
| journal | Genome Research, 2011 |
| open_access | false (PMC free) |
| organism | Drosophila melanogaster |
| geo_accession | GSE18508 |
| bioconductor_pkg | pasilla |
| n_samples | 7 (subset used in tutorials) |
| design | 2 groups (pasilla RNAi knockdown vs control) |
| analysis | DEXSeq 差异外显子使用 |
| analysis_type | differential_exon_usage |
| data_format | count matrix (ExonCountSet) |
| data_size_mb | ~5 |
| env | R + DEXSeq + pasilla |
| computation_time | < 2 min |
| known_answer | DEXSeq vignette 标准结果 |
| notes | 数据最小，测试外显子水平分析 |

---

## Tier 2: 稍微复杂

### 4. Tuch et al. 2010

| 字段 | 值 |
|------|-----|
| title | Tumor transcriptome sequencing reveals allelic expression imbalances associated with copy number alterations |
| doi | 10.1371/journal.pone.0009317 |
| pmid | 20174472 |
| pmcid | PMC2824832 |
| journal | PLOS ONE, 2010 |
| open_access | true |
| organism | Homo sapiens |
| geo_accession | GSE19089 |
| bioconductor_pkg | — (需从 GEO 下载) |
| n_samples | 6 (3 tumor + 3 matched normal) |
| design | paired design (tumor vs matched normal) |
| analysis | edgeR paired test 差异表达 |
| analysis_type | differential_expression_paired |
| data_format | count matrix |
| data_size_mb | ~10 |
| env | R + edgeR |
| computation_time | < 1 min |
| known_answer | edgeR User Guide 案例 |
| notes | 配对设计，需处理 blocking factor (`~patient + treatment`) |

### 5. Fu et al. 2015

| 字段 | 值 |
|------|-----|
| title | EGF-mediated induction of Mcl-1 at the switch to lactation is essential for alveolar cell survival |
| doi | 10.1038/ncb3117 |
| pmid | 25730472 |
| pmcid | — |
| journal | Nature Cell Biology, 2015 |
| open_access | false |
| organism | Mus musculus |
| geo_accession | GSE60450 |
| bioconductor_pkg | — (GEO 直接下载) |
| n_samples | 12 |
| design | 2×2 factorial: cell type (luminal/basal) × stage (virgin/lactating) |
| analysis | edgeR/limma 差异表达 + 交互效应 |
| analysis_type | differential_expression_factorial |
| data_format | count matrix (GEO supplementary) |
| data_size_mb | ~20 |
| env | R + edgeR / limma |
| computation_time | < 2 min |
| known_answer | edgeR User Guide 案例 |
| notes | 2×2 因子设计，测试交互项 (`~cell * stage`) |

### 6. Leong et al. 2014

| 字段 | 值 |
|------|-----|
| title | A global non-coding RNA system modulates fission yeast protein levels in response to stress |
| doi | 10.1038/ncomms4947 |
| pmid | 24853205 |
| pmcid | — |
| journal | Nature Communications, 2014 |
| open_access | true |
| organism | Schizosaccharomyces pombe |
| geo_accession | GSE56761 |
| bioconductor_pkg | fission |
| n_samples | 36 |
| design | time course (6 time points) × genotype (WT vs atf21Δ) |
| analysis | DESeq2 LRT 时间序列 + 基因型交互 |
| analysis_type | time_course_with_interaction |
| data_format | RangedSummarizedExperiment (Bioconductor) |
| data_size_mb | ~30 |
| env | R + DESeq2 + fission |
| computation_time | 2-5 min |
| known_answer | DESeq2 LRT vignette 标准结果 |
| notes | 时间序列 + 双因子交互，需用 LRT 检验，DESeq2 vignette 示例 |

---

## Tier 3: 后续候选（更大/更复杂）

| 论文 | PMID | 数据集 | 特点 |
|------|------|--------|------|
| SEQC Consortium 2014 | 25150838 | GSE49712 | 多平台 benchmark，大样本量 |
| Pickrell et al. 2010 | 20220756 | GSE19480 | eQTL 分析，69 样本 |
| 含 batch effect 的数据集 | — | bladderbatch (microarray) | 批次效应校正 |

---

## 复杂度维度覆盖

| 维度 | 覆盖论文 |
|------|---------|
| 两组比较 | Himes 2014, Bottomly 2011 |
| 配对设计 | Himes 2014, Tuch 2010 |
| 多工具比较 | Bottomly 2011 |
| 外显子水平 | Brooks 2011 |
| 2×2 因子交互 | Fu 2015 |
| 时间序列 | Leong 2014 |
| 双因子交互 | Leong 2014 |
| LRT 检验 | Leong 2014 |
| 不同物种 | Human (Himes, Tuch), Mouse (Bottomly, Fu), Fly (Brooks), Yeast (Leong) |

---

## 使用方式

### 通过 DOI 运行

```bash
loop run bio-reproducer \
  --args '{"paper_doi": "10.1371/journal.pone.0099625", "language": "zh"}'
```

### 通过本地 PDF 运行

```bash
loop run bio-reproducer \
  --args '{"paper_path": "paper.pdf", "language": "zh"}'
```

### 推荐测试顺序

1. `10.1371/journal.pone.0099625` (Himes 2014) — 基线
2. `10.1371/journal.pone.0017820` (Bottomly 2011) — 多工具
3. `10.1101/gr.108662.110` (Brooks 2011) — 外显子
4. `10.1371/journal.pone.0009317` (Tuch 2010) — 配对
5. `10.1038/ncb3117` (Fu 2015) — 因子交互
6. `10.1038/ncomms4947` (Leong 2014) — 时间序列