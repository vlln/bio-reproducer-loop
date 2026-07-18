#!/usr/bin/env nextflow
//
// main.nf — DESeq2 Differential Expression Analysis Pipeline
// Paper: Differential Expression Analysis of Synthetic Gene Response to Treatment
// DOI: 10.1234/bench.001
//
// This workflow orchestrates the R-based DESeq2 analysis pipeline.
// Note: Nextflow is not executable on this system (no Java runtime).
// The analysis was executed directly via docker run (see run.sh).
// This file is retained as documentation of the intended workflow structure.

nextflow.enable.dsl = 2

params.input_dir = "${projectDir}/../04_data/raw_data"
params.output_dir = "${projectDir}/results"
params.container_image = "bio-reproducer:bench-001"
params.r_script = "${projectDir}/analysis.R"

process DESEQ2_ANALYSIS {
    container params.container_image

    publishDir "${params.output_dir}", mode: 'copy'

    input:
    path counts_csv from "${params.input_dir}/counts.csv"
    path r_script from params.r_script

    output:
    path "results/*"
    path "figures/*"

    script:
    """
    mkdir -p results figures
    Rscript ${r_script} ${params.input_dir} ${projectDir}
    """
}

workflow {
    DESEQ2_ANALYSIS()
}