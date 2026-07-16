# Figure Comparison

## Mode

| Field | Value |
|-------|-------|
| Figure Validation Status | validated |
| Paper Figure Source | N/A (paper provided as Markdown only; no PDF or image available) |
| Generated Figures Directory | ../05_run/figures/ |

## Figure Evidence

| Figure/Panel | Original Image | Generated Figure | Paper Claim | Source Data | Comparison Type | Result | Notes |
|--------------|----------------|------------------|-------------|-------------|-----------------|--------|-------|
| Figure 1: Volcano Plot | Not available | figures/volcano_plot.png, figures/volcano_plot.pdf | Gene_A and Gene_B are significant DEGs; remaining 8 genes are not | deseq2_results.csv | Pattern-based (no original image) | Confirmed | Generated plot matches described layout: Gene_A upper-right, Gene_B upper-left, 8 genes near origin |

## Visual Assessment

### Figure 1: Volcano Plot

**Panel-level assessment:**

The generated volcano plot (1200×900 px, PNG + PDF) displays the following features consistent with the paper's description:

1. **Axes**: x-axis shows log2 Fold Change (range approximately −2.5 to +3.5); y-axis shows −log₁₀(adjusted p-value) (range 0 to ~120). This matches the paper's described layout.

2. **Gene_A position**: Located at approximately (2.92, 119) — upper-right quadrant, far above the significance threshold. The paper describes Gene_A at (2.5, ~3.10); the x-position is ~17% further right than described, and the y-position is dramatically higher due to the much more extreme p-value (4.37e-119 vs 0.0008). Despite the magnitude difference, the qualitative position (upper-right, highly significant) is correct.

3. **Gene_B position**: Located at approximately (−2.0, 41) — upper-left quadrant, well above the significance threshold. The paper describes Gene_B at (−1.8, ~2.40); similar to Gene_A, the x-position is ~11% further left and the y-position is much higher due to the more extreme p-value. Qualitative position (upper-left, highly significant) is correct.

4. **Non-significant genes**: 8 genes (Gene_C through Gene_J) cluster tightly near the origin (log2FC ≈ 0, −log₁₀(padj) ≈ 0), all below the dashed significance threshold line at padj = 0.05. This matches the paper's description of "8 genes near origin."

5. **Color coding**: Significant genes (Gene_A, Gene_B) are highlighted in red; non-significant genes are grey. This matches the paper's described visualization.

6. **Threshold line**: A dashed horizontal line at −log₁₀(0.05) ≈ 1.3 separates significant from non-significant genes. Present and correctly positioned.

7. **Gene labels**: Gene_A label is partially cut off at the right edge of the plot (shows "Gen" only); Gene_B label is fully visible. This is a minor cosmetic issue that does not affect scientific interpretation.

**Scientific conclusion**: The volcano plot fully supports the paper's core finding — exactly two genes (Gene_A upregulated, Gene_B downregulated) are statistically significant, while the remaining 8 genes show no differential expression. The visual pattern is qualitatively identical to what the paper describes, despite quantitative differences in p-value magnitudes.

## Non-Visual Figure Checks

| Check | Result | Notes |
|-------|--------|-------|
| Plotting script exists | Yes | analysis.R in 05_run/ directory |
| Plotting script follows paper workflow | Yes | Uses DESeq2 results as input; ggplot2 for visualization; matches 5-step workflow |
| Input data for plot | Correct | deseq2_results.csv with all 10 genes, log2FoldChange_shrunken and padj columns |
| Output file formats | PNG (150 dpi) + PDF | Both formats generated as expected |
| Plot dimensions | 8×6 inches | Standard publication-quality size |
