#!/usr/bin/env bash
#
# Phase 5: Run DESeq2 Analysis Pipeline
# Paper: Differential Expression Analysis of Synthetic Gene Response to Treatment
#
# Runs the analysis via Docker using the provisioned bio-reproducer:bench-001 image.
# Nextflow is not available (no Java runtime), so the analysis is executed directly
# via docker run with the R analysis script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DATA="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE="bio-reproducer:bench-001"

echo "=== Phase 5: Run DESeq2 Analysis ==="
echo "Image: ${IMAGE}"
echo "Input: ${REPRO_DATA}/04_data/raw_data/counts.csv"
echo "Output: ${SCRIPT_DIR}/results/"
echo ""

# Step 1: Container network check
echo "[Check] Testing container network connectivity..."
if docker run --rm "${IMAGE}" Rscript -e 'cat("R OK\n"); if(curl::has_internet()) cat("Internet: OK\n") else cat("Internet: UNAVAILABLE\n")' 2>&1; then
    echo "[Check] Container network check passed"
else
    echo "[Check] Container network check completed (curl may not be installed)"
fi
echo ""

# Step 2: Run analysis
echo "[Run] Starting DESeq2 analysis..."
docker run --rm \
    --platform linux/arm64 \
    -v "${REPRO_DATA}:/data:ro" \
    -v "${SCRIPT_DIR}/results:/data/05_run/results" \
    -v "${SCRIPT_DIR}/figures:/data/05_run/figures" \
    "${IMAGE}" \
    Rscript /data/05_run/analysis.R /data/04_data/raw_data /data/05_run

EXIT_CODE=$?
echo ""
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "[Run] Analysis completed successfully"
else
    echo "[Run] Analysis failed with exit code ${EXIT_CODE}"
fi

exit ${EXIT_CODE}