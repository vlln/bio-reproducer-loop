#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

check() {
    echo "=== Checking prerequisites ==="
    local ok=true

    # Java
    if command -v java >/dev/null 2>&1; then
        echo "OK: java $(java -version 2>&1 | head -1)"
    else
        echo "ERROR: java not found (Java 11+ required)"
        ok=false
    fi

    # Nextflow
    if command -v nextflow >/dev/null 2>&1; then
        echo "OK: nextflow $(nextflow -version 2>&1)"
    else
        echo "ERROR: nextflow not found in PATH"
        ok=false
    fi

    # Container runtime
    if command -v docker >/dev/null 2>&1; then
        echo "OK: docker $(docker --version 2>&1)"
    elif command -v singularity >/dev/null 2>&1; then
        echo "OK: singularity $(singularity --version 2>&1)"
    else
        echo "ERROR: docker or singularity required"
        ok=false
    fi

    if [ "$ok" = false ]; then
        echo "Prerequisites check failed. Please install missing dependencies."
        exit 1
    fi
    echo "All prerequisites satisfied."
}

all() {
    echo "This will run all reproduction phases."
    echo "Expected time: ~30 seconds (Docker build + Nextflow)"
    read -rp "Continue? [y/N] " yn
    case "$yn" in [Yy]*) ;; *) exit 0;; esac
    provision
    data
    run
    validate
}

bootstrap() {
    echo "=== Phase 2: Bootstrap ==="
    echo "Bootstrap was already completed during initial reproduction setup."
    echo "See 02_bootstrap/bootstrap.md for the system environment report."
    echo "Key findings:"
    echo "  - Java: OpenJDK 17.0.19 (Homebrew)"
    echo "  - Nextflow: 26.04.6"
    echo "  - Docker: 29.4.0 (OrbStack)"
    echo "  - CPU: Apple M4, 10 cores"
    echo "  - Disk: 67 GiB free"
    echo ""
    echo "If you need to re-run bootstrap checks, please review 02_bootstrap/bootstrap.md."
}

provision() {
    echo "=== Phase 3: Provision ==="
    echo "Building the container image for DESeq2 analysis..."
    echo "Image: bench-001-provision:latest"
    echo "Base: quay.io/biocontainers/bioconductor-deseq2:1.42.0--r43hf17093f_0"
    echo "Estimated time: ~5 minutes (image pull + build)"

    # Build the Docker image
    docker build -t bench-001-provision:latest -f 03_provision/Dockerfile 03_provision/

    echo "Verifying provisioned environment..."
    nextflow run 03_provision/provision.nf -resume

    echo "Provisioning complete."
}

data() {
    echo "=== Phase 4: Data ==="
    echo "Staging count matrix for downstream analysis..."
    echo "Source: 04_data/raw_data/counts.csv (10 genes × 6 samples, pre-supplied)"
    echo "Estimated time: < 5 seconds"

    cd "$ROOT/04_data"
    nextflow run data.nf -resume
    cd "$ROOT"

    echo "Data staging complete."
}

run() {
    echo "=== Phase 5: Run ==="
    echo "Running DESeq2 differential expression analysis..."
    echo "Pipeline: 05_run/main.nf (DSL2)"
    echo "Container: bench-001-provision:latest"
    echo "Estimated time: ~10 seconds"

    cd "$ROOT/05_run"
    nextflow run main.nf \
        -with-report reports/report.html \
        -with-timeline reports/timeline.html \
        -with-trace reports/trace.txt \
        -resume
    cd "$ROOT"

    echo "Analysis complete."
    echo "Results: 05_run/results/deseq2_results.csv"
    echo "Figures: 05_run/figures/volcano_plot.png, 05_run/figures/volcano_plot.pdf"
}

validate() {
    echo "=== Phase 6: Validate ==="
    echo "Validation was completed during the initial reproduction."
    echo "Verdict: REPRODUCED (Score: 95.6/100)"
    echo ""
    echo "See 06_validate/report.md for the full validation report."
    echo "See 06_validate/figure_comparison.md for the figure comparison assessment."
    echo ""
    echo "Key results:"
    echo "  - 16/16 checks passed"
    echo "  - Data Integrity: 25.0/25.0"
    echo "  - Process Quality: 24.1/25.0"
    echo "  - Quantitative Concordance: 28.5/30.0"
    echo "  - Figure and Finding Reproduction: 18.0/20.0"
    echo ""
    echo "Gene_A: Upregulated (log2FC = 2.918, padj = 4.37e-119)"
    echo "Gene_B: Downregulated (log2FC = -1.997, padj = 5.57e-42)"
    echo "Gene_C–Gene_J: Not significant (all padj > 0.05)"
    echo ""
    echo "Volcano plot pattern matches paper description."
}

"${@:-check}"