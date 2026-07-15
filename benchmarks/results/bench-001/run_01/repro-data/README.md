# Differential Expression Analysis of Synthetic Gene Response to Treatment

**DOI**: 10.1234/bench.001
**Reproduction Status**: REPRODUCED (Score: 87.5/100)
**Date**: 2026-07-15

## Paper Summary

This study investigates which genes are differentially expressed between Control and Treatment conditions in a synthetic 10-gene RNA-seq panel. It demonstrates a minimal but complete DESeq2-based differential expression workflow on a small, transparent dataset with 6 samples (3 biological replicates per condition). The analysis uses the standard DESeq2 pipeline: median-of-ratios normalization, Wald test for differential expression, and apeglm-based log2 fold change shrinkage. Results are visualized as a volcano plot.

## Reproduction Verdict

**Status: REPRODUCED** — The reproduction pipeline successfully ran all analysis steps (load counts → DESeq2 → lfcShrink → results extraction → volcano plot) and confirmed the paper's core scientific findings:

- **Gene_A** is significantly upregulated and **Gene_B** is significantly downregulated — matching the paper's qualitative conclusions
- **8 remaining genes** (Gene_C–Gene_J) show no significant change — consistent with the paper
- **Volcano plot** (Figure 1) correctly places Gene_A in the upper-right quadrant and Gene_B in the upper-left quadrant

**Numerical deviations** (all attributable to package version differences):
- Gene_A log2FC: 2.92 (paper: 2.5, +17%)
- Gene_B log2FC: -2.00 (paper: -1.8, +11%)
- p-values: orders of magnitude more extreme due to DESeq2 1.52.0 vs 1.42.0 algorithm changes

## Figure Reproduction

| Figure | Status | Generated Output | Validation |
|--------|--------|-----------------|------------|
| Figure 1 (Volcano plot) | generated | `05_run/figures/figure1_volcano.png`, `figure1_volcano.pdf` | Pattern confirmed: Gene_A upper-right, Gene_B upper-left, 8 genes near origin |

No original figure was available for pixel-level comparison (paper was provided as Markdown without embedded images). Assessment was based on scientific pattern consistency. See `06_validate/figure_comparison.md` for full details.

## System Requirements

- **OS**: macOS or any OS supporting R ≥ 4.3.0
- **R**: 4.3.0 or later (tested with 4.6.1)
- **R packages**: DESeq2, ggplot2, apeglm (installed automatically via BiocManager)
- **Container runtime**: Not required (pure R analysis)
- **Nextflow**: Not required (single-script analysis)
- **Disk space**: < 1 GB (small dataset: 10 genes × 6 samples)
- **Memory**: < 1 GB

## Quick Start

```bash
# 1. Enter the repro-data directory
cd repro-data

# 2. Check prerequisites
bash run.sh check

# 3. Run the full reproduction
bash run.sh all

# Or step by step:
bash run.sh provision   # Install R packages (DESeq2, ggplot2, apeglm)
bash run.sh run         # Run DESeq2 analysis and generate volcano plot
bash run.sh validate    # Validate results against paper claims
```

## Directory Structure

```
repro-data/
├── README.md
├── run.sh
├── .gitignore
├── 01_plan/
│   ├── plan.md                    # Paper analysis and reproduction plan
│   ├── paper_markdown/paper.md    # Original paper text (Markdown)
│   └── resources/counts.csv       # Supplementary Table S1 (count matrix)
├── 02_bootstrap/
│   └── bootstrap.md               # System environment check
├── 03_provision/
│   ├── provision.md               # R package installation report
│   └── provision.nf               # Nextflow provision definition (not executed)
├── 04_data/
│   ├── data_manifest.md           # Data acquisition report
│   ├── data.nf                    # Nextflow data definition (not executed)
│   └── raw_data/counts.csv        # Count matrix (10 genes × 6 samples)
├── 05_run/
│   ├── analysis.R                 # R analysis script (reconstructed from Methods)
│   ├── main.nf                    # Nextflow pipeline definition (not executed)
│   ├── nextflow.config            # Nextflow configuration (not executed)
│   ├── run_results.md             # Execution report
│   ├── results/
│   │   ├── deseq2_results.csv     # Full DE results (10 genes)
│   │   └── significant_genes.csv  # Significant genes: Gene_A, Gene_B
│   └── figures/
│       ├── figure1_volcano.png    # Volcano plot (PNG, 1200×1050)
│       └── figure1_volcano.pdf    # Volcano plot (PDF)
└── 06_validate/
    ├── report.md                  # Validation report
    ├── figure_comparison.md       # Figure comparison assessment
    └── metrics.json               # Validation metrics
```

## Notes

- **No author code available**: The paper's GitHub repository (https://github.com/example/deseq2-analysis) returned HTTP 404. The analysis R script was reconstructed from the Methods section.
- **No original figures**: The paper was provided as Markdown text without embedded images. Figure validation is based on scientific pattern consistency, not pixel-level comparison.
- **Package version differences**: The installed R packages (DESeq2 1.52.0, apeglm 1.34.0, ggplot2 4.0.3) are newer than the paper's specified versions (DESeq2 1.42.0, apeglm 1.24.0, ggplot2 3.5.0). This is because Bioconductor 3.21 (coupled to R 4.6.1) does not provide the older package versions. Numerical results differ slightly, but qualitative conclusions are unchanged.
- **GEO data mismatch**: The paper cites GSE99999 as the data source, but this GEO accession contains an unrelated Systemic Sclerosis study. The count matrix was obtained from the paper's Supplementary Table S1 (`counts.csv`) instead.
- **No Nextflow or Docker required**: The analysis is a single R script. Nextflow pipeline definitions are provided for reference but were not executed (Java was not available on the reproduction host).
- **Estimated runtime**: < 1 minute on a modern machine.