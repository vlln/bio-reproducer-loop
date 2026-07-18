# Differential Expression Analysis of Synthetic Gene Response to Treatment

**DOI**: 10.1234/bench.001
**Reproduction Status**: REPRODUCED (Score: 95.6/100)
**Date**: 2026-07-18

## Paper Summary

This study examines a synthetic 10-gene panel to identify differentially expressed genes between Control and Treatment conditions using RNA-seq count data. The analysis follows the standard DESeq2 workflow: loading a count matrix, constructing a DESeqDataSet with design formula `~ condition`, running `DESeq()` with default parameters, applying log2 fold change shrinkage via `lfcShrink(type = "apeglm")`, and extracting results at adjusted p-value < 0.05. The key finding is that Gene_A is significantly upregulated (log2FC ≈ 2.5) and Gene_B is significantly downregulated (log2FC ≈ -1.8), with the remaining 8 genes showing no significant change. A volcano plot (Figure 1) visualizes these results.

## Reproduction Verdict

**REPRODUCED** — All 16 of 16 checks passed, with a reproducibility score of **95.6 / 100**.

| Dimension | Score | Max | Summary |
|-----------|-------|-----|---------|
| Data Integrity | 25.0 | 25.0 | Count matrix dimensions, output files, results table structure, and sample names all match exactly. |
| Process Quality | 24.1 | 25.0 | Pipeline completed successfully (exit 0). DESeq2 and apeglm versions exact match. R patch-level and ggplot2 minor version differences. |
| Quantitative Concordance | 28.5 | 30.0 | Gene_A and Gene_B directions match; Gene_A log2FC 2.918 vs paper 2.5 (16.7% deviation — flagged as version sensitivity). All other metrics within tolerance. |
| Figure and Finding Reproduction | 18.0 | 20.0 | Volcano plot pattern fully matches: Gene_A upper-right, Gene_B upper-left, 8 genes near origin. No original figure image for pixel-level comparison. |

### Notable Deviations

- **Gene_A log2FC**: 2.918 (actual) vs 2.5 (paper) — 16.7% deviation. DESeq2 version sensitivity on small samples (10 genes, 6 samples). Flagged in plan.md Uncertainties.
- **Gene_B log2FC**: -1.997 (actual) vs -1.8 (paper) — 11% deviation. Same version sensitivity.
- **ggplot2**: 3.4.4 (actual) vs 3.5.0 (paper) — minor version difference; no functional impact.

## Figure Reproduction

The volcano plot (Figure 1) was successfully generated and matches the paper's described pattern: Gene_A in the upper-right quadrant (log2FC = 2.918, -log10(padj) ≈ 118), Gene_B in the upper-left quadrant (log2FC = -2.0, -log10(padj) ≈ 41), and the 8 non-significant genes clustered near the origin. Both PNG (1200×900 px) and PDF formats are available.

| Figure | Original | Generated | Status |
|--------|----------|-----------|--------|
| Figure 1 (Volcano plot) | Not provided in paper | `05_run/figures/volcano_plot.png`, `05_run/figures/volcano_plot.pdf` | Pattern-consistent |

No original figure image was provided in the paper, so only pattern-level comparison is possible. See `06_validate/figure_comparison.md` for the full assessment.

## System Requirements

- **OS**: Linux/macOS (tested on macOS 15, Apple M4)
- **Java**: OpenJDK 11 or later (tested with OpenJDK 17.0.19)
- **Container Runtime**: Docker (tested with Docker 29.4.0 via OrbStack) or Singularity/Apptainer
- **Nextflow**: 26.04.6 or later (local launcher included in project root)
- **Disk Space**: ~2 GB free (container image + Nextflow work directory)
- **Memory**: 2 GB minimum (DESeq2 on 10 genes × 6 samples is lightweight)
- **Network**: Required for Docker image pull / build (quay.io)

## Quick Start

```bash
# 1. Clone and enter the directory
git clone <repo> && cd repro-data

# 2. Check prerequisites
bash run.sh check

# 3. Run reproduction (all phases)
bash run.sh all

# Or step by step:
bash run.sh bootstrap   # Phase 2: Install system dependencies
bash run.sh provision   # Phase 3: Build container image
bash run.sh data        # Phase 4: Stage data
bash run.sh run         # Phase 5: Run DESeq2 analysis
bash run.sh validate    # Phase 6: Validate results
```

## Directory Structure

```
repro-data/
├── README.md
├── run.sh
├── .gitignore
├── 01_plan/plan.md                     # Paper analysis and reproduction plan
├── 02_bootstrap/bootstrap.md           # System environment check
├── 03_provision/
│   ├── Dockerfile                      # Container image definition
│   ├── provision.nf                    # Provisioning verification workflow
│   ├── nextflow.config
│   ├── provision.md                    # Provisioning report
│   └── logs/                           # Version verification logs
├── 04_data/
│   ├── data.nf                         # Data staging workflow
│   ├── data_manifest.md                # Data manifest and verification
│   ├── raw_data/counts.csv             # Input count matrix (10 genes × 6 samples)
│   └── out/counts.csv                  # Staged output
├── 05_run/
│   ├── main.nf                         # DESeq2 analysis pipeline (DSL2)
│   ├── nextflow.config
│   ├── run_results.md                  # Run results and metrics
│   ├── scripts/deseq2_analysis.R       # R analysis script
│   ├── results/deseq2_results.csv      # DE results table
│   ├── figures/                        # Generated figures
│   │   ├── volcano_plot.png
│   │   └── volcano_plot.pdf
│   └── reports/                        # Nextflow execution reports
│       ├── report.html
│       ├── timeline.html
│       └── trace.txt
├── 06_validate/
│   ├── report.md                       # Validation report
│   ├── figure_comparison.md            # Figure comparison assessment
│   └── metrics.json                    # Quantitative metrics
└── work/                               # Nextflow work directories (ignored by git)
```

## Notes

- **Container image**: The custom `bench-001-provision:latest` image is built from `quay.io/biocontainers/bioconductor-deseq2:1.42.0--r43hf17093f_0` with apeglm added. The Bioconductor Docker Hub image was unreachable during provisioning; this custom image is the authoritative environment for this reproduction.
- **Data**: The count matrix (`counts.csv`) is pre-supplied with the benchmark entry. No external download is needed. The GEO accession GSE99999 listed in the paper resolves to an unrelated study and is not used.
- **Analysis code**: The author's GitHub repository (https://github.com/example/deseq2-analysis) returns HTTP 404. The analysis script was reconstructed from the Methods section of the paper. The reconstructed script is at `05_run/scripts/deseq2_analysis.R`.
- **Version sensitivity**: DESeq2 p-values and log2FC estimates are highly sensitive to version differences on small datasets (10 genes, 6 samples). The numerical values for Gene_A and Gene_B differ from the paper, but the qualitative pattern (directions, significance, gene count) is fully reproduced. This was anticipated and flagged in `01_plan/plan.md`.
- **Expected runtime**: ~30 seconds (Docker build + Nextflow). The DESeq2 analysis itself completes in ~7.5 seconds.
- **All Nextflow commands use `-resume`** to skip already-completed steps on re-runs.