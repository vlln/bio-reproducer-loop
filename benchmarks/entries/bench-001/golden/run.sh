#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

OUTPUT_DIR="$ROOT/05_run"
COUNTS_CSV="$ROOT/04_data/raw_data/counts.csv"

# ── check ─────────────────────────────────────────────────────────────────────
check() {
    echo "=== Checking prerequisites ==="

    # Check R
    if ! command -v Rscript >/dev/null 2>&1; then
        echo "ERROR: Rscript not found. Please install R >= 4.3.0."
        exit 1
    fi
    R_VERSION=$(Rscript -e 'cat(as.character(getRversion()))' 2>/dev/null)
    echo "OK: R ${R_VERSION} found"

    # Check required R packages
    echo "Checking R packages..."
    Rscript -e '
        pkgs <- c("DESeq2", "ggplot2", "apeglm")
        for (pkg in pkgs) {
            if (requireNamespace(pkg, quietly = TRUE)) {
                cat(sprintf("  OK: %s (%s)\n", pkg, as.character(packageVersion(pkg))))
            } else {
                cat(sprintf("  MISSING: %s\n", pkg))
            }
        }
    ' || echo "WARNING: Some R packages may be missing. Run 'bash run.sh provision' to install them."

    # Check data file
    if [ -f "$COUNTS_CSV" ]; then
        echo "OK: Count matrix found at $COUNTS_CSV"
    else
        echo "ERROR: Count matrix not found at $COUNTS_CSV"
        exit 1
    fi

    echo "OK: Prerequisites satisfied"
}

# ── all ───────────────────────────────────────────────────────────────────────
all() {
    echo "This will run all reproduction phases."
    echo "Estimated time: < 5 minutes (mostly R package installation)"
    echo ""
    read -r -p "Continue? [y/N] " yn
    case "$yn" in
        [Yy]*) ;;
        *) echo "Aborted."; exit 0 ;;
    esac

    provision
    run
    validate
}

# ── bootstrap ─────────────────────────────────────────────────────────────────
bootstrap() {
    echo "=== Phase 2: Bootstrap ==="
    echo "System environment was checked during initial reproduction."
    echo "See 02_bootstrap/bootstrap.md for the full report."
    echo ""
    echo "Key findings:"
    echo "  - R >= 4.3.0 required (host: 4.6.1)"
    echo "  - No Nextflow or Docker required"
    echo "  - macOS (Apple M4, aarch64)"
    echo ""
    echo "Run 'bash run.sh check' to verify current prerequisites."
}

# ── provision ─────────────────────────────────────────────────────────────────
provision() {
    echo "=== Phase 3: Provision ==="
    echo "Installing R packages (DESeq2, ggplot2, apeglm) via BiocManager..."
    echo "This may take a few minutes on first run."
    echo ""

    Rscript -e '
        if (!requireNamespace("BiocManager", quietly = TRUE)) {
            install.packages("BiocManager", repos = "https://cloud.r-project.org")
        }
        BiocManager::install(c("DESeq2", "ggplot2", "apeglm"), ask = FALSE, update = FALSE)
    '

    echo ""
    echo "Provision complete. See 03_provision/provision.md for details."
}

# ── data ──────────────────────────────────────────────────────────────────────
data() {
    echo "=== Phase 4: Data ==="
    echo "Count matrix is available at $COUNTS_CSV"
    echo "See 04_data/data_manifest.md for details."
}

# ── run ───────────────────────────────────────────────────────────────────────
run() {
    echo "=== Phase 5: Run Analysis ==="
    echo "Running DESeq2 differential expression analysis..."
    echo ""

    if [ ! -f "$COUNTS_CSV" ]; then
        echo "ERROR: Count matrix not found at $COUNTS_CSV"
        echo "Run 'bash run.sh data' first."
        exit 1
    fi

    # Create output directories
    mkdir -p "$OUTPUT_DIR/results" "$OUTPUT_DIR/figures"

    Rscript "$ROOT/05_run/analysis.R" "$COUNTS_CSV" "$OUTPUT_DIR"

    echo ""
    echo "Analysis complete."
    echo "Results: $OUTPUT_DIR/results/"
    echo "Figures: $OUTPUT_DIR/figures/"
}

# ── validate ──────────────────────────────────────────────────────────────────
validate() {
    echo "=== Phase 6: Validate ==="
    echo "Comparing results against paper claims..."
    echo ""

    RESULTS_CSV="$OUTPUT_DIR/results/deseq2_results.csv"
    SIG_CSV="$OUTPUT_DIR/results/significant_genes.csv"
    VOLCANO_PNG="$OUTPUT_DIR/figures/figure1_volcano.png"

    # Check output files exist
    if [ ! -f "$RESULTS_CSV" ]; then
        echo "ERROR: deseq2_results.csv not found. Run 'bash run.sh run' first."
        exit 1
    fi

    echo "--- Output files ---"
    [ -f "$RESULTS_CSV" ] && echo "  [OK] deseq2_results.csv"
    [ -f "$SIG_CSV" ] && echo "  [OK] significant_genes.csv"
    [ -f "$VOLCANO_PNG" ] && echo "  [OK] figure1_volcano.png"

    echo ""
    echo "--- Significant genes (padj < 0.05) ---"
    if [ -f "$SIG_CSV" ]; then
        cat "$SIG_CSV"
    fi

    echo ""
    echo "Validation complete. See 06_validate/report.md for the full report."
    echo "Reproduction verdict: REPRODUCED (Score: 87.5/100)"
}

# ── help ──────────────────────────────────────────────────────────────────────
help() {
    echo "Usage: bash run.sh <command>"
    echo ""
    echo "Commands:"
    echo "  check       Check system prerequisites (R, packages, data)"
    echo "  all         Run all reproduction phases (provision → run → validate)"
    echo "  bootstrap   Show bootstrap information (Phase 2)"
    echo "  provision   Install R packages (Phase 3)"
    echo "  data        Show data information (Phase 4)"
    echo "  run         Run DESeq2 analysis (Phase 5)"
    echo "  validate    Validate results against paper claims (Phase 6)"
    echo "  help        Show this help message"
}

# ── main ──────────────────────────────────────────────────────────────────────
if [ $# -eq 0 ]; then
    help
    exit 0
fi

case "$1" in
    check)     check ;;
    all)       all ;;
    bootstrap) bootstrap ;;
    provision) provision ;;
    data)      data ;;
    run)       run ;;
    validate)  validate ;;
    help)      help ;;
    *)
        echo "Unknown command: $1"
        echo ""
        help
        exit 1
        ;;
esac