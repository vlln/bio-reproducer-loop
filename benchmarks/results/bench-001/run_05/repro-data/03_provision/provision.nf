#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
 * Phase 3: Provision — Deploy Bioconductor container with R, DESeq2, ggplot2, apeglm
 */

params.outdir = "${launchDir}"

process PULL_BIOCONDUCTOR {
    label 'bioconductor'
    
    output:
    stdout
    
    """
    echo "Image: ${params.bioconductor_image}"
    echo "Image pulled and available"
    """
}

process VERIFY_R {
    label 'bioconductor'
    
    output:
    stdout
    
    """
    R --version
    """
}

process VERIFY_PACKAGES {
    label 'bioconductor'
    
    output:
    stdout
    
    """
    Rscript -e '
    cat("R version:", paste(R.version\$major, R.version\$minor, sep="."), "\n")
    cat("DESeq2:", as.character(packageVersion("DESeq2")), "\n")
    cat("ggplot2:", as.character(packageVersion("ggplot2")), "\n")
    cat("apeglm:", as.character(packageVersion("apeglm")), "\n")
    '
    """
}

workflow {
    PULL_BIOCONDUCTOR()
    VERIFY_R()
    VERIFY_PACKAGES()
}