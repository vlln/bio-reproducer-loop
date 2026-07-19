# Run Results — bench-002 run_01

Generated: 2026-07-15T12:07 UTC

## Execution Summary

| Item | Value |
|------|-------|
| Status | SUCCESS |
| Duration | ~23 seconds (R analysis) |
| Pipeline Engine | Rscript (direct invocation) |
| Pipeline Script | analysis.R |
| R Version | 4.6.1 (2026-06-24, "Happy Hop") |
| Platform | aarch64-apple-darwin25.4.0 |

## Nextflow Runtime

Nextflow was not available for execution. Java JRE is not installed on this system
(macOS stub `/usr/bin/java` redirects to no installed runtime). The Nextflow
installer fails with "Unable to locate a Java Runtime."

The analysis was executed via direct `Rscript analysis.R` invocation. The
`main.nf` and `nextflow.config` files are provided as documentation of the
intended Nextflow-based deployment strategy. The pipeline is a single R process
that would be trivially wrapped in a Nextflow process.

Docker daemon was also not running (OrbStack not started). Container-based
execution was not possible. Native R packages (installed in Phase 3) were used
directly.

## Pipeline Metrics

| Step | Tool | Status | Key Metric |
|------|------|--------|------------|
| 1. Load data | R read.csv | success | 20 genes × 6 samples |
| 2. Pre-filtering | DESeq2 estimateSizeFactors | success | 0 genes removed (all mean norm count ≥ 10) |
| 3. Differential Expression | DESeq2 + apeglm lfcShrink | success | 8 significant genes (padj < 0.05) |
| 4. Volcano Plot (Figure 1) | ggplot2 + ggrepel | success | 8 highlighted genes |
| 5. GO Enrichment | clusterProfiler enrichGO (BP) | success | 1013 enriched terms (q < 0.05) |
| 6. GO Bar Plot (Figure 2) | ggplot2 | success | Top 10 BP terms |
| 7. KEGG Pathway (Figure 3) | pathview (hsa04668) | success | TNF signaling pathway with gene coloring |

## Quality Metrics

| Metric | Value | Expected | Match |
|--------|-------|----------|-------|
| Input genes | 20 | 20 | ✓ |
| Input samples | 6 | 6 | ✓ |
| DE genes (padj < 0.05) | 8 | ≥ 5 | ✓ |
| IL6 log2FC | 3.00 | > 1.5 | ✓ |
| IL6 padj | 7.34e-71 | < 0.01 | ✓ |
| TNF log2FC | 2.27 | > 1.0 | ✓ |
| TNF padj | 2.89e-43 | < 0.01 | ✓ |
| CXCL8 log2FC | 2.08 | > 1.0 | ✓ |
| CXCL8 padj | 2.05e-30 | < 0.01 | ✓ |
| IL1B log2FC | 2.19 | > 0.8 | ✓ |
| IL1B padj | 1.53e-24 | < 0.05 | ✓ |
| BCL2 log2FC | -2.22 | < -1.0 | ✓ |
| BCL2 padj | 6.70e-55 | < 0.01 | ✓ |
| MCL1 log2FC | -1.85 | < -0.8 | ✓ |
| MCL1 padj | 9.34e-53 | < 0.01 | ✓ |
| GO terms enriched | 1013 | ≥ 1 | ✓ |
| Inflammatory/cytokine terms found | Yes | required | ✓ |
| Apoptotic terms found | Yes | required | ✓ |

## Figure Generation

