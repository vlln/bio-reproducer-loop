#!/usr/bin/env nextflow

/**
 * Phase 4: Data Acquisition
 *
 * Copies the count matrix (counts.csv) from the benchmark entry
 * into the run's raw_data directory. The data is a single local file;
 * no external downloads are required.
 *
 * Blocked sources:
 *   - GSE99999: resolves to unrelated study (Phase 1 conflict)
 *   - GitHub analysis script: HTTP 404 (reconstructed in Phase 5)
 */

params.input_counts = "${projectDir}/../benchmarks/entries/bench-001/data/counts.csv"
params.output_dir  = "${launchDir}/04_data/raw_data"

process COPY_COUNTS {
    publishDir params.output_dir, mode: 'copy', overwrite: false

    input:
    path counts_csv

    output:
    path "counts.csv", emit: counts

    script:
    """
    cp ${counts_csv} counts.csv
    echo "Copied counts.csv: \$(wc -l < counts.csv) lines, \$(wc -c < counts.csv) bytes"
    """
}

workflow {
    Channel.fromPath(params.input_counts)
        | COPY_COUNTS
}