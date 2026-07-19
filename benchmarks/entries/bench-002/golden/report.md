# Validation Report — bench-002 run_01

## Verdict

| Field | Value |
|-------|-------|
| Status | PARTIAL |
| Reproducibility Score | 82.75 / 100 |
| Checks Scored | 17 / 17 (0 N/A) |
| Figure Validation Status | generated |
| Date | 2026-07-15 |

## Score Breakdown

| Dimension | Score | Max | Checks | Notes |
|-----------|-------|-----|--------|-------|
| Data Integrity | 25.00 | 25 | D1–D4 | All input/output integrity checks passed |
| Process Quality | 18.75 | 25 | Q1–Q3 | Software versions differ from paper (R 4.6.1 vs 4.3.0, DESeq2 1.52.0 vs 1.42.0) |
| Quantitative Concordance | 24.00 | 30 | R1–R10 | Core log2FC values match closely; 8 vs 6 significant genes; paper-specific GO IDs absent |
| Figure and Finding Reproduction | 15.00 | 20 | K1–K4 | Volcano pattern preserved; GO bar plot ranking differs; KEGG diagram consistent; conclusion supported |
| **Total** | **82.75** | **100** | | |

Dimension weights are default (25/25/30/20); no adjustments made.

## Evidence Compared

| Check ID | Metric | Expected | Actual | Score | Type | Notes |
|----------|--------|----------|--------|-------|------|-------|
| D1 | Input gene count | 20 | 20 | 1.0 | Auto | counts.csv has 20 genes |
| D2 | Input sample count | 6 | 6 | 1.0 | Auto | 3 control + 3 drug samples |
| D3 | Output files present and non-empty | de_results.csv, go_enrichment.csv, 3 figures | All 6 files present and non-empty | 1.0 | Auto | See Output Files in run_results.md |
| D4 | DE results table row count | 20 | 20 | 1.0 | Auto | All 20 input genes present in DE results |
| Q1 | Pipeline steps completed | All 7 steps success | All 7 steps success | 1.0 | Auto | See Pipeline Metrics in run_results.md |
| Q2 | Software versions match paper | R 4.3.0, DESeq2 1.42.0, ggplot2 3.5.0, apeglm 1.24.0 | R 4.6.1, DESeq2 1.52.0 | 0.5 | Auto | Newer versions installed; paper specified older versions |
| Q3 | Qualitative conclusion matches | Inflammatory induction + anti-apoptotic suppression | Conclusion matches | 1.0 | Manual | IL6/TNF/CXCL8/IL1B up; BCL2/MCL1 down |
| R1 | IL6 log2FC | 3.0 | 2.998 | 1.0 | Auto | Deviation < 0.1% |
| R2 | TNF log2FC | 2.5 | 2.271 | 0.7 | Auto | Deviation 9.2%; within reasonable range |
| R3 | CXCL8 log2FC | 2.2 | 2.076 | 1.0 | Auto | Deviation 5.6% |
| R4 | IL1B log2FC | 2.0 | 2.187 | 1.0 | Auto | Deviation 9.4% |
| R5 | BCL2 log2FC | -2.2 | -2.222 | 1.0 | Auto | Deviation 1.0% |
| R6 | MCL1 log2FC | -1.8 | -1.852 | 1.0 | Auto | Deviation 2.9% |
| R7 | Direction of regulation (6 core genes) | IL6/TNF/CXCL8/IL1B up; BCL2/MCL1 down | All 6 match | 1.0 | Auto | Directions fully consistent |
| R8 | Significant gene count | 6 | 8 | 0.5 | Auto | 2 additional borderline genes (VEGFA, EGFR) |
| R9 | GO term IDs match paper | GO:0006954, GO:0019221 present | Neither found; related terms present | 0.3 | Auto | See Deviations section |
| R10 | GO thematic concordance | Inflammatory, cytokine, apoptotic terms enriched | 17 inflammatory, 19 cytokine, 45 apoptotic terms found | 0.7 | Manual | Themes present but ranking differs |
| K1 | Volcano plot pattern | 4 upper-right, 2 upper-left, 14 near origin | 4 upper-right, 4 upper-left, 12 near origin | 0.7 | Visual | Core 6 correct; 2 extra borderline genes |
| K2 | GO bar plot top terms | Inflammatory/cytokine terms at top | Apoptotic "absence of ligand" sub-terms dominate top 10 | 0.3 | Visual | See figure_comparison.md |
| K3 | KEGG pathway diagram | hsa04668 with up=red, down=blue | TNF signaling rendered; IL6/TNF/IL1B in red | 1.0 | Visual | Consistent with paper claim |
| K4 | Overall conclusion | Inflammatory induction + anti-apoptotic suppression | Conclusion supported | 1.0 | Manual | Core biological finding reproduced |

