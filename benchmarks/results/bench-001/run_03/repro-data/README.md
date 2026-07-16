# Differential Expression Analysis of Synthetic Gene Response to Treatment

**DOI**: 10.1234/bench.001
**Reproduction Status**: REPRODUCED (Score: 87.5/100)
**Date**: 2026-07-16

## Paper Summary

This study identifies differentially expressed genes (DEGs) between Control and Treatment conditions using a synthetic 10-gene RNA-seq count panel. The analysis follows the canonical DESeq2 workflow: loading a count matrix from CSV, constructing a DESeqDataSet with design formula `~ condition`, running DESeq2 with default parameters, applying log2 fold change shrinkage via `lfcShrink(type = "apeglm")`, and extracting results at adjusted p-value < 0.05. A volcano plot visualizes the results using ggplot2.

## Reproduction Verdict

**REPRODUCED** — Score: 87.5/100 (17 checks scored, 0 N/A)

| Dimension | Score | Max | Assessment |
|-----------|-------|-----|------------|
| Data Integrity | 25.0 | 25.0 | All 4 checks passed. Gene count, sample count, output files, and table structure all match. |
| Process Quality | 20.0 | 25.0 | Pipeline succeeded. DESeq2 version matches (1.42.1 vs 1.42.0). Minor R/ggplot2 version differences from Bioconductor container. |
| Quantitative Concordance | 22.5 | 30.0 | Directions, significance calls, and non-DE genes all correct. log2FC magnitudes within ~17%. padj values are orders of magnitude more extreme than the paper's idealized values. |
| Figure and Finding Reproduction | 20.0 | 20.0 | All 5 checks passed. Volcano plot pattern confirmed. Core biological conclusions fully reproduced. |

The numerical discrepancies (log2FC and padj magnitudes) originate from the paper using idealized/synthetic values. The reproduction correctly implements the described analysis on the actual count data. The core biological conclusions are fully reproduced: Gene_A is significantly upregulated, Gene_B is significantly downregulated, and the remaining 8 genes (Gene_C–Gene_J) show no significant differential expression.

### Key Deviations

| Metric | Paper | Reproduced | Cause |
|--------|-------|------------|-------|
| Gene_A log2FC | 2.5 | 2.92 (+16.8%) | Paper uses idealized values |
| Gene_A padj | 0.0008 | 4.37e-119 | Same as above |
| Gene_B log2FC | -1.8 | -2.00 (-11.1%) | Same as above |
| Gene_B padj | 0.004 | 5.57e-42 | Same as above |
| R version | 4.3.0 | 4.4.0 | Bioconductor RELEASE_3_18 container |
| ggplot2 version | 3.5.0 | 4.0.3 | Bioconductor RELEASE_3_18 container |

## Figure Reproduction

| Figure/Panel | Status | Generated Files | Validation |
|--------------|--------|-----------------|------------|
| Figure 1 (volcano plot) | Generated | `05_run/figures/volcano_plot.png` (46 KB, 1050×900 px), `volcano_plot.pdf` (6 KB, 1 page) | Pattern-based visual: Gene_A upper-right, Gene_B upper-left, others near origin — confirmed |

The generated volcano plot was visually inspected and compared against the paper's described expected pattern. Gene_A is positioned in the upper-right quadrant, Gene_B in the upper-left quadrant, and the remaining 8 genes are tightly clustered near the origin. All structural elements (significance threshold line, axis labels, legend) are present. The plot fully reproduces the scientific pattern described in the paper.

**Limitation**: No original figure image was provided in the paper. Pixel-level comparison is not possible. Validation is based on pattern matching against the paper's textual description. See `06_validate/figure_comparison.md` for the detailed visual assessment.

## System Requirements

- **OS**: macOS / Linux (tested on macOS 15 with Apple M4)
- **Container Runtime**: Docker (tested with OrbStack 29.4.0)
- **Nextflow**: 26.04.6 (project-local script included)
- **Java**: 17+ (tested with OpenJDK 17.0.19 via Homebrew)
- **Disk Space**: ~2 GB (container image); analysis data is ~390 bytes
- **Memory**: 4 GB minimum (16 GB recommended)
- **Network**: Required for initial container pull only

## Quick Start

```bash
# 1. Clone and enter the repository
git clone <repo> && cd repro-data

# 2. Check prerequisites
bash run.sh check

# 3. Run reproduction (all phases)
bash run.sh all

# Or step by step:
bash run.sh bootstrap   # Phase 2: Review environment report
bash run.sh provision   # Phase 3: Pull/build container
bash run.sh data        # Phase 4: Stage data
bash run.sh run         # Phase 5: Run DESeq2 analysis
bash run.sh validate    # Phase 6: Review validation report
```

## Directory Structure

```
repro-data/
├── README.md
├── run.sh
├── .gitignore
├── 01_plan/
│   └── plan.md                       # Paper extraction and reproduction plan
├── 02_bootstrap/
│   └── bootstrap.md                  # Environment inventory and verification
├── 03_provision/
│   ├── provision.md                  # Container provisioning report
│   ├── Dockerfile                    # Custom Docker image definition
│   ├── provision.nf                  # Nextflow workflow for container build
│   └── nextflow.config               # Nextflow config (Docker scope)
├── 04_data/
│   ├── data_manifest.md              # Data acquisition report
│   ├── data.nf                       # Nextflow workflow for data staging
│   ├── nextflow.config
│   └── raw_data/
│       └── counts.csv                # Count matrix (10 genes × 6 samples)
├── 05_run/
│   ├── main.nf                       # Main analysis pipeline (DSL2)
│   ├── run_results.md                # Execution summary and results
│   ├── deseq2_analysis.R             # DESeq2 + apeglm analysis script
│   ├── volcano_plot.R                # Volcano plot generation script
│   ├── nextflow.config
│   ├── results/
│   │   ├── deseq2_results.csv        # DE results table
│   │   └── normalized_counts.csv
│   ├── figures/
│   │   ├── volcano_plot.png          # Figure 1 (PNG)
│   │   └── volcano_plot.pdf          # Figure 1 (PDF)
│   └── reports/
│       ├── run_report.html
│       ├── timeline.html
│       └── trace.txt
└── 06_validate/
    ├── report.md                     # Validation report
    ├── figure_comparison.md          # Figure comparison assessment
    ├── checks_plan.md                # Validation check definitions
    └── metrics.json                  # Machine-readable metrics
```

## Notes

- **Paper is a benchmark**: The paper uses synthetic/idealized numerical values for log2FC and padj. The reproduction using actual DESeq2 on the count data produces more extreme p-values and slightly different log2FC estimates. Directions and significance calls are fully consistent.
- **No author code available**: The GitHub repository (https://github.com/example/deseq2-analysis) returns HTTP 404. The analysis pipeline was reconstructed from the Methods section of the paper.
- **No original figure image**: The paper describes the volcano plot but does not provide an original image file. Visual validation is pattern-based.
- **GEO accession mismatch**: GSE99999 resolves to an unrelated study. The count matrix from Supplementary Table S1 (`counts.csv`) is used as the primary data source.
- **Estimated runtime**: ~5 minutes (including container pull). Cached re-runs complete in ~5 seconds.
- **Java note**: The system Java stub may not work without `JAVA_HOME` set. The `run.sh` script handles this automatically.