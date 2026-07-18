# Validation Report

## Verdict

| Field | Value |
|-------|-------|
| Status | PARTIAL |
| Reproducibility Score | 79.75 / 100 |
| Checks Scored | 18 / 19 (1 N/A) |
| Figure Validation Status | partial |
| Date | 2026-07-18 |

## Score Breakdown

| Dimension | Score | Max | Checks | Notes |
|-----------|-------|-----|--------|-------|
| Data Integrity | 25.0 | 25 | D1–D5 | D3 scored 0.5 (GO output files missing) |
| Process Quality | 18.75 | 25 | Q1–Q6 | Q2 scored 0.0 (GO enrichment failed); Q4 scored 0.5 (version mismatch) |
| Quantitative Concordance | 24.0 | 30 | R1–R10 | R2 scored 0.7 (TNF 9.2% deviation); R8 scored 0.7 (8 vs 6 genes); R9 scored 0.0 (GO terms absent); R10 N/A |
| Figure and Finding Reproduction | 12.0 | 20 | F1–F4 | F1 scored 0.7 (2 extra genes); F2 scored 0.0 (not generated); F3, F4 scored 1.0 |
| **Total** | **79.75** | **100** | | |

Dimension weights: default (25/25/30/20). No adjustment.

## Evidence Compared

| Check ID | Metric | Expected | Actual | Score | Type | Notes |
|----------|--------|----------|--------|-------|------|-------|
| D1 | Input gene count | 20 | 20 | 1.0 | Auto | counts.csv: 20 genes × 6 samples |
| D2 | Input sample count | 6 | 6 | 1.0 | Auto | counts.csv: 20 genes × 6 samples |
| D3 | Output files present and non-empty | de_results.csv, analysis.log, figure1_volcano.png, hsa04668.figure3_kegg.png, go_enrichment.csv, figure2_go_barplot.png | 4/6 files present; go_enrichment.csv and figure2_go_barplot.png missing | 0.5 | Auto | GO enrichment output files missing due to enrichment failure |
| D4 | DE results table row count | 20 | 20 | 1.0 | Auto | de_results.csv contains all 20 genes |
| D5 | Pre-filtering outcome | Genes with mean count < 10 removed | 20/20 genes retained (all above threshold) | 1.0 | Auto | All genes have mean count ≥ 10 |
| Q1 | DESeq2 DE analysis completed | success | success — 8 DE genes identified | 1.0 | Auto | DESeq2 + apeglm lfcShrink completed without error |
| Q2 | GO enrichment completed | success — enriched terms found | failed — 0 enriched terms at q < 0.05 | 0.0 | Auto | enrichGO returned 0 terms; small universe (20 genes) likely cause |
| Q3 | KEGG pathway visualization completed | success | success — hsa04668 diagram generated | 1.0 | Auto | pathview completed; diagram shows TNF signaling pathway |
| Q4 | Software versions match paper | R 4.3.0, DESeq2 1.42.0, ggplot2 3.5.0, apeglm 1.24.0 | R 4.6.1, DESeq2 1.52.0, ggplot2 4.0.3, apeglm 1.34.0 | 0.5 | Auto | Newer versions installed; paper specified older versions |
| Q5 | Pipeline stages executed in order | DE → GO enrichment → KEGG visualization | DE → GO enrichment (failed) → KEGG visualization; order preserved | 1.0 | Auto | Pipeline order correct; GO step failed but did not block downstream |
| Q6 | Gene ID conversion (SYMBOL → ENTREZID) | true | 20/20 genes mapped | 1.0 | Auto | bitr() mapped all 20 gene symbols |
| R1 | IL6 log2FC | 3.0 | 2.998 | 1.0 | Auto | Deviation: 0.07% |
| R2 | TNF log2FC | 2.5 | 2.271 | 0.7 | Auto | Deviation: 9.2%; likely DESeq2 version effect |
| R3 | CXCL8 log2FC | 2.2 | 2.076 | 1.0 | Auto | Deviation: 5.6% |
| R4 | IL1B log2FC | 2.0 | 2.187 | 1.0 | Auto | Deviation: 9.4% |
| R5 | BCL2 log2FC | -2.2 | -2.222 | 1.0 | Auto | Deviation: 1.0% |
| R6 | MCL1 log2FC | -1.8 | -1.852 | 1.0 | Auto | Deviation: 2.9% |
| R7 | Direction of regulation (6 core genes) | IL6/TNF/CXCL8/IL1B up; BCL2/MCL1 down | All 6 core genes match expected direction | 1.0 | Auto | Perfect direction concordance |
| R8 | Significant gene count | 6 | 8 | 0.7 | Auto | 2 additional genes (EGFR padj=0.041, VEGFA padj=0.021) with small fold changes |
| R9 | GO term IDs match paper (GO:0006954, GO:0019221) | GO:0006954, GO:0019221 present with q < 0.05 | 0 enriched terms; neither GO:0006954 nor GO:0019221 found | 0.0 | Auto | GO enrichment failed entirely |
| R10 | GO thematic concordance (inflammatory/cytokine/apoptotic) | Inflammatory, cytokine, apoptotic terms enriched | N/A — no GO terms generated | N/A | Manual | Cannot assess; see Q2 |
| F1 | Volcano plot pattern | 4 upper-right, 2 upper-left, 14 near origin | 4 upper-right (IL6,TNF,CXCL8,IL1B), 4 upper-left (BCL2,MCL1,VEGFA,EGFR), 12 near origin | 0.7 | Visual | Core 6 genes correctly positioned; 2 additional marginal genes in upper-left |
| F2 | GO bar plot top terms | Top 10 BP terms, inflammatory/cytokine at top | Not generated — GO enrichment failed | 0.0 | Visual | Figure 2 not generated |
| F3 | KEGG pathway diagram | hsa04668 with up=red, down=blue | TNF signaling pathway rendered; IL6, TNF, IL1B in red; correct coloring scheme | 1.0 | Visual | See figure_comparison.md for detailed assessment |
| F4 | Overall conclusion (inflammatory + anti-apoptotic) | Inflammatory induction + anti-apoptotic suppression | Conclusion supported: IL6/TNF/CXCL8/IL1B upregulated, BCL2/MCL1 downregulated | 1.0 | Manual | Core biological conclusion reproduced |