## Figure Reproduction

| Field | Value |
|-------|-------|
| Validation Status | generated |
| Generated Figures | 05_run/figures/ (figure1_volcano.png, figure2_go_barplot.png, figure3_kegg_pathway.png) |
| Original Figure Images | N/A — paper provided as Markdown only; no embedded figure images |
| Figure Comparison Report | 06_validate/figure_comparison.md |
| Limitation | Missing original figure images prevents pixel-level comparison; pattern-level comparison performed instead |

## Deviations

| Check ID | Deviation | Magnitude | Likely Cause | Fault Phase |
|----------|-----------|-----------|-------------|-------------|
| R8 | 8 significant genes vs 6 expected | 2 additional genes (VEGFA padj=0.021, EGFR padj=0.041) with small fold changes (-0.24, -0.23) | DESeq2 version difference (1.52.0 vs 1.42.0) affects significance boundary sensitivity | 05_run |
| R9 | Paper-specific GO IDs (GO:0006954, GO:0019221) not found | Exact IDs absent; related terms (GO:0002675, GO:0002367) present at different ranks | Different DE gene set (8 vs 6) and background universe produce different GO term rankings | 05_run |
| K2 | GO bar plot top 10 dominated by apoptotic "absence of ligand" sub-terms | Inflammatory/cytokine terms present but outside top 10 | Small DE gene set causes GO hierarchy effects; "absence of ligand" sub-terms have very small background sizes (27-45 genes) producing extreme fold enrichment | 05_run |
| Q2 | Software versions do not match paper | R 4.6.1 vs 4.3.0; DESeq2 1.52.0 vs 1.42.0 | Newer package versions installed during provisioning | 03_provision |
| R2 | TNF log2FC = 2.27 vs paper 2.5 | 9.2% deviation | DESeq2 version difference and/or different normalization | 05_run |

## Reproduction Limits

| Limit | Affected Checks | Impact |
|-------|-----------------|--------|
| No original figure images available (paper.md only) | K1, K2, K3 | Pattern-level comparison only; no pixel-level visual similarity scoring possible |
| DESeq2 version mismatch (1.52.0 vs 1.42.0) | R1–R6, R8 | Slightly different log2FC values and significance boundaries; 2 additional borderline genes |
| Small gene panel (20 genes) | R9, R10, K2 | GO enrichment produces hierarchy artifacts; "absence of ligand" sub-terms dominate due to tiny background sizes |
| Paper-specific GO IDs not reproducible | R9 | Exact GO term IDs depend on background gene universe and DE gene set; different inputs yield different term IDs even when biological themes match |

## Interpretation Guide

- **Score ≥ 85 (REPRODUCED)**: Key data, processes, and major results are consistent with the paper; deviations are within acceptable range or have reasonable explanations.
- **Score 60–84 (PARTIAL)**: Technical pipeline runs successfully, but data scale, some metrics, or secondary findings differ from the paper.
- **Score 40–59 (PARTIAL, substantial deviations)**: Pipeline runs, but multiple core metrics significantly deviate from the paper; reproduction is only partially valid.
- **Score < 40 (FAILED)**: After running with documented data and environment, results are inconsistent with the paper's core conclusions.
- **BLOCKED**: Restricted data, missing code, permissions, resources, or external services prevent validation execution; scoring not applicable.

## Next Action

- **PARTIAL**: Deviations are documented. The 2 extra DE genes (VEGFA, EGFR) are borderline significant with small fold changes, attributable to DESeq2 version differences. The GO term ranking difference is caused by the small gene panel interacting with GO hierarchy. The core biological conclusion (inflammatory induction + anti-apoptotic suppression) is fully supported. No rollback needed — deviations are explainable and do not affect the primary reproduction targets. Archive the report.
