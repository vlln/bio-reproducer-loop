#!/usr/bin/env nextflow

/*
 * Phase 4: Data Acquisition
 * bench-002 run_01
 *
 * Copies the local count matrix (counts.csv) from the benchmark entry
 * to the analysis working directory. No external downloads are required:
 *   - GSE99999 is a wrong accession (unrelated study)
 *   - GitHub repository is a dead URL (HTTP 404)
 *   - Supplementary Table S2 is missing but regenerable
 *   - KEGG pathway data is fetched automatically by pathview at runtime
 */

params.entry_dir = "${launchDir}/../../../../entries/bench-002"
params.output_dir = "${launchDir}"

process COPY_COUNTS {
    publishDir "${params.output_dir}/raw_data", mode: 'copy'

    input:
    path counts_csv from "${params.entry_dir}/data/counts.csv"

    output:
    path "counts.csv"

    """
    cp "${counts_csv}" counts.csv
    """
}

workflow {
    COPY_COUNTS()
}