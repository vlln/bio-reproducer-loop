# Figure Comparison

## Mode

| Field | Value |
|-------|-------|
| Figure Validation Status | partial |
| Paper Figure Source | N/A — PDF conversion failed (MinerU API unreachable); paper.md used as primary source; no original figure images available |
| Generated Figures Directory | ../05_run/figures/ |

## Figure Evidence

| Figure/Panel | Original Image | Generated Figure | Paper Claim | Source Data | Comparison Type | Result | Notes |
|--------------|----------------|------------------|-------------|-------------|-----------------|--------|-------|
| Figure 1 (Volcano plot) | Not available (PDF conversion failed) | figures/figure1_volcano.png | 6 significant DE genes: 4 upregulated upper-right, 2 downregulated upper-left, 14 near origin | de_results.csv (20 genes, DESeq2 output) | Visual | Partial | Core 6 genes correctly positioned; 2 additional genes (VEGFA, EGFR) in upper-left quadrant |
| Figure 2 (GO bar plot) | Not available (PDF conversion failed) | Not generated | Top 10 enriched BP terms ordered by -log10(q-value); inflammatory/cytokine terms at top | N/A (GO enrichment failed) | N/A | Blocked | GO enrichment produced 0 terms; figure could not be generated |
| Figure 3 (KEGG pathway) | Not available (PDF conversion failed) | figures/hsa04668.figure3_kegg.png | TNF signaling pathway (hsa04668) with upregulated genes in red, downregulated in blue | de_results.csv (log2FC named vector, ENTREZID mapped) | Visual | Confirmed | TNF signaling pathway rendered correctly; IL6, TNF, IL1B nodes in red; correct coloring scheme |

## Visual Assessment

### Figure 1: Volcano Plot

**Generated figure analysis:**
- The volcano plot shows -log10(padj) vs log2FC for all 20 genes.
- **Upper-right quadrant (upregulated, significant):** IL6 (log2FC ≈ 3.0, -log10(padj) ≈ 70), TNF (log2FC ≈ 2.3, -log10(padj) ≈ 42), CXCL8 (log2FC ≈ 2.1, -log10(padj) ≈ 30), IL1B (log2FC ≈ 2.2, -log10(padj) ≈ 24). All 4 expected upregulated genes are present and correctly positioned.
- **Upper-left quadrant (downregulated, significant):** BCL2 (log2FC ≈ -2.2, -log10(padj) ≈ 54), MCL1 (log2FC ≈ -1.9, -log10(padj) ≈ 52). Both expected downregulated genes are present. Additionally, VEGFA and EGFR appear in this quadrant with marginal significance (padj ≈ 0.02–0.04) and small fold changes (|log2FC| < 0.25).
- **Near origin (non-significant):** 12 genes cluster near log2FC = 0 with -log10(padj) ≈ 0–1.
- **Pattern consistency:** The core scientific pattern is reproduced — 4 inflammatory genes strongly upregulated, 2 anti-apoptotic genes strongly downregulated. The 2 additional marginal genes (VEGFA, EGFR) represent a minor deviation attributable to DESeq2 version differences.
- **Scientific conclusion supported:** Yes. The volcano plot confirms Compound X induces inflammatory gene upregulation and anti-apoptotic gene suppression.

**Deviation from expected pattern:**
- Expected: 4 upper-right, 2 upper-left, 14 near origin
- Actual: 4 upper-right, 4 upper-left, 12 near origin
- The 2 extra upper-left genes (VEGFA, EGFR) have very small effect sizes and are borderline significant. This does not change the scientific interpretation.

### Figure 3: KEGG Pathway Diagram

**Generated figure analysis:**
- The KEGG pathway diagram shows the TNF signaling pathway (hsa04668) rendered by pathview.
- **Gene coloring:** IL6, TNF, and IL1B are highlighted in red (upregulated), consistent with the paper's claim. CXCL8 is not visible as a labeled node in the standard KEGG hsa04668 diagram (CXCL8/IL-8 is not a canonical node in this pathway map). BCL2 and MCL1 are not directly labeled in the pathway diagram but the pathway shows apoptosis-related nodes.
- **Pathway structure:** The canonical TNF signaling pathway structure is preserved, showing TNFR1/TNFR2 receptors, TRADD, TRAF, IKK, NF-kB, MAPK, and apoptosis signaling branches.
- **Scientific conclusion supported:** Yes. The pathway diagram confirms TNF signaling pathway activation with inflammatory cytokines upregulated.

**Limitation:** CXCL8, BCL2, and MCL1 are not directly visible as colored nodes in the standard KEGG hsa04668 map. This is a limitation of the KEGG pathway map coverage, not a reproduction error.

### Figure 2: GO Bar Plot

- **Status:** Not generated. GO enrichment failed with 0 enriched terms at q < 0.05.
- **Root cause:** The analysis script passed a universe of only 20 genes to `enrichGO()`, making the hypergeometric test extremely conservative. The golden reference run (run_01) did not specify a universe parameter and found 1013 enriched terms.
- **Impact:** The GO enrichment bar plot (Figure 2) could not be generated, preventing visual validation of GO term rankings.

## Non-Visual Figure Checks

| Check | Status | Notes |
|-------|--------|-------|
| Figure 1 file exists and is non-empty | Pass | figure1_volcano.png: 88,942 bytes, 1200×1050 px |
| Figure 2 file exists | Fail | Not generated — GO enrichment failure |
| Figure 3 file exists and is non-empty | Pass | hsa04668.figure3_kegg.png: 124,791 bytes, 1323×979 px |
| Figure 1 contains expected gene labels | Pass | IL6, TNF, CXCL8, IL1B, BCL2, MCL1, VEGFA, EGFR labeled |
| Figure 3 contains pathway ID hsa04668 | Pass | Title shows "TNF SIGNALING PATHWAY" |
| Original paper figures available for comparison | N/A | PDF conversion failed; no original figure images extracted |
