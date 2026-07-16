#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Detect Java and set JAVA_HOME if needed
setup_java() {
    if [ -n "${JAVA_HOME:-}" ] && command -v java >/dev/null 2>&1; then
        return 0
    fi
    # Try Homebrew OpenJDK 17
    if [ -d "/opt/homebrew/opt/openjdk@17" ]; then
        export JAVA_HOME="/opt/homebrew/opt/openjdk@17"
        export PATH="$JAVA_HOME/bin:$PATH"
        return 0
    fi
    # Try system Java
    if [ -x "/usr/libexec/java_home" ]; then
        export JAVA_HOME="$(/usr/libexec/java_home 2>/dev/null || true)"
        if [ -n "$JAVA_HOME" ]; then
            export PATH="$JAVA_HOME/bin:$PATH"
            return 0
        fi
    fi
    echo "WARNING: JAVA_HOME not set and no Java runtime detected. Nextflow may fail."
    return 1
}

# Locate the Nextflow launcher script (project-local)
find_nextflow() {
    # Search for the nextflow script relative to repro-data root
    if [ -x "$ROOT/../../../../../nextflow" ]; then
        echo "$ROOT/../../../../../nextflow"
    elif command -v nextflow >/dev/null 2>&1; then
        echo "nextflow"
    else
        echo ""
    fi
}

check() {
    echo "=== Checking Prerequisites ==="
    echo ""

    # Java
    setup_java
    if command -v java >/dev/null 2>&1; then
        echo "[OK] Java: $(java -version 2>&1 | head -1)"
    else
        echo "[FAIL] Java not found. Install OpenJDK 17+ (e.g., brew install openjdk@17)"
        exit 1
    fi

    # Nextflow
    NF=$(find_nextflow)
    if [ -n "$NF" ]; then
        echo "[OK] Nextflow: $($NF -version 2>&1 | head -1)"
    else
        echo "[FAIL] Nextflow not found. Ensure the project-local 'nextflow' script is present."
        exit 1
    fi

    # Container runtime
    if command -v docker >/dev/null 2>&1; then
        echo "[OK] Docker: $(docker --version 2>&1)"
    elif command -v singularity >/dev/null 2>&1; then
        echo "[OK] Singularity: $(singularity --version 2>&1)"
    else
        echo "[FAIL] Neither Docker nor Singularity found. Install one to proceed."
        exit 1
    fi

    # Disk space (check for at least 2 GB free)
    if command -v df >/dev/null 2>&1; then
        AVAIL=$(df -k . | tail -1 | awk '{print $4}')
        if [ "$AVAIL" -lt 2097152 ]; then
            echo "[WARN] Less than 2 GB disk space available. Container pull may fail."
        else
            echo "[OK] Disk space: $((AVAIL / 1024 / 1024)) GB available"
        fi
    fi

    echo ""
    echo "All prerequisites satisfied."
}

all() {
    echo "This will run all reproduction phases: bootstrap, provision, data, run, validate."
    echo "Estimated time: ~5 minutes (first run), ~5 seconds (cached re-run)."
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
    echo "Environment inventory was already collected during the initial reproduction run."
    echo "See 02_bootstrap/bootstrap.md for the full report."
    echo ""
    echo "Running prerequisite check..."
    check
}

provision() {
    echo "=== Phase 3: Provision ==="
    echo "Building the custom Docker image with R, DESeq2, ggplot2, and apeglm."
    echo "Estimated time: ~5 minutes (first pull + build), ~10 seconds (cached)."
    echo ""

    setup_java
    NF=$(find_nextflow)
    if [ -z "$NF" ]; then
        echo "ERROR: Nextflow not found."
        exit 1
    fi

    cd "$ROOT/03_provision"
    "$NF" run provision.nf -resume
    echo ""
    echo "Provision complete. See 03_provision/provision.md for details."
}

data() {
    echo "=== Phase 4: Data ==="
    echo "Staging the count matrix (counts.csv) for analysis."
    echo "Estimated time: ~2 seconds."
    echo ""

    setup_java
    NF=$(find_nextflow)
    if [ -z "$NF" ]; then
        echo "ERROR: Nextflow not found."
        exit 1
    fi

    cd "$ROOT/04_data"
    "$NF" run data.nf -resume
    echo ""
    echo "Data staging complete. See 04_data/data_manifest.md for details."
}

run() {
    echo "=== Phase 5: Run ==="
    echo "Running DESeq2 differential expression analysis and generating the volcano plot."
    echo "Estimated time: ~30 seconds."
    echo ""

    setup_java
    NF=$(find_nextflow)
    if [ -z "$NF" ]; then
        echo "ERROR: Nextflow not found."
        exit 1
    fi

    cd "$ROOT/05_run"
    "$NF" run main.nf -resume \
        -with-report reports/run_report.html \
        -with-timeline reports/timeline.html \
        -with-trace reports/trace.txt
    echo ""
    echo "Analysis complete. See 05_run/run_results.md for details."
    echo "Results: 05_run/results/"
    echo "Figures: 05_run/figures/"
}

validate() {
    echo "=== Phase 6: Validate ==="
    echo "Reviewing validation results from the reproduction run."
    echo ""

    if [ -f "$ROOT/06_validate/report.md" ]; then
        echo "Validation report: 06_validate/report.md"
        echo "Figure comparison: 06_validate/figure_comparison.md"
        echo ""
        # Extract and display the verdict
        echo "--- Verdict Summary ---"
        grep -E "^\| Status" "$ROOT/06_validate/report.md" || true
        grep "Reproducibility Score" "$ROOT/06_validate/report.md" || true
        echo ""
        echo "See 06_validate/report.md for the full validation report."
    else
        echo "Validation report not found. Run 'bash run.sh run' first."
        exit 1
    fi
}

# Default action: show usage
if [ $# -eq 0 ]; then
    echo "Usage: run.sh <command>"
    echo ""
    echo "Commands:"
    echo "  check       Check system prerequisites (nextflow, docker, java, disk)"
    echo "  all         Run all reproduction phases (provision → data → run → validate)"
    echo "  bootstrap   Show bootstrap report and run prerequisite check"
    echo "  provision   Build/pull the Docker container (Phase 3)"
    echo "  data        Stage input data (Phase 4)"
    echo "  run         Run DESeq2 analysis and generate volcano plot (Phase 5)"
    echo "  validate    Display validation report (Phase 6)"
    exit 0
fi

"${@}"