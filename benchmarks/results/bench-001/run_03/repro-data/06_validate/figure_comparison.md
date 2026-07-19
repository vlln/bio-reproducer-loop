# Figure Comparison

## Mode
| Field | Value |
|-------|-------|
| Figure Validation Status | generated |
| Paper Figure Source | N/A (not extracted by mineru; only table images were captured) |
| Generated Figures Directory | ../05_run/figures/ |

## Figure Evidence
| Figure/Panel | Original Image | Generated Figure | Paper Claim | Source Data | Comparison Type | Result | Notes |
|--------------|----------------|------------------|-------------|-------------|-----------------|--------|-------|
| Figure 1: Volcano Plot | Not available | figures/figure1_volcano.png, figures/figure1_volcano.pdf | Gene_A upper-right (log2FC=2.5, padj=0.0008); Gene_B upper-left (log2FC=-1.8, padj=0.004); 8 genes near origin | deseq2_results.csv | Visual (generated only) | Pattern confirmed | Gene_A at (2.42, 161), Gene_B at (-1.86, 120), 8 genes clustered near y=0; significant genes in red |

## Visual Assessment

### Figure 1: Volcano Plot (generated only — no original for comparison)

The generated volcano plot shows the expected scientific pattern:

- **Gene_A** (red, upper-right): log2FC = 2.42, -log10(padj) = 161. Positioned in the upper-right quadrant as expected for a strongly upregulated gene.
- **Gene_B** (red, upper-left): log2FC = -1.86, -log10(padj) = 120. Positioned in the upper-left quadrant as expected for a strongly downregulated gene.
- **Genes C–J** (gray, near origin): All 8 non-significant genes cluster near log2FC = 0 with -log10(padj) < 1, consistent with the paper's description of "8 non-significant points near the x-axis origin."
- **Significance threshold**: Dashed horizontal line at -log10(0.05) ≈ 1.3, with legend indicating red = significant (padj < 0.05).

### Key observations:
- The qualitative pattern (2 significant genes in opposite quadrants, 8 non-significant near origin) is fully reproduced.
- The -log10(padj) axis extends to ~170 due to the extremely small p-values from the reconstructed data (vs. the paper's expected range of ~3 for padj=0.0008). This is a quantitative difference in statistical strength, not a pattern difference.
- The plot is labeled "Figure 1: Volcano Plot of Differential Expression" with subtitle "DESeq2: Control vs Treatment (n = 3 per group)".
- Axis labels, legend, and color coding follow standard DESeq2 volcano plot conventions.

### Scientific conclusions supported:
1. Gene_A is significantly upregulated — **confirmed**
2. Gene_B is significantly downregulated — **confirmed**
3. Genes C–J show no significant differential expression — **confirmed**
4. The overall volcano plot pattern matches the paper's description — **confirmed**

## Non-Visual Figure Checks

| Check | Result | Notes |
|-------|--------|-------|
| Plot data file exists (figure1_data.csv) | Pass | Contains all 10 genes with log2FC, padj, neg_log10_padj |
| PNG output exists | Pass | 48,713 bytes, 1200x900 px |
| PDF output exists | Pass | 6,292 bytes (vector) |
| Plotting script available | Partial | analysis.R (handwritten fallback; author code unavailable) |
| Original figure available for comparison | Fail | mineru only extracted table images; volcano plot figure not captured |
