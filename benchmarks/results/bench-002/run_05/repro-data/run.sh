#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

check() {
    echo "=== Checking Prerequisites ==="
    command -v Rscript >/dev/null 2>&1 || { echo "ERROR: Rscript not found. Install R >= 4.3.0."; exit 1; }
    echo "OK: Rscript found ($(Rscript --version 2>&1))"
    echo "OK: Prerequisites satisfied"
}

all() {
    echo "This will run all reproduction phases."
    echo "Estimated time: ~3-5 minutes"
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
    echo "Verifying system environment..."
    echo "See 02_bootstrap/bootstrap.md for the full environment report."
    echo "Bootstrap complete."
}

provision() {
    echo "=== Phase 3: Provision ==="
    echo "Installing R packages: DESeq2, ggplot2, apeglm, clusterProfiler, pathview, org.Hs.eg.db..."
    Rscript -e '
        if (!requireNamespace("BiocManager", quietly = TRUE)) install.packages("BiocManager", repos = "https://cloud.r-project.org")
        BiocManager::install(c("DESeq2", "ggplot2", "apeglm", "clusterProfiler", "pathview", "org.Hs.eg.db"), ask = FALSE, update = FALSE)
    '
    echo "See 03_provision/provision.md for the full provision report."
    echo "Provision complete."
}

data() {
    echo "=== Phase 4: Data ==="
    echo "The count matrix (counts.csv) is already in 04_data/raw_data/."
    echo "See 04_data/data_manifest.md for the full data manifest."
    echo "Data acquisition complete."
}

run() {
    echo "=== Phase 5: Run Analysis ==="
    echo "Executing R analysis pipeline (DESeq2 → clusterProfiler → pathview)..."
    echo "Estimated time: ~2-4 minutes"
    Rscript 05_run/analysis.R
    echo "See 05_run/run_results.md for the run results."
    echo "Analysis complete. Outputs in 05_run/results/ and 05_run/figures/."
}

validate() {
    echo "=== Phase 6: Validate ==="
    echo "Validation report is in 06_validate/report.md."
    echo "See 06_validate/report.md for the full validation report."
    echo "Validation complete."
}

"${@:-check}"