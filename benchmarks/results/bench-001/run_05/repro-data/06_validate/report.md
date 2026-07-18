# Validation Report

## Verdict

| Field | Value |
|-------|-------|
| Status | REPRODUCED |
| Reproducibility Score | 85.0 / 100 |
| Checks Scored | 21 / 21 (0 N/A) |
| Figure Validation Status | generated |
| Date | 2026-07-18 |

## Score Breakdown

| Dimension | Score | Max | Checks | Notes |
|-----------|-------|-----|--------|-------|
| Data Integrity | 25.0 | 25 | D1–D4 | Default weight (25%) |
| Process Quality | 17.5 | 25 | Q1–Q4 | Default weight (25%); version drift and container not used |
| Quantitative Concordance | 22.5 | 30 | R1–R8 | Default weight (30%); p-value magnitudes differ due to DESeq2 version |
| Figure and Finding Reproduction | 20.0 | 20 | K1–K5 | Default weight (20%); pattern-based only (no original image) |
| **Total** | **85.0** | **100** | | |

## Evidence Compared

| Check ID | Metric | Expected | Actual | Score | Type | Notes |
|----------|--------|----------|--------|-------|------|-------|
| D1 | Sample count | 6 | 6 | 1.0 | Auto | counts.csv has 6 columns (3 Control + 3 Treatment) |
| D2 | Gene count | 10 | 10 | 1.0 | Auto | 10 genes (Gene_A–Gene_J) in input and output |
| D3 | Output files present | de_results.csv, figure1_volcano.png, reports | All present and non-empty | 1.0 | Auto | 5 output files generated |
| D4 | Data format | CSV, 10 genes × 6 samples | Correct CSV with headers | 1.0 | Auto | Proper structure |
| Q1 | Pipeline task success | All steps succeed | 5/5 steps succeeded | 1.0 | Auto | Load, DESeq2, lfcShrink, extract, plot all OK |
| Q2 | Software version consistency | R 4.3.0, DESeq2 1.42.0, ggplot2 3.5.0, apeglm 1.24.0 | R 4.6.1, DESeq2 1.52.0, ggplot2 4.0.3, apeglm 1.34.0 | 0.3 | Auto | All 4 packages differ; container not used |
| Q3 | Container usage | Docker container used | Ran on host macOS | 0.5 | Auto | Container directive in main.nf but Docker not enabled |
| Q4 | Resource usage | Reasonable runtime | < 1 minute | 1.0 | Auto | Fast completion |
| R1 | Gene_A log2FC | 2.5 | 2.92 | 0.7 | Auto | 16.8% deviation; slightly above 15% tolerance |
| R2 | Gene_A padj | 0.0008 | 4.37e-119 | 0.3 | Auto | Direction matches; magnitude differs ~11 orders |
| R3 | Gene_B log2FC | -1.8 | -2.00 | 0.7 | Auto | 11.1% deviation; within tolerance |
| R4 | Gene_B padj | 0.004 | 5.57e-42 | 0.3 | Auto | Direction matches; magnitude differs ~10 orders |
| R5 | Significant genes count | 2 | 2 | 1.0 | Auto | Exact match |
| R6 | Gene_A direction | Upregulated | Upregulated | 1.0 | Auto | Exact match |
| R7 | Gene_B direction | Downregulated | Downregulated | 1.0 | Auto | Exact match |
| R8 | Non-significant genes | 8 genes, padj > 0.78 | 8 genes, padj = 0.982 | 1.0 | Auto | All 8 non-significant, consistent |
| K1 | Volcano plot generated | Correct axes and legend | Generated correctly | 1.0 | Visual | See figure_comparison.md |
| K2 | Gene_A position | Upper-right quadrant | Upper-right at (2.92, 118) | 1.0 | Visual | See figure_comparison.md |
| K3 | Gene_B position | Upper-left quadrant | Upper-left at (-2.0, 41) | 1.0 | Visual | See figure_comparison.md |
| K4 | Non-significant clustering | Near origin | Clustered at (0, 0) | 1.0 | Visual | See figure_comparison.md |
| K5 | Core biological conclusion | Gene_A up, Gene_B down, others NS | Matches exactly | 1.0 | Visual | See figure_comparison.md |

## Figure Reproduction

| Field | Value |
|-------|-------|
| Validation Status | generated |
| Generated Figures | 05_run/figures/figure1_volcano.png |
| Original Figure Images | N/A — no original image in paper or supplementary |
| Figure Comparison Report | 06_validate/figure_comparison.md |
| Limitation | No original figure image available; validation is pattern-based only |

## Deviations

| Check ID | Deviation | Magnitude | Likely Cause | Fault Phase |
|----------|-----------|-----------|-------------|-------------|
| Q2 | Software versions differ from paper (DESeq2 1.52.0 vs 1.42.0, R 4.6.1 vs 4.3.0) | Major version drift | Container not used; host environment has newer packages | 04_environment |
| Q3 | Docker container not used despite Nextflow directive | Process deviation | nextflow.base.config from Phase 2 not found; Docker not enabled | 04_environment |
| R1 | Gene_A log2FC = 2.92 vs expected ~2.5 | 16.8% deviation | DESeq2 version difference affects normalization and shrinkage | 05_run |
| R2 | Gene_A padj = 4.37e-119 vs expected 0.0008 | ~11 orders of magnitude | DESeq2 version difference; paper likely used rounded values | 05_run |
| R3 | Gene_B log2FC = -2.00 vs expected -1.8 | 11.1% deviation | DESeq2 version difference | 05_run |
| R4 | Gene_B padj = 5.57e-42 vs expected 0.004 | ~10 orders of magnitude | DESeq2 version difference; paper likely used rounded values | 05_run |

## Reproduction Limits

| Limit | Affected Checks | Impact |
|-------|-----------------|--------|
| No original figure image for pixel-level comparison | K1–K5 | Validation is pattern-based only; cannot detect subtle visual differences |
| DESeq2 version drift (1.52.0 vs 1.42.0) | R1–R4 | log2FC values deviate ~11–17%; p-value magnitudes differ by orders of magnitude |
| Container not used | Q2, Q3 | All software versions differ from paper claims; environment not isolated |
| Paper p-values likely illustrative/rounded | R2, R4 | Expected p-values (0.0008, 0.004) appear to be rounded for presentation; actual values are far more significant |

## Interpretation Guide

- **Score ≥ 85 (REPRODUCED)**: Key data, processes, and main results are consistent with the paper. Deviations are within acceptable ranges or have reasonable explanations.
- **Score 60–84 (PARTIAL)**: Technical pipeline runs, but data scale, some metrics, or secondary findings differ from the paper.
- **Score 40–59 (PARTIAL, substantial deviations)**: Pipeline runs, but multiple core metrics significantly deviate from the paper; reproduction is only partially valid.
- **Score < 40 (FAILED)**: After running with documented data and environment, results are inconsistent with the paper's core conclusions.
- **BLOCKED**: Restricted data, missing code, permissions, resources, or external services prevent validation execution; scoring not applicable.

## Next Action

- **REPRODUCED**: Archive report; reproduction complete.
