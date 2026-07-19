#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

check() {
    echo "=== Checking prerequisites ==="
    command -v R >/dev/null 2>&1 || { echo "ERROR: R not found. Install R >= 4.3.0."; exit 1; }
    R_VERSION=$(R --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "0.0.0")
    echo "R version: $R_VERSION"
    echo "OK: Prerequisites satisfied"
}

all() {
    echo "This will run all reproduction phases."
    echo "Estimated time: < 5 minutes"
    read -p "Continue? [y/N] " yn
    case "$yn" in [Yy]*) ;; *) exit 0;; esac
    bootstrap
    provision
    data
    run
    validate
}

bootstrap() {
    echo "=== Phase 2: Bootstrap ==="
    echo "Installing R package dependencies..."
    Rscript -e '
        pkgs <- c("DESeq2", "ggplot2", "apeglm", "clusterProfiler", "pathview", "org.Hs.eg.db")
        for (p in pkgs) {
            if (!requireNamespace(p, quietly=TRUE)) {
                if (p %in% c("DESeq2", "apeglm", "clusterProfiler", "org.Hs.eg.db")) {
                    if (!requireNamespace("BiocManager", quietly=TRUE)) install.packages("BiocManager", repos="https://cloud.r-project.org")
                    BiocManager::install(p, ask=FALSE, update=FALSE)
                } else {
                    install.packages(p, repos="https://cloud.r-project.org")
                }
            }
            cat(p, ": ", as.character(packageVersion(p)), "\n", sep="")
        }
    '
    echo "Bootstrap complete."
}

provision() {
    echo "=== Phase 3: Provision ==="
    echo "Verifying R environment..."
    Rscript -e '
        pkgs <- c("DESeq2", "ggplot2", "apeglm", "clusterProfiler", "pathview", "org.Hs.eg.db")
        for (p in pkgs) {
            if (requireNamespace(p, quietly=TRUE)) {
                cat("OK: ", p, " (", as.character(packageVersion(p)), ")\n", sep="")
            } else {
                cat("ERROR: ", p, " not installed\n", sep="")
            }
        }
    '
    echo "Provision complete."
}

data() {
    echo "=== Phase 4: Data ==="
    if [ -f "04_data/raw_data/counts.csv" ]; then
        echo "counts.csv already present in 04_data/raw_data/"
    else
        echo "ERROR: counts.csv not found in 04_data/raw_data/. Please ensure the count matrix is available."
        exit 1
    fi
    echo "Data check complete."
}

run() {
    echo "=== Phase 5: Run ==="
    echo "Running DE → GO → KEGG analysis..."
    if [ ! -f "05_run/run_analysis.R" ]; then
        echo "ERROR: run_analysis.R not found in 05_run/"
        exit 1
    fi
    Rscript 05_run/run_analysis.R "$ROOT"
    echo "Run complete. Results in 05_run/results/ and figures in 05_run/figures/"
}

validate() {
    echo "=== Phase 6: Validate ==="
    echo "Check 06_validate/report.md for the full validation report."
    if [ -f "06_validate/report.md" ]; then
        echo "Validation report: 06_validate/report.md"
        if [ -f "06_validate/figure_comparison.md" ]; then
            echo "Figure comparison: 06_validate/figure_comparison.md"
        fi
    else
        echo "WARNING: validation report not found. Please run the analysis first."
    fi
    echo "Validate complete."
}

"${@:-check}"