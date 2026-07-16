# Validation Report

## Verdict

| Field | Value |
|-------|-------|
| Status | PARTIAL |
| Reproducibility Score | 63.0 / 100 |
| Checks Scored | 17 / 17 (0 N/A) |
| Figure Validation Status | generated |
| Date | 2026-07-16 |

## Score Breakdown

| Dimension | Score | Max | Checks | Notes |
|-----------|-------|-----|--------|-------|
| Data Integrity | 25.0 | 25.0 | D1–D4 | All 4 checks passed. Gene count, sample count, output files, and table structure all match. |
| Process Quality | 18.75 | 25.0 | Q1–Q4 | Pipeline succeeded (Q1=1.0), DESeq2 version matches (Q2=1.0). R version differs by minor release (Q3=0.7), ggplot2 differs by major version (Q4=0.5). Both version differences come from the bioconductor_docker:RELEASE_3_18 container. |
| Quantitative Concordance | 18.0 | 30.0 | R1–R8 | Directions correct (R1, R2 = 1.0), significant count correct (R3 = 1.0), non-DE genes correct (R8 = 1.0). log2FC magnitudes moderately deviate (R4, R5 = 0.7 each). padj magnitudes severely deviate (R6, R7 = 0.3 each) — paper values appear idealized/synthetic. |
| Figure and Finding Reproduction | 20.0 | 20.0 | K1–K5 | All 5 checks passed. Volcano plot generated with correct pattern. Gene_A upper-right, Gene_B upper-left, others near origin. Core biological conclusions fully reproduced. |
| **Total** | **63.0** | **100** | | |

No dimension weight adjustments were made. Default weights (25/25/30/20) were used.

## Evidence Compared

| Check ID | Metric | Expected | Actual | Score | Type | Notes |
|----------|--------|----------|--------|-------|------|-------|
| D1 | Gene count | 10 genes (Gene_A–Gene_J) | 10 genes | 1.0 | Auto | Exact match |
| D2 | Sample count | 6 samples | 6 samples | 1.0 | Auto | Exact match |
| D3 | Output files | 4 files present | 4 files present | 1.0 | Auto | All non-empty |
| D4 | Results structure | 7 columns | 7 columns | 1.0 | Auto | Exact match |
| Q1 | Process success | 2/2 | 2/2 | 1.0 | Auto | Both exited 0 |
| Q2 | DESeq2 version | 1.42.0 | 1.42.1 | 1.0 | Auto | Patch-level difference |
| Q3 | R version | 4.3.0 | 4.4.0 | 0.7 | Auto | Minor version difference |
| Q4 | ggplot2 version | 3.5.0 | 4.0.3 | 0.5 | Auto | Major version difference |
| R1 | Gene_A log2FC direction | Positive | +2.92 | 1.0 | Auto | Direction matches |
| R2 | Gene_B log2FC direction | Negative | -2.00 | 1.0 | Auto | Direction matches |
| R3 | Significant gene count | 2 | 2 | 1.0 | Auto | Exact match |
| R4 | Gene_A log2FC magnitude | 2.5 | 2.92 | 0.7 | Auto | +16.8% deviation |
| R5 | Gene_B log2FC magnitude | -1.8 | -2.00 | 0.7 | Auto | -11.1% deviation |
| R6 | Gene_A padj magnitude | 0.0008 | 4.37e-119 | 0.3 | Auto | Orders of magnitude difference |
| R7 | Gene_B padj magnitude | 0.004 | 5.57e-42 | 0.3 | Auto | Orders of magnitude difference |
| R8 | Non-DE genes padj > 0.05 | 8 genes | 8 genes | 1.0 | Auto | Exact match |
| K1 | Volcano plot generated | Yes | Yes | 1.0 | Auto | PNG + PDF |
| K2 | Gene_A position | Upper-right | Upper-right | 1.0 | Visual | See figure_comparison.md |
| K3 | Gene_B position | Upper-left | Upper-left | 1.0 | Visual | See figure_comparison.md |
| K4 | Non-DE genes near origin | Yes | Yes | 1.0 | Visual | See figure_comparison.md |
| K5 | Core biological conclusion | Gene_A up, Gene_B down | Confirmed | 1.0 | Manual | Fully consistent |

## Figure Reproduction

| Field | Value |
|-------|-------|
| Validation Status | generated |
| Generated Figures | 05_run/figures/volcano_plot.png, volcano_plot.pdf |
| Original Figure Images | N/A (not provided in paper) |
| Figure Comparison Report | 06_validate/figure_comparison.md |
| Limitation | Missing original figure — pattern-based validation only |

## Deviations

| Check ID | Deviation | Magnitude | Likely Cause | Fault Phase |
|----------|-----------|-----------|-------------|-------------|
| R4 | Gene_A log2FC = 2.92 vs paper 2.5 | Moderate (+16.8%) | Paper uses idealized values; actual DESeq2 on count data differs | Paper |
| R5 | Gene_B log2FC = -2.00 vs paper -1.8 | Moderate (-11.1%) | Same as R4 | Paper |
| R6 | Gene_A padj = 4.37e-119 vs paper 0.0008 | Severe (orders of magnitude) | Paper uses idealized p-values; actual data produces extreme significance | Paper |
| R7 | Gene_B padj = 5.57e-42 vs paper 0.004 | Severe (orders of magnitude) | Same as R6 | Paper |
| Q3 | R version 4.4.0 vs paper 4.3.0 | Minor | bioconductor_docker:RELEASE_3_18 ships R 4.4.0 | Provision |
| Q4 | ggplot2 version 4.0.3 vs paper 3.5.0 | Moderate | bioconductor_docker:RELEASE_3_18 ships ggplot2 4.0.3 | Provision |

## Reproduction Limits

| Limit | Affected Checks | Impact |
|-------|-----------------|--------|
| No original figure image provided | K1–K4 (visual) | Pixel-level comparison not possible; validated via pattern matching against textual description |
| Paper uses idealized/synthetic numerical values | R4–R7 | log2FC and padj magnitudes differ significantly from paper claims, but directions and significance calls are fully consistent |
| Software version differences (R, ggplot2) | Q3, Q4 | Minor impact on numerical results; DESeq2 version matches at patch level |
| GitHub analysis script unavailable (404) | All | Analysis reconstructed from Methods; no way to verify exact implementation details |

## Interpretation Guide

- **Score ≥ 85 (REPRODUCED)**: Key data, processes, and major results are consistent with the paper. Deviations are within acceptable range or have reasonable explanations.
- **Score 60–84 (PARTIAL)**: Technical pipeline runs successfully, but data scale, some metrics, or secondary findings differ from the paper.
- **Score 40–59 (PARTIAL, substantial deviations)**: Pipeline runs, but multiple core metrics significantly deviate from the paper. Reproduction is only partially valid.
- **Score < 40 (FAILED)**: After running with documented data and environment, results are inconsistent with the paper's core conclusions.
- **BLOCKED**: Restricted data, missing code, permissions, resources, or external services prevent validation execution. Scoring does not apply.

## Next Action

- **PARTIAL**: Record deviation causes; no rollback needed. The numerical discrepancies (R4–R7) originate from the paper itself using idealized/synthetic values rather than actual DESeq2 output. The reproduction correctly implements the described analysis on the provided count data. The core biological conclusions (Gene_A upregulated, Gene_B downregulated, 8 genes not significant) are fully reproduced. The volcano plot pattern matches the paper description. Recommend archiving the report.
