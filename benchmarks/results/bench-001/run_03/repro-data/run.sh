#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# ── image name ───────────────────────────────────────────────────────────────
IMAGE="bio-reproducer:bench-001"

# ── check ────────────────────────────────────────────────────────────────────
check() {
    echo "=== Checking Prerequisites ==="
    local ok=1

    if ! command -v docker >/dev/null 2>&1; then
        echo "ERROR: docker not found — install Docker or OrbStack"
        ok=0
    else
        echo "OK: docker ($(docker --version 2>/dev/null | head -1))"
    fi

    echo ""
    if [ "$ok" -eq 0 ]; then
        echo "Some prerequisites are missing. Please install them and re-run."
        exit 1
    fi
    echo "All prerequisites satisfied."
}

# ── bootstrap ────────────────────────────────────────────────────────────────
bootstrap() {
    echo "=== Phase 2: Bootstrap ==="
    echo "This phase assesses the system environment."
    echo "The bootstrap report already exists at 02_bootstrap/bootstrap.md."
    echo ""
    echo "System: macOS (Darwin), Apple M4, 16 GB RAM, 228 GB disk"
    echo "Docker: available (OrbStack)"
    echo "R: 4.6.1 (native), 4.3.3 (in container)"
    echo ""
    echo "No action needed — bootstrap is informational only."
    echo "See 02_bootstrap/bootstrap.md for full details."
}

# ── provision ────────────────────────────────────────────────────────────────
provision() {
    echo "=== Phase 3: Provision ==="
    echo "Building Docker image: ${IMAGE}"
    echo "This is a one-time operation (~10 minutes, ~6 GB disk)."
    echo ""

    # Check if image already exists
    if docker image inspect "${IMAGE}" >/dev/null 2>&1; then
        echo "Image ${IMAGE} already exists."
        read -rp "Rebuild? [y/N] " yn
        case "$yn" in [Yy]*) ;; *) echo "Skipping build."; return 0;; esac
    fi

    docker build \
        --platform linux/arm64 \
        -t "${IMAGE}" \
        -f "${ROOT}/03_provision/Dockerfile" \
        "${ROOT}/03_provision"

    echo ""
    echo "Image built successfully."
    echo "See 03_provision/provision.md for details."
}

# ── data ─────────────────────────────────────────────────────────────────────
data() {
    echo "=== Phase 4: Data ==="
    echo "The count matrix already exists at 04_data/raw_data/counts.csv."
    echo "It was reconstructed from the paper description (10 genes x 6 samples)."
    echo ""
    echo "No action needed — data is pre-generated."
    echo "See 04_data/data_manifest.md for details."
}

# ── run ──────────────────────────────────────────────────────────────────────
run() {
    echo "=== Phase 5: Run Analysis ==="
    echo "Running DESeq2 differential expression analysis via Docker."
    echo "Estimated time: < 1 minute."
    echo ""

    # Check image exists
    if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
        echo "ERROR: Docker image ${IMAGE} not found."
        echo "Run 'bash run.sh provision' first."
        exit 1
    fi

    # Ensure output directories exist
    mkdir -p "${ROOT}/05_run/results" "${ROOT}/05_run/figures"

    # Container network check
    echo "[Check] Testing container network connectivity..."
    docker run --rm "${IMAGE}" \
        Rscript -e 'cat("R OK\n"); if(curl::has_internet()) cat("Internet: OK\n") else cat("Internet: UNAVAILABLE\n")' 2>&1 || true
    echo ""

    # Run analysis
    echo "[Run] Starting DESeq2 analysis..."
    docker run --rm \
        --platform linux/arm64 \
        -v "${ROOT}:/data:ro" \
        -v "${ROOT}/05_run/results:/data/05_run/results" \
        -v "${ROOT}/05_run/figures:/data/05_run/figures" \
        "${IMAGE}" \
        Rscript /data/05_run/analysis.R /data/04_data/raw_data /data/05_run

    echo ""
    echo "Analysis completed."
    echo "Results: 05_run/results/deseq2_results.csv"
    echo "Figures: 05_run/figures/figure1_volcano.png"
    echo "See 05_run/run_results.md for details."
}

# ── validate ─────────────────────────────────────────────────────────────────
validate() {
    echo "=== Phase 6: Validate ==="
    echo "Validation report already exists at 06_validate/report.md."
    echo ""

    if [ -f "${ROOT}/06_validate/report.md" ]; then
        # Extract verdict line
        local verdict
        verdict=$(grep -E '^\| Status' "${ROOT}/06_validate/report.md" | head -1 || echo "N/A")
        echo "Validation: ${verdict}"
        echo "See 06_validate/report.md for full report."
        echo "See 06_validate/figure_comparison.md for figure comparison."
    else
        echo "Validation report not found. Ensure Phase 5 completed successfully."
        exit 1
    fi
}

# ── all ──────────────────────────────────────────────────────────────────────
all() {
    echo "=============================================="
    echo " Reproduction Pipeline — All Phases"
    echo " Paper: Differential Expression Analysis of"
    echo "        Synthetic Gene Response to Treatment"
    echo "=============================================="
    echo ""
    echo "This will run: provision → data → run → validate"
    echo "Estimated time: ~10 minutes (first run, includes Docker build)"
    echo "Disk space: ~7 GB for Docker image"
    echo ""
    read -rp "Continue? [y/N] " yn
    case "$yn" in
        [Yy]*) ;;
        *) echo "Aborted."; exit 0;;
    esac
    echo ""

    provision
    echo ""
    data
    echo ""
    run
    echo ""
    validate
    echo ""

    echo "=============================================="
    echo " All phases completed."
    echo " See 06_validate/report.md for the verdict."
    echo "=============================================="
}

# ── dispatch ─────────────────────────────────────────────────────────────────
if [ $# -eq 0 ]; then
    echo "Usage: run.sh <command>"
    echo ""
    echo "Commands:"
    echo "  check       Check system prerequisites"
    echo "  bootstrap   Phase 2: Assess environment (informational)"
    echo "  provision   Phase 3: Build Docker image"
    echo "  data        Phase 4: Verify data availability"
    echo "  run         Phase 5: Run DESeq2 analysis"
    echo "  validate    Phase 6: Show validation results"
    echo "  all         Run all executable phases (provision → validate)"
    echo ""
    exit 0
fi

"${@:-check}"