#!/usr/bin/env nextflow
// Phase 3: Tool container environment provisioning
// Builds a custom Docker image extending bioconductor/bioconductor_docker:RELEASE_3_18
// with DESeq2, ggplot2, and apeglm installed.

nextflow.enable.dsl = 2

params.outdir = "${projectDir}"

def custom_image = 'bio-reproducer:bench-001'

process BUILD_IMAGE {
    label 'provision'
    containerOptions '--entrypoint=""'
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: '*.log'
    output:
    path "build.log", emit: build_log
    path "verify.log", emit: verify_log

    script:
    """
    echo "=== Building ${custom_image} ==="
    docker build -t ${custom_image} -f ${params.outdir}/Dockerfile ${params.outdir} 2>&1 | tee build.log

    echo "=== Verifying ${custom_image} ==="
    docker run --rm ${custom_image} R -e 'cat("DESeq2 version:", as.character(packageVersion("DESeq2")), "\\n"); cat("ggplot2 version:", as.character(packageVersion("ggplot2")), "\\n"); cat("apeglm version:", as.character(packageVersion("apeglm")), "\\n")' 2>&1 | tee verify.log
    """
}

workflow {
    BUILD_IMAGE()
}