# Figure Comparison

## Mode

| Field | Value |
|-------|-------|
| Figure Validation Status | generated |
| Paper Figure Source | N/A (no original image provided) |
| Generated Figures Directory | ../05_run/figures/ |

## Figure Evidence

| Figure/Panel | Original Image | Generated Figure | Paper Claim | Source Data | Comparison Type | Result | Notes |
|--------------|----------------|------------------|-------------|-------------|-----------------|--------|-------|
| Figure 1 (volcano plot) | Not provided | volcano_plot.png, volcano_plot.pdf | Gene_A upper-right, Gene_B upper-left, others near origin | deseq2_results.csv | Pattern-based visual | Confirmed | Generated plot matches described pattern exactly |

## Visual Assessment

### Figure 1 — Volcano Plot: Control vs Treatment

**Panel description**: Single-panel volcano plot with log2 Fold Change on x-axis and -log10(adjusted p-value) on y-axis. Significant genes (padj < 0.05) shown in red; non-significant genes in gray.

**Gene_A (upper-right)**: Confirmed. Gene_A appears at approximately log2FC = +2.9, -log10(padj) ≈ 119, clearly in the upper-right quadrant. Labeled and colored red. Matches paper claim of "upper-right (high positive log2FC, high -log10(padj))".

**Gene_B (upper-left)**: Confirmed. Gene_B appears at approximately log2FC = -2.0, -log10(padj) ≈ 41, clearly in the upper-left quadrant. Labeled and colored red. Matches paper claim of "upper-left (negative log2FC, high -log10(padj))".

**Gene_C–Gene_J (near origin)**: Confirmed. All 8 non-significant genes form a tight cluster at log2FC ≈ 0, -log10(padj) ≈ 0, shown in gray. Matches paper claim of "clustered near origin (log2FC ≈ 0, low -log10(padj))".

**Overall pattern**: The generated volcano plot faithfully reproduces the scientific pattern described in the paper. The two significant genes are clearly separated from the non-significant cluster, with correct directional placement. The -log10(padj) scale extends to ~120 due to the extremely small p-values from the actual count data, whereas the paper's idealized values would produce a much shorter y-axis. This is a quantitative difference that does not affect the scientific interpretation.

**Limitation**: No original figure image was provided in the paper (plan.md confirms "Not provided" for Figure 1 original image). Therefore, pixel-level comparison is not possible. Validation is based on pattern matching against the paper's textual description of the expected figure.

## Non-Visual Figure Checks

| Check | Result | Notes |
|-------|--------|-------|
| Plotting script exists | Yes | volcano_plot.R in 05_run/ |
| Input data file exists | Yes | deseq2_results.csv used as input |
| Output file format | PNG + PDF | Both formats generated |
| Plot title | Present | "Volcano Plot: Control vs Treatment" with subtitle "Differential Expression Analysis (DESeq2 + apeglm)" |
| Axis labels | Present | x-axis: "log2 Fold Change", y-axis: "-log10 (adjusted p-value)" |
| Legend | Present | "Not Significant" (gray) and "Significant (padj < 0.05)" (red) |
| Gene labels | Present | Gene_A and Gene_B labeled on plot |
| Reference lines | Present | Vertical dashed line at log2FC = 0, horizontal dashed line at -log10(padj) = 0 |
