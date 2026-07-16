# Validation Checks Plan

## Check Definitions

Checks are derived from plan.md Expected Results, Key Findings, and Reproduction Target.

### Dimension 1: Data Integrity (weight: 25%)

| Check ID | Metric | Type | Expected | Source |
|----------|--------|------|----------|--------|
| D1 | Gene count in results | Auto | 10 genes (Gene_A–Gene_J) | plan.md Study Design |
| D2 | Sample count in normalized counts | Auto | 6 samples (3 Control + 3 Treatment) | plan.md Study Design |
| D3 | Output files present and non-empty | Auto | deseq2_results.csv, normalized_counts.csv, volcano_plot.png/pdf | plan.md Expected Results |
| D4 | Results table structure | Auto | Columns: gene, baseMean, log2FoldChange, lfcSE, pvalue, padj, significant | plan.md Analysis Steps |

### Dimension 2: Process Quality (weight: 25%)

| Check ID | Metric | Type | Expected | Source |
|----------|--------|------|----------|--------|
| Q1 | Pipeline process success rate | Auto | 2/2 processes completed | plan.md Analysis Steps |
| Q2 | DESeq2 version match | Auto | 1.42.0 (paper) vs actual | plan.md Environment Requirements |
| Q3 | R version match | Auto | 4.3.0 (paper) vs actual | plan.md Environment Requirements |
| Q4 | ggplot2 version match | Auto | 3.5.0 (paper) vs actual | plan.md Environment Requirements |

### Dimension 3: Quantitative Concordance (weight: 30%)

| Check ID | Metric | Type | Expected | Source |
|----------|--------|------|----------|--------|
| R1 | Gene_A log2FC direction | Auto | Positive (upregulated) | plan.md Key Findings |
| R2 | Gene_B log2FC direction | Auto | Negative (downregulated) | plan.md Key Findings |
| R3 | Significant gene count | Auto | 2 (padj < 0.05) | plan.md Expected Results |
| R4 | Gene_A log2FC magnitude | Auto | 2.5 | plan.md Expected Results |
| R5 | Gene_B log2FC magnitude | Auto | -1.8 | plan.md Expected Results |
| R6 | Gene_A padj magnitude | Auto | 0.0008 | plan.md Expected Results |
| R7 | Gene_B padj magnitude | Auto | 0.004 | plan.md Expected Results |
| R8 | Non-significant genes (C–J) padj > 0.05 | Auto | 8 genes not significant | plan.md Key Findings |

### Dimension 4: Figure and Finding Reproduction (weight: 20%)

| Check ID | Metric | Type | Expected | Source |
|----------|--------|------|----------|--------|
| K1 | Volcano plot generated | Auto | Figure file exists | plan.md Expected Results |
| K2 | Gene_A position in volcano plot | Visual | Upper-right quadrant | plan.md Figure Reproduction Inventory |
| K3 | Gene_B position in volcano plot | Visual | Upper-left quadrant | plan.md Figure Reproduction Inventory |
| K4 | Non-significant genes near origin | Visual | Gene_C–J clustered near log2FC=0, low significance | plan.md Figure Reproduction Inventory |
| K5 | Core biological conclusion | Manual | Gene_A up, Gene_B down, others not DE | plan.md Key Findings |
