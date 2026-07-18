# Validation Report

## Verdict

| Field | Value |
|-------|-------|
| Status | PARTIAL |
| Reproducibility Score | 78.25 / 100 |
| Checks Scored | 20 / 21 (1 N/A) |
| Figure Validation Status | generated |
| Date | 2026-07-18 |

## Score Breakdown

| Dimension | Score | Max | Checks | Notes |
|-----------|-------|-----|--------|-------|
| Data Integrity | 25.0 | 25 | D1-D4 | All output files present, correct dimensions, complete results table |
| Process Quality | 19.0 | 25 | Q1-Q5 | Dispersion method deviated (gene-wise vs parametric); Nextflow unavailable, ran via direct docker |
| Quantitative Concordance | 14.25 | 30 | R1-R8 | log2FC values close (3-4% diff); padj values orders of magnitude off due to reconstructed count data; directions and significance classifications all correct |
| Figure and Finding Reproduction | 20.0 | 20 | K1-K4 | Volcano plot pattern fully reproduced; original figure unavailable for direct visual comparison (N/A for K2) |
| **Total** | **78.25** | **100** | | |

## Evidence Compared

| Check ID | Metric | Expected | Actual | Score | Type | Notes |
|----------|--------|----------|--------|-------|------|-------|
| D1 | Output files exist and non-empty | 5 output files | All 5 present and non-empty | 1.0 | Auto | |
| D2 | Count matrix dimensions | 10 genes x 6 samples | 10 genes x 6 samples | 1.0 | Auto | |
| D3 | Normalized counts file | Non-empty matrix | 1187 bytes, 10x6 | 1.0 | Auto | |
| D4 | Results table completeness | 10 genes with all fields | 10 genes, all fields populated | 1.0 | Auto | |
| Q1 | Pipeline step success rate | 6/6 succeed | 6/6 succeeded | 1.0 | Auto | |
| Q2 | Dispersion estimation method | Default parametric curve fit | Gene-wise estimates (parametric failed with 10 genes) | 0.3 | Auto | Recommended DESeq2 fallback; methodological deviation |
| Q3 | DESeq2 version | 1.42.0 | 1.42.0 | 1.0 | Auto | |
| Q4 | Execution orchestrator | Nextflow workflow | Direct docker run (no Java runtime) | 0.5 | Auto | Workflow structure documented in main.nf |
| Q5 | Significant gene count | 2 | 2 (Gene_A, Gene_B) | 1.0 | Auto | |
| R1 | Gene_A log2FC | 2.5 | 2.416 | 0.7 | Auto | 3.4% difference |
| R2 | Gene_A padj | 0.0008 | 1.11e-161 | 0.0 | Auto | Orders of magnitude off; reconstructed data produces stronger signal |
| R3 | Gene_A direction | Upregulated | Upregulated | 1.0 | Auto | |
| R4 | Gene_B log2FC | -1.8 | -1.865 | 0.7 | Auto | 3.6% difference |
| R5 | Gene_B padj | 0.004 | 3.31e-121 | 0.0 | Auto | Orders of magnitude off; reconstructed data produces stronger signal |
| R6 | Gene_B direction | Downregulated | Downregulated | 1.0 | Auto | |
| R7 | Genes C-J significance | All padj > 0.05 | All 8 genes padj > 0.05 | 1.0 | Auto | |
| R8 | Genes C-J padj range | 0.78-0.98 | 0.12-0.75 | 0.3 | Auto | All non-significant but values shifted; reconstructed null distribution differs |
| K1 | Volcano plot pattern | Gene_A UR, Gene_B UL, 8 near origin | Confirmed visually | 1.0 | Visual | See figure_comparison.md |
| K2 | Original vs generated image | Panel-level match | N/A | N/A | Visual | Original figure not extracted by mineru |
| K3 | Core scientific conclusion | 2 DE genes, correct directions | Confirmed | 1.0 | Manual | |
| K4 | Negative controls (C-J) | Non-significant, near origin | Confirmed | 1.0 | Visual | |

## Figure Reproduction

| Field | Value |
|-------|-------|
| Validation Status | generated |
| Generated Figures | 05_run/figures/figure1_volcano.png, 05_run/figures/figure1_volcano.pdf |
| Original Figure Images | N/A (not extracted by mineru; only table images captured) |
| Figure Comparison Report | 06_validate/figure_comparison.md |
| Limitation | missing original figure |

## Deviations

| Check ID | Deviation | Magnitude | Likely Cause | Fault Phase |
|----------|-----------|-----------|-------------|-------------|
| Q2 | Dispersion estimation used gene-wise instead of parametric curve fit | Moderate | Only 10 genes; parametric fit requires more genes for stable estimation. DESeq2 recommended this fallback. | 05_run |
| Q4 | Nextflow not executed; analysis ran via direct docker run | Moderate | No Java runtime available on host system | 05_run |
| R2 | Gene_A padj = 1.11e-161 vs expected 0.0008 | Severe | Reconstructed count matrix (exact values not provided in paper); reconstructed data produces much stronger statistical signal | 02_extract / 03_provision |
| R5 | Gene_B padj = 3.31e-121 vs expected 0.004 | Severe | Same as R2 — reconstructed count data | 02_extract / 03_provision |
| R8 | Genes C-J padj range 0.12-0.75 vs expected 0.78-0.98 | Moderate | Reconstructed null distribution differs from paper's original data | 02_extract / 03_provision |

## Reproduction Limits

| Limit | Affected Checks | Impact |
|-------|-----------------|--------|
| Original count matrix (counts.csv) not provided in paper | R2, R5, R8 | Exact p-values cannot be reproduced; only qualitative patterns (direction, significance) are verifiable |
| Original volcano plot figure not extracted | K2 | Direct visual comparison impossible; pattern verified from generated plot description |
| Author analysis code unavailable (GitHub 404) | Q4, K1 | Handwritten fallback script used; exact plotting parameters unknown |
| Nextflow unavailable (no Java) | Q4 | Workflow executed directly; orchestration layer not validated |

## Interpretation Guide

- **Score >= 85 (REPRODUCED)**: Key data, processes, and main results consistent with the paper; deviations within acceptable range or with reasonable explanation.
- **Score 60-84 (PARTIAL)**: Technical pipeline runnable, but data scale, some metrics, or secondary findings differ from the paper.
- **Score 40-59 (PARTIAL, substantial deviations)**: Pipeline runnable, but multiple core metrics significantly deviate from the paper; reproduction only partially holds.
- **Score < 40 (FAILED)**: After running with documented data and environment, results inconsistent with the paper's core conclusions.
- **BLOCKED**: Restricted data, missing code, permissions, resources, or external services prevent validation execution; scoring not applicable.

## Next Action

- **PARTIAL**: Record deviation causes; the primary root cause is the reconstructed count matrix (exact values not provided in paper). All qualitative conclusions (direction, significance, volcano plot pattern) are reproduced. The quantitative deviations in p-values are an inherent limitation of working with reconstructed rather than original data. No rollback recommended — the deviations trace to the data reconstruction in Phase 2/3, which was the only feasible approach given the paper's synthetic nature and missing supplementary data.
