# Paper: Differential Expression Analysis of Synthetic Gene Response to Treatment

DOI: 10.1234/bench.001

## Paper Understanding

### Research Question
What are the differentially expressed genes between Control and Treatment conditions in a synthetic 10-gene panel?

### Study Design
- 10 genes measured via RNA-seq
- 2 conditions: Control vs Treatment
- 3 biological replicates per condition
- 6 samples total

### Method Overview
- Count matrix loaded from CSV
- Normalization with DESeq2 default (median-of-ratios)
- Differential expression testing with DESeq2 Wald test
- Log2 fold change shrinkage with apeglm
- Significance threshold: padj < 0.05
- Visualization: volcano plot with ggplot2

### Key Findings
- Gene_A: significantly upregulated (log2FC = 2.5, padj = 0.0008)
- Gene_B: significantly downregulated (log2FC = -1.8, padj = 0.004)
- 8 other genes: no significant change
- Volcano plot: Figure 1

### Reproduction Target
Reproduce the differential expression analysis and generate the volcano plot (Figure 1) showing Gene_A and Gene_B as significant.

## Paper Claims

### Analysis Steps
1. Load count matrix: `counts.csv` → R → DESeq2 → normalized counts
2. Differential expression: normalized counts → DESeq2 → DE results table
3. Visualization: DE results → ggplot2 → volcano plot (Figure 1)

### Environment Requirements
| Software | Version | Purpose | Source in Paper |
|----------|---------|---------|-----------------|
| R | 4.3.0 | Statistical computing | Methods |
| DESeq2 | 1.42.0 | Differential expression analysis | Methods |
| ggplot2 | 3.5.0 | Data visualization | Methods |
| apeglm | 1.24.0 | Log2 fold change shrinkage | Methods |

### Data Requirements
| Database | Accession | Samples | Type | Location in Paper |
|----------|-----------|---------|------|-------------------|
| GEO | GSE99999 | 6 | Count matrix | Data Availability |
| Supplementary | counts.csv | 6 | Count matrix | Supplementary Table S1 |

### Parameters
| Tool | Parameter | Value | From |
|------|-----------|-------|------|
| DESeq2 | significance_threshold | padj < 0.05 | Methods |
| DESeq2 | design_formula | ~ condition | Methods |
| DESeq2 | lfcShrink_type | apeglm | Methods |

### Expected Results
| Output | Figure/Table | Expected Value |
|--------|--------------|----------------|
| Gene_A log2FC | Table 1 | 2.5 |
| Gene_A padj | Table 1 | 0.0008 |
| Gene_B log2FC | Table 1 | -1.8 |
| Gene_B padj | Table 1 | 0.004 |
| Volcano plot | Figure 1 | Gene_A and Gene_B highlighted |

### Figure Reproduction Inventory
| Figure/Panel | Caption/Source | Plot Type | Required Data | Expected Pattern |
|--------------|----------------|-----------|---------------|------------------|
| Figure 1 | Volcano plot of differential expression | volcano | DE results table | Gene_A (right, high), Gene_B (left, mid-high), others centered near zero |

## Uncertainties
| Item | Issue | Source |
|------|-------|--------|
| Exact normalization | "Default parameters" could mean different normalization methods | Methods |
| ggplot2 version | Listed as 3.5.0, may need compatible R version | Methods |