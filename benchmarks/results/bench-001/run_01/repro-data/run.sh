#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Java home — adjust if your JDK is elsewhere
JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home}"

# Path to the Nextflow launcher — adjust if nextflow is on PATH
NEXTFLOW="${NEXTFLOW:-nextflow}"

check() {
    echo "=== Checking prerequisites ==="

    # Java
    if command -v java >/dev/null 2>&1; then
        echo "OK: java $(java -version 2>&1 | head -1)"
    elif [ -n "${JAVA_HOME:-}" ] && [ -x "$JAVA_HOME/bin/java" ]; then
        echo "OK: java found at JAVA_HOME ($JAVA_HOME)"
        export PATH="$JAVA_HOME/bin:$PATH"
    else
        echo "ERROR: Java 11+ not found. Install via: brew install openjdk@17"
        echo "  Then set JAVA_HOME: export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
        exit 1
    fi

    # Nextflow
    if command -v nextflow >/dev/null 2>&1; then
        echo "OK: nextflow $(nextflow -version 2>&1)"
    elif [ -x "$ROOT/../nextflow" ]; then
        echo "OK: nextflow found at project root"
        NEXTFLOW="$ROOT/../nextflow"
    else
        echo "ERROR: nextflow not found. Install via: brew install nextflow"
        echo "  Or use the launcher at the project root: $ROOT/../nextflow"
        exit 1
    fi

    # Docker
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            echo "OK: docker $(docker version --format '{{.Server.Version}}' 2>/dev/null || echo 'available')"
        else
            echo "ERROR: docker daemon not running. Start Docker and retry."
            exit 1
        fi
    else
        echo "ERROR: docker not found. Install Docker Desktop or OrbStack."
        exit 1
    fi

    # Disk space (need ~10 GB)
    local avail
    avail=$(df -k . | awk 'NR==2 {print $4}')
    if [ "$avail" -lt 10485760 ]; then
        echo "WARN: Low disk space (< 10 GB free). Docker image build may fail."
    else
        echo "OK: $(($avail / 1024 / 1024)) GB free disk space"
    fi

    echo ""
    echo "All prerequisites satisfied."
}

all() {
    echo "This will run all reproduction phases."
    echo "Estimated time: ~10–30 minutes (mostly Docker image build)"
    echo ""
    read -r -p "Continue? [y/N] " yn
    case "$yn" in
        [Yy]*) ;;
        *) echo "Aborted."; exit 0 ;;
    esac
    bootstrap
    provision
    data
    run
    validate
}

bootstrap() {
    echo "=== Phase 2: Bootstrap ==="
    echo "Checking system dependencies (Java, Nextflow, Docker)..."
    echo "See 02_bootstrap/bootstrap.md for the full environment report."
    echo ""
    check
    echo ""
    echo "Bootstrap complete. If any prerequisites were missing, install them and re-run."
}

provision() {
    echo "=== Phase 3: Provision ==="
    echo "Building the custom Docker image (bio-reproducer:bench-001) with R, DESeq2, ggplot2, and apeglm."
    echo "This may take 10–30 minutes depending on network speed."
    echo "See 03_provision/provision.md for details."
    echo ""

    cd "$ROOT/03_provision"
    JAVA_HOME="$JAVA_HOME" "$NEXTFLOW" run provision.nf -resume
    cd "$ROOT"
    echo ""
    echo "Provision complete. Docker image bio-reproducer:bench-001 is ready."
}

data() {
    echo "=== Phase 4: Data ==="
    echo "Staging the count matrix (counts.csv) from the benchmark entry."
    echo "This takes a few seconds."
    echo "See 04_data/data_manifest.md for details."
    echo ""

    cd "$ROOT/04_data"
    JAVA_HOME="$JAVA_HOME" "$NEXTFLOW" run data.nf -resume
    cd "$ROOT"
    echo ""
    echo "Data staging complete. Count matrix is at 04_data/raw_data/counts.csv."
}

run() {
    echo "=== Phase 5: Run ==="
    echo "Running the DESeq2 differential expression analysis pipeline."
    echo "This takes ~1 minute."
    echo "See 05_run/run_results.md for details."
    echo ""

    cd "$ROOT/05_run"
    JAVA_HOME="$JAVA_HOME" "$NEXTFLOW" run main.nf -resume \
        -with-report reports/report.html \
        -with-timeline reports/timeline.html \
        -with-trace reports/trace.txt
    cd "$ROOT"
    echo ""
    echo "Run complete. Results:"
    echo "  - DE results: 05_run/results/de_results.csv"
    echo "  - Normalized counts: 05_run/results/normalized_counts.csv"
    echo "  - Volcano plot: 05_run/figures/volcano_plot.png"
}

validate() {
    echo "=== Phase 6: Validate ==="
    echo "Reviewing validation results."
    echo "See 06_validate/report.md for the full validation report."
    echo ""

    if [ -f "$ROOT/06_validate/report.md" ]; then
        echo "Validation report found."
        # Extract verdict from the report
        grep -A1 "| Status " "$ROOT/06_validate/report.md" 2>/dev/null || true
        grep -A1 "| Reproducibility Score " "$ROOT/06_validate/report.md" 2>/dev/null || true
        echo ""
        echo "Open 06_validate/report.md for the complete validation report."
        if [ -f "$ROOT/06_validate/figure_comparison.md" ]; then
            echo "Open 06_validate/figure_comparison.md for figure comparison details."
        fi
    else
        echo "Validation report not found. Run the analysis first with: bash run.sh run"
    fi
}

"${@:-check}"