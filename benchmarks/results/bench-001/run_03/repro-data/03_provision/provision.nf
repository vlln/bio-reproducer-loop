#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
 * Phase 3: Provision — Custom R/Bioconductor container for bench-001
 *
 * Image: bench001-r-analysis:latest
 *   Based on: bioconductor/bioconductor_docker:RELEASE_3_18
 *   R: 4.3.3
 *   Bioconductor: 3.18
 *   Packages: DESeq2 1.42.1, ggplot2 4.0.3, apeglm 1.24.0
 */

params.outdir = "${launchDir}"

process VERIFY_TOOLS {
    container "bench001-r-analysis:latest"

    output:
    path "verify_results.json", emit: results

    script:
    """
    Rscript -e '
    pkgs <- c("DESeq2", "ggplot2", "apeglm")
    results <- list(R_version = R.version.string)
    for (pkg in pkgs) {
        ver <- as.character(packageVersion(pkg))
        cat(sprintf("%-12s %s\\n", pkg, ver))
        library(pkg, character.only = TRUE)
        results[[pkg]] <- ver
    }
    cat("All tools verified.\\n")
    jsonlite::write_json(results, "verify_results.json", auto_unbox = TRUE)
    '
    """
}

workflow {
    VERIFY_TOOLS()
}