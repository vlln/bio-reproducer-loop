#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

check() {
    echo "=== Checking Prerequisites ==="
    echo ""

    # Java
    if command -v java >/dev/null 2>&1; then
        echo "[OK] Java: $(java -version 2>&1 | head -1)"
    else
        echo "[ERROR] Java not found. Install Java 11+: https://adoptium.net/"
        exit 1
    fi

    # Nextflow
    if command -v nextflow >/dev/null 2>&1; then
        echo "[OK] Nextflow: $(nextflow -version 2>&1)"
    else
        echo "[ERROR] Nextflow not found. Install: curl -s https://get.nextflow.io | bash"
        exit 1
    fi

    # Container runtime
    if command -v docker >/dev/null 2>&1; then
        echo "[OK] Docker: $(docker --version)"
    elif command -v singularity >/dev/null 2>&1; then
        echo "[OK] Singularity: $(singularity --version)"
    elif command -v apptainer >/dev/null 2>&1; then
        echo "[OK] Apptainer: $(apptainer --version)"
    else
        echo "[ERROR] Docker, Singularity, or Apptainer required."
        exit 1
    fi

    # Disk space
    local available
    available=$(df -BM . | awk 'NR==2 {print $4}' | sed 's/M//')
    if [ "$available" -lt 500 ]; then
        echo "[WARN] Disk space: ${available} MB available (< 500 MB may be insufficient)"
    else
        echo "[OK] Disk space: ${available} MB available"
    fi

    echo ""
    echo "All prerequisites satisfied."
}

all() {
    echo "This will run all reproduction phases."
    echo "Expected time: < 1 minute"
    echo ""
    read -rp "Continue? [y/N] " yn
    case "$yn" in
        [Yy]*) ;;
        *) exit 0 ;;
    esac
    bootstrap
    provision
    data
    run
    validate
}

bootstrap() {
    echo "=== Phase 2: Bootstrap ==="
    echo "Installing system dependencies (Java, Nextflow)..."
    echo ""
    echo "Bootstrap is already complete on this system."
    echo "See 02_bootstrap/bootstrap.md for the environment status report."
    echo ""
    echo "If Java or Nextflow are missing, install them manually:"
    echo "  Java: https://adoptium.net/"
    echo "  Nextflow: curl -s https://get.nextflow.io | bash"
}

provision() {
    echo "=== Phase 3: Provision ==="
    echo "Building/pulling the Docker container with R and DESeq2..."
    echo "Expected time: 5-10 minutes (first run; image download)"
    echo ""

    if [ -f "03_provision/Dockerfile" ]; then
        cd "$ROOT/03_provision"
        nextflow run provision.nf -resume
        cd "$ROOT"
    else
        echo "ERROR: 03_provision/Dockerfile not found."
        exit 1
    fi
}

data() {
    echo "=== Phase 4: Data ==="
    echo "Preparing the count matrix (counts.csv)..."
    echo "Expected time: < 1 second"
    echo ""

    if [ -f "04_data/data.nf" ]; then
        cd "$ROOT/04_data"
        nextflow run data.nf -resume
        cd "$ROOT"
    else
        echo "ERROR: 04_data/data.nf not found."
        exit 1
    fi
}

run() {
    echo "=== Phase 5: Run ==="
    echo "Running DESeq2 differential expression analysis..."
    echo "Expected time: < 1 minute"
    echo ""

    if [ -f "05_run/main.nf" ]; then
        cd "$ROOT/05_run"
        nextflow run main.nf -resume \
            -with-report reports/report.html \
            -with-timeline reports/timeline.html \
            -with-trace reports/trace.txt
        cd "$ROOT"
    else
        echo "ERROR: 05_run/main.nf not found."
        exit 1
    fi
}

validate() {
    echo "=== Phase 6: Validate ==="
    echo "Validating reproduction results..."
    echo ""

    if [ -f "06_validate/report.md" ]; then
        echo "Validation report already exists: 06_validate/report.md"
        echo ""

        # Extract and display the verdict
        if grep -q "REPRODUCED" "06_validate/report.md" 2>/dev/null; then
            echo "Verdict: REPRODUCED"
        elif grep -q "PARTIAL" "06_validate/report.md" 2>/dev/null; then
            echo "Verdict: PARTIAL"
        else
            echo "Verdict: see 06_validate/report.md for details"
        fi

        echo ""
        echo "See 06_validate/report.md for the full validation report."
        echo "See 06_validate/figure_comparison.md for the figure comparison."
    else
        echo "Validation report not found. Re-run Phase 5 first."
        exit 1
    fi
}

"${@:-check}"