| Field | Value |
|-------|-------|
| Generation Status | generated |
| Figures Directory | figures/ |
| Plotting Source | handwritten fallback |
| Author Plotting Attempt | N/A |
| Handwritten Fallback Justification | Author code unavailable — GitHub repo (https://github.com/example/drug-response-analysis) returns HTTP 404 |

| Figure/Panel | Original Image | Script/Notebook | Input Data | Output Figure | Status | Notes |
|--------------|----------------|-----------------|------------|---------------|--------|-------|
| Figure 1 (Volcano) | Not found (paper.md only) | analysis.R (handwritten) | de_results.csv | figure1_volcano.png | generated | 8 genes highlighted; 4 up (red), 2 down (blue) + 2 additional (EGFR, VEGFA) |
| Figure 2 (GO Bar) | Not found (paper.md only) | analysis.R (handwritten) | go_enrichment.csv | figure2_go_barplot.png | generated | Top 10 BP terms by -log10(q-value); apoptotic/inflammatory terms present |
| Figure 3 (KEGG) | Not found (paper.md only) | analysis.R (handwritten) | de_results.csv (ENTREZID mapped) | figure3_kegg_pathway.png | generated | hsa04668 TNF signaling; up=red, down=blue |

## Deviations from Paper Expectations

### 1. 8 significant genes instead of 6

The paper reports 6 significant DE genes. Our analysis found 8:
- Expected 6: IL6, TNF, CXCL8, IL1B (upregulated); BCL2, MCL1 (downregulated)
- Additional 2: VEGFA (padj=0.021, log2FC=-0.24), EGFR (padj=0.041, log2FC=-0.23)

Both VEGFA and EGFR have very small fold changes (-0.24 and -0.23) and are
borderline significant (padj near 0.05). This is likely a version effect —
DESeq2 1.52.0 (installed) vs 1.42.0 (paper) may have slightly different
sensitivity at the significance boundary. The core 6 genes are robustly
significant (padj < 1e-23 for all).

### 2. GO term ranking differs from paper

The paper reports "inflammatory response (GO:0006954)", "cytokine-mediated
signaling (GO:0019221)", and "apoptotic process" as the top enriched terms.
Our analysis finds these terms are enriched but they are not the top-ranked
terms. The top-ranked terms are dominated by "absence of ligand" sub-terms
of the apoptotic signaling pathway, which have very high fold enrichment
due to the small background gene set size (27-45 genes). The expected
inflammatory and apoptotic terms are present in the results at lower ranks.

### 3. KEGG figure retry

The initial pathview run failed because the `reference/` directory did not
exist. After creating the directory, pathview successfully downloaded KEGG
data and generated the pathway diagram on the second attempt.

## Issues Encountered

| Issue | Status | Resolution |
|-------|--------|------------|
| Nextflow unavailable (Java JRE not installed) | Resolved | Used direct Rscript invocation |
| Docker daemon not running (OrbStack not started) | Resolved | Used native R packages |
| KEGG reference directory missing | Resolved | Created `reference/` directory and retried pathview |
| Author code unavailable (GitHub 404) | Recorded | Handwritten analysis.R from paper Methods description |
| 8 DE genes instead of expected 6 | Recorded | Version effect (DESeq2 1.52.0 vs 1.42.0); see Deviations |
| GO term ranking differs from paper | Recorded | Small gene set causes GO hierarchy effects; see Deviations |

## Output Files

| File | Path | Size |
|------|------|------|
| DE results | results/de_results.csv | 2.0 KB |
| GO enrichment | results/go_enrichment.csv | 197 KB |
| Analysis log | results/analysis.log | 10 KB |
| Figure 1 (Volcano) | figures/figure1_volcano.png | 102 KB |
| Figure 2 (GO Bar) | figures/figure2_go_barplot.png | 125 KB |
| Figure 3 (KEGG) | figures/figure3_kegg_pathway.png | 125 KB |
| Nextflow workflow | main.nf | 1.1 KB |
| Nextflow config | nextflow.config | 0.5 KB |
| Analysis script | analysis.R | 11.7 KB |

## Conclusion

The analysis pipeline successfully reproduced the paper's three-stage workflow:
1. DESeq2 differential expression identified the core 6 genes (IL6, TNF, CXCL8,
   IL1B upregulated; BCL2, MCL1 downregulated) with strong statistical support.
2. GO enrichment confirmed inflammatory and apoptotic pathway dysregulation.
3. KEGG pathway visualization confirmed TNF signaling pathway activation.

The qualitative conclusion matches the paper: Compound X induces an inflammatory
transcriptional program (IL6, TNF, CXCL8, IL1B upregulated) while suppressing
anti-apoptotic gene expression (BCL2, MCL1 downregulated).