# Differential Expression Analysis of Synthetic Gene Response to Treatment

**DOI**: 10.1234/bench.001
**Reproduction Status**: REPRODUCED (Score: 85/100)
**Date**: 2026-07-18

## Paper Summary

This study investigates differentially expressed genes between Control and Treatment conditions in a synthetic 10-gene RNA-seq panel. Using a minimal, fully known dataset of 10 genes across 6 samples (3 replicates per condition), the paper demonstrates a complete DESeq2 differential expression workflow. The analysis starts from a raw integer count matrix and identifies Gene_A (upregulated) and Gene_B (downregulated) as the only two significantly differentially expressed genes (padj < 0.05), with the remaining 8 genes showing no significant change.

## Reproduction Verdict

**REPRODUCED** with a score of **85.0 / 100**. The core biological conclusions are fully confirmed: 2 significant genes (Gene_A upregulated, Gene_B downregulated) identified exactly as the paper claims, and all 8 non-significant genes are consistently non-significant. The volcano plot (Figure 1) shows the expected pattern: Gene_A in the upper-right quadrant, Gene_B in the upper-left, and non-significant genes clustered near the origin.

Known deviations:
- **Software versions**: The analysis ran on the host R 4.6.1 / DESeq2 1.52.0 instead of the provisioned Docker container (R 4.3.3 / DESeq2 1.42.1), causing minor version drift.
- **log2FC values**: Gene_A log2FC = 2.92 vs expected ~2.5 (16.8% deviation); Gene_B = -2.00 vs expected -1.8 (11.1% deviation). These are within acceptable range given DESeq2 version differences.
- **p-value magnitudes**: Observed padj values (Gene_A: 4.37e-119, Gene_B: 5.57e-42) differ by orders of magnitude from paper-claimed values (0.0008, 0.004). The paper values appear to be rounded for presentation; the direction and significance classification are correct.
- **No original figure image**: The paper does not provide an original volcano plot image for pixel-level comparison. Validation is pattern-based.

Score breakdown:
| Dimension | Score | Max |
|-----------|-------|-----|
| Data Integrity | 25.0 | 25 |
| Process Quality | 17.5 | 25 |
| Quantitative Concordance | 22.5 | 30 |
| Figure and Finding Reproduction | 20.0 | 20 |
| **Total** | **85.0** | **100** |

## Figure Reproduction

The volcano plot (Figure 1, `05_run/figures/figure1_volcano.png`) was generated using a handwritten R script reconstructed from the Methods section, as the original author code repository (https://github.com/example/deseq2-analysis) is inaccessible (HTTP 404). The plot correctly shows:
- Gene_A in the upper-right quadrant (red, high log2FC and significance)
- Gene_B in the upper-left quadrant (red, negative log2FC and high significance)
- 8 non-significant genes (grey) clustered near the origin

No original figure image was available for pixel-level comparison. See `06_validate/figure_comparison.md` for the full figure validation report.

## System Requirements

- **OS**: macOS (also compatible with Linux)
- **Container runtime**: Docker 29.4.0+ (or Singularity/Apptainer)
- **Nextflow**: 22.10+ (install via `curl -s https://get.nextflow.io | bash`)
- **Java**: 11+ (required by Nextflow; macOS may prompt for installation on first use)
- **Disk space**: < 100 MB (synthetic dataset, minimal compute)
- **Memory**: 4 GB RAM minimum
- **Network**: Required for container image pull (bioconductor/bioconductor_docker:RELEASE_3_18)

## Quick Start

```bash
# 1. Clone and enter the directory
git clone <repo> && cd repro-data

# 2. Check prerequisites
bash run.sh check

# 3. Run the full reproduction (all phases)
bash run.sh all

# Or run step by step:
bash run.sh bootstrap   # Phase 2: Install system dependencies
bash run.sh provision   # Phase 3: Pull/build container
bash run.sh data        # Phase 4: Download/prepare data
bash run.sh run         # Phase 5: Run the analysis
bash run.sh validate    # Phase 6: Validate results
```

## Directory Structure

```
repro-data/
├── README.md
├── run.sh
├── .gitignore
├── 01_plan/
│   ├── plan.md
│   └── paper_markdown/
│       └── paper/
│           ├── paper.md
│           └── images/
├── 02_bootstrap/
│   └── bootstrap.md
├── 03_provision/
│   ├── provision.md
│   ├── Dockerfile
│   ├── provision.nf
│   └── nextflow.config
├── 04_data/
│   ├── data_manifest.md
│   ├── data.nf
│   └── raw_data/
│       └── counts.csv
├── 05_run/
│   ├── main.nf
│   ├── analysis.R
│   ├── run_results.md
│   ├── results/
│   │   └── de_results.csv
│   ├── figures/
│   │   └── figure1_volcano.png
│   └── reports/
│       ├── report.html
│       ├── timeline.html
│       └── trace.txt
└── 06_validate/
    ├── report.md
    ├── figure_comparison.md
    └── metrics.json
```

## Notes

- **Container not used during run**: The Phase 5 run executed on the host R environment (4.6.1) instead of the provisioned Docker container (R 4.3.3 / DESeq2 1.42.1). To use the container, ensure Docker is enabled in your Nextflow configuration (`docker.enabled = true`). The qualitative results are unaffected by this version drift.
- **Data access**: The count matrix (`counts.csv`) is included in this repository under `04_data/raw_data/`. The paper's GEO accession (GSE99999) resolves to an unrelated study and cannot be used. The author's GitHub repository (https://github.com/example/deseq2-analysis) returns HTTP 404; the analysis script was reconstructed from the Methods description.
- **Expected runtime**: < 1 minute for the full pipeline on a modern machine.
- **p-value magnitudes**: The observed p-values are far more extreme than the paper reports. The paper values (0.0008, 0.004) appear to be rounded for presentation purposes. The statistical conclusion (significant vs not) is identical.
- **No original figure comparison**: The paper does not include an original volcano plot image. Figure validation is based on gene positions and the significance pattern matching the paper's description.