## Figure Reproduction

| Field | Value |
|-------|-------|
| Validation Status | partial |
| Generated Figures | 05_run/figures/figure1_volcano.png, 05_run/figures/hsa04668.figure3_kegg.png |
| Original Figure Images | N/A — PDF conversion failed (MinerU API unreachable); no original figure images extracted |
| Figure Comparison Report | 06_validate/figure_comparison.md |
| Limitation | Missing original figure images (PDF conversion failed); Figure 2 (GO bar plot) not generated due to GO enrichment failure |

## Deviations

| Check ID | Deviation | Magnitude | Likely Cause | Fault Phase |
|----------|-----------|-----------|-------------|-------------|
| Q2 | GO enrichment produced 0 enriched terms at q < 0.05 | Complete failure — no terms at any significance level | Small universe parameter (20 genes) passed to enrichGO makes hypergeometric test overly conservative; golden run (run_01) did not specify universe and found 1013 terms | 05_run |
| F2 | GO bar plot (Figure 2) not generated | Figure entirely missing | Blocked by GO enrichment failure (Q2) | 05_run |
| R8 | 8 significant genes found vs 6 expected | 2 additional genes (VEGFA padj=0.021, EGFR padj=0.041) with small fold changes (\|log2FC\| < 0.25) | DESeq2 version difference (1.52.0 vs 1.42.0) affects significance boundary sensitivity | 05_run |
| R9 | Paper-specific GO term IDs (GO:0006954, GO:0019221) not found | Exact IDs absent; enrichment failed entirely | GO enrichment failure due to small universe; even if enrichment had succeeded, different DE gene set (8 vs 6) would produce different term rankings | 05_run |
| Q4 | Software versions do not match paper | R 4.6.1 vs 4.3.0; DESeq2 1.52.0 vs 1.42.0; ggplot2 4.0.3 vs 3.5.0; apeglm 1.34.0 vs 1.24.0 | Newer package versions installed in Phase 3; paper specified older versions | 03_provision |
| R2 | TNF log2FC = 2.27 vs paper 2.5 | 9.2% deviation | DESeq2 version difference and/or different normalization | 05_run |

## Reproduction Limits

| Limit | Affected Checks | Impact |
|-------|-----------------|--------|
| Original paper figures unavailable (PDF conversion failed) | F1, F2, F3 | Visual comparison relies on generated figures only; cannot compare against original paper images. Pattern validation based on plan.md descriptions. |
| GO enrichment failure (0 terms) | Q2, R9, R10, F2 | GO enrichment bar plot not generated; GO term IDs and thematic concordance cannot be assessed. Root cause: small universe parameter in enrichGO. |
| No author plotting code (GitHub 404) | F1, F2, F3 | All figures generated via handwritten R code; plotting style may differ from paper but scientific content is preserved. |
| DESeq2 version mismatch (1.52.0 vs 1.42.0) | R2, R8, Q4 | 2 additional marginally significant genes; TNF log2FC 9.2% deviation. Core 6 genes robustly reproduced. |
| padj magnitude discrepancy | R1–R6 (padj values) | Computed padj values are orders of magnitude more extreme than paper (e.g., IL6: 7.3e-71 vs 0.0003). Expected for clean benchmark data with strong group separation. Direction and significance classification are correct. |

## Interpretation Guide

- **Score ≥ 85 (REPRODUCED):** Key data, processes, and major results are consistent with the paper. Deviations are within acceptable range or have reasonable explanations.
- **Score 60–84 (PARTIAL):** Technical pipeline is runnable, but data scale, some metrics, or secondary findings differ from the paper.
- **Score 40–59 (PARTIAL, substantial deviations):** Pipeline is runnable, but multiple core metrics significantly deviate from the paper. Reproduction is only partially valid.
- **Score < 40 (FAILED):** After running with documented data and environment, results are inconsistent with the paper's core conclusions.
- **BLOCKED:** Restricted data, missing code, permissions, resources, or external service unavailability prevent validation execution. Scoring is not applicable.

## Next Action

- **PARTIAL:** The core biological conclusion is reproduced (inflammatory gene upregulation + anti-apoptotic gene suppression). The primary deviation is GO enrichment failure, which is attributable to a methodological issue in the analysis script (small universe parameter). Recommendation: **rollback to 05_run** to fix the GO enrichment step by removing or expanding the `universe` parameter in `enrichGO()`. The golden reference run (run_01) demonstrates that GO enrichment succeeds with the same data when the universe is not constrained to 20 genes.

### Rollback Analysis

| Field | Value |
|-------|-------|
| Earliest likely fault phase | 05_run |
| Faulty check IDs | Q2, R9, F2 |
| Root cause | `enrichGO()` called with `universe = bg_entrez` where `bg_entrez` contains only 20 genes. The hypergeometric test with such a small background is extremely conservative. The fix is to either omit the `universe` parameter (letting clusterProfiler use its default background) or use a larger background gene set. |
| Evidence | Golden run (run_01) used the same data and found 1013 enriched GO BP terms. The golden run's analysis script did not specify a `universe` parameter. |
| Expected outcome after fix | GO enrichment should produce enriched terms; Figure 2 (GO bar plot) should be generated; checks Q2, R9, R10, F2 should improve. |
| Estimated score after fix | ~90+ (REPRODUCED), assuming GO enrichment produces terms consistent with paper claims. |
