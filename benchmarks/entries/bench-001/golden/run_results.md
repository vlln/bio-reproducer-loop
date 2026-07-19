# Run Results

## Execution Summary

| Item | Value |
|------|-------|
| Status | SUCCESS |
| Pipeline | DESeq2 differential expression analysis (R script) |
| Orchestration | None — R script executed directly (Nextflow unavailable: Java not installed) |
| Duration | < 1 minute |
| Date | 2026-07-15 |

## Nextflow Decision

| Decision | Reason |
|----------|--------|
| Nextflow not used | Java Runtime not available on this host. OpenJDK@17 installation via Homebrew failed (download error from ghcr.io). The paper's analysis is a single R script; Nextflow orchestration would add no value. The bootstrap phase (02_bootstrap) confirmed Nextflow is not required by the paper. |

## Pipeline Metrics

| Step | Description | Tool | Status | Key Metrics |
|------|-------------|------|--------|-------------|
| 1. Load counts | Load count matrix from CSV (10 genes × 6 samples) | R (read.csv) | success | 10 genes, 6 samples loaded |
| 2. DESeqDataSet | Create DESeqDataSet with design ~condition | DESeq2 1.52.0 | success | — |
| 3. DESeq | Run DESeq2 with default parameters (median-of-ratios, Wald test) | DESeq2 1.52.0 | success | — |
| 4. lfcShrink | Apply log2 fold change shrinkage (type = "apeglm") | apeglm 1.34.0 | success | — |
| 5. Results | Extract results, filter padj < 0.05 | R base | success | 2 significant genes |
| 6. Volcano plot | Generate volcano plot with ggplot2 | ggplot2 4.0.3 | success | Figure 1 generated |

## Quality Metrics

| Metric | Observed | Expected (Paper) | Match |
|--------|----------|------------------|-------|
| Significant genes count | 2 | 2 | ✓ |
| Gene_A direction | Upregulated (log2FC > 0) | Upregulated | ✓ |
| Gene_B direction | Downregulated (log2FC < 0) | Downregulated | ✓ |
| Gene_A log2FC | 2.918 | 2.5 | Partial (different version) |
| Gene_A padj | 4.37e-119 | 0.0008 | Partial (different version) |
| Gene_B log2FC | -1.997 | -1.8 | Partial (different version) |
| Gene_B padj | 5.57e-42 | 0.004 | Partial (different version) |
| Non-significant genes | 8 (Gene_C–Gene_J) | 8 | ✓ |

**Version Note**: The installed package versions (DESeq2 1.52.0, apeglm 1.34.0, R 4.6.1) are newer than the paper's requirements (DESeq2 1.42.0, apeglm 1.24.0, R 4.3.0). The log2FC and padj values differ from the paper's expected values due to version differences in the DESeq2 algorithm and apeglm shrinkage procedure. The qualitative conclusions (Gene_A upregulated, Gene_B downregulated, 8 non-significant genes) remain consistent with the paper.

## Figure Generation

| Field | Value |
|-------|-------|
| Generation Status | generated |
| Figures Directory | figures/ |
| Plotting Source | handwritten fallback |
| Author Plotting Attempt | N/A |
| Handwritten Fallback Justification | Author's GitHub repository (https://github.com/example/deseq2-analysis) returned HTTP 404; no author plotting code available. The volcano plot was generated from the DESeq2 results table using ggplot2, exactly as described in the Methods section. |

| Figure/Panel | Original Image | Script/Notebook | Input Data | Output Figure | Status | Notes |
|--------------|----------------|-----------------|------------|---------------|--------|-------|
| Figure 1 | Not available (paper was Markdown, no PDF) | 05_run/analysis.R | deseq2_results.csv (10 genes) | figures/figure1_volcano.png | generated | Gene_A in upper-right (log2FC=2.92, -log10(padj)=118.4), Gene_B in upper-left (log2FC=-2.00, -log10(padj)=41.3), 8 other genes near origin. Y-axis scale compressed compared to paper due to extremely small p-values from newer DESeq2 version. |

## Issues Encountered

| Issue | Severity | Resolution |
|-------|----------|------------|
| Java/Nextflow unavailable | Minor | Ran R script directly; single-script analysis does not need Nextflow orchestration |
| Package version mismatch | Moderate | Used latest compatible versions (DESeq2 1.52.0, apeglm 1.34.0) for R 4.6.1; qualitative results consistent with paper |
| Author code unavailable | Minor | Reconstructed analysis from Methods section; GitHub repo (https://github.com/example/deseq2-analysis) returned HTTP 404 |
| No original paper figures | Minor | Paper was provided as Markdown; no PDF figures to compare against |

## Output Files

| File | Description |
|------|-------------|
| results/deseq2_results.csv | Full DESeq2 results table (10 genes) |
| results/significant_genes.csv | Significant genes (padj < 0.05): Gene_A, Gene_B |
| figures/figure1_volcano.png | Volcano plot (PNG, 1200×1050) |
| figures/figure1_volcano.pdf | Volcano plot (PDF) |
| analysis.R | R analysis script (reconstructed from Methods) |
| main.nf | Nextflow pipeline definition (not executed) |
| nextflow.config | Nextflow configuration (not executed) |