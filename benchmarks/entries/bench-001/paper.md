# Differential Expression Analysis of Synthetic Gene Response to Treatment

**Authors:** A. Researcher, B. Scientist

**DOI:** 10.1234/bench.001

---

## Abstract

**Background:** Understanding gene expression changes in response to treatment is a fundamental task in transcriptomics. This study examines a synthetic 10-gene panel to identify differentially expressed genes between Control and Treatment conditions.

**Methods:** RNA-seq count data for 10 genes were profiled across 6 samples (3 Control, 3 Treatment). Differential expression analysis was performed using DESeq2 v1.42.0 in R v4.3.0. Significance was defined as adjusted p-value < 0.05. Log2 fold change shrinkage was applied using the apeglm method.

**Results:** Gene_A showed strong upregulation with log2FC = 2.5 (padj = 0.0008). Gene_B showed strong downregulation with log2FC = -1.8 (padj = 0.004). The remaining 8 genes showed no significant change. Results are visualized in a volcano plot (Figure 1).

**Conclusions:** The analysis successfully identified two differentially expressed genes. Gene_A and Gene_B are robust markers of Treatment response in this synthetic dataset.

---

## Introduction

RNA-sequencing (RNA-seq) is the standard method for profiling genome-wide gene expression. A core analysis task is identifying genes that are differentially expressed between experimental conditions. The DESeq2 package (Love et al., 2014) is widely used for this purpose.

This study presents a minimal but complete differential expression analysis pipeline: count matrix loading, normalization, statistical testing with DESeq2, and visualization with a volcano plot. The small 10-gene panel makes the analysis transparent and verifiable.

---

## Methods

### Sample Preparation

RNA-seq was performed on 6 samples:
- **Control group:** 3 biological replicates (Control_1, Control_2, Control_3)
- **Treatment group:** 3 biological replicates (Treatment_1, Treatment_2, Treatment_3)

Each sample was profiled for the same 10 genes. The count matrix is provided as `counts.csv` (Supplementary Table S1).

### Data Processing

Count data were normalized and analyzed using DESeq2 v1.42.0 in R v4.3.0. The analysis followed the standard DESeq2 workflow:

1. Load count matrix from CSV
2. Create DESeqDataSet with design formula `~ condition`
3. Run DESeq2 with default parameters
4. Apply log2 fold change shrinkage with `lfcShrink(type = "apeglm")`
5. Extract results at adjusted p-value < 0.05

### Visualization

A volcano plot was generated using ggplot2 v3.5.0, displaying -log10(adjusted p-value) on the y-axis against log2 fold change on the x-axis. Significant genes (padj < 0.05) were highlighted in red.

### Software Versions

| Software | Version | Purpose |
|----------|---------|---------|
| R | 4.3.0 | Statistical computing environment |
| DESeq2 | 1.42.0 | Differential expression analysis |
| ggplot2 | 3.5.0 | Data visualization |
| apeglm | 1.24.0 | Log2 fold change shrinkage |

---

## Results

### Differential Expression

DESeq2 identified 2 significantly differentially expressed genes (padj < 0.05):

| Gene | log2FC | padj | Direction |
|------|--------|------|-----------|
| Gene_A | 2.5 | 0.0008 | Upregulated |
| Gene_B | -1.8 | 0.004 | Downregulated |
| Gene_C | 0.02 | 0.95 | Not significant |
| Gene_D | 0.05 | 0.88 | Not significant |
| Gene_E | -0.03 | 0.92 | Not significant |
| Gene_F | 0.08 | 0.78 | Not significant |
| Gene_G | -0.01 | 0.97 | Not significant |
| Gene_H | 0.04 | 0.90 | Not significant |
| Gene_I | 0.01 | 0.98 | Not significant |
| Gene_J | 0.03 | 0.93 | Not significant |

Gene_A showed strong upregulation with log2FC = 2.5 and padj = 0.0008, indicating a robust response to Treatment. Gene_B showed strong downregulation with log2FC = -1.8 and padj = 0.004.

### Figure 1: Volcano Plot

![Figure 1: Volcano plot showing -log10(adjusted p-value) vs log2 fold change for all 10 genes. Gene_A appears in the upper-right quadrant (high log2FC, high significance). Gene_B appears in the upper-left quadrant (negative log2FC, high significance). The remaining 8 genes cluster near the origin.](figures/figure1_volcano.png)

---

## Data Availability

The count matrix is available as Supplementary Table S1 (`counts.csv`), containing 10 rows (genes) and 6 columns (samples). The dataset is also deposited at GEO under accession **GSE99999**.

The analysis script is available at `https://github.com/example/deseq2-analysis`.

---

## Supplementary Materials

### Supplementary Table S1: Count Matrix

The count matrix is provided in `counts.csv` with the following structure:
- **Rows:** 10 genes (Gene_A through Gene_J)
- **Columns:** 6 samples (Control_1, Control_2, Control_3, Treatment_1, Treatment_2, Treatment_3)
- **Values:** Raw integer counts

---

## References

1. Love, M.I., Huber, W., & Anders, S. (2014). Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. *Genome Biology*, 15(12), 550.
2. Zhu, A., Ibrahim, J.G., & Love, M.I. (2019). Heavy-tailed prior distributions for sequence count data: removing the noise and preserving large differences. *Bioinformatics*, 35(12), 2084-2092.