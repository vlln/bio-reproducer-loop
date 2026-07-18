#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
 * provision.nf — Phase 3: Tool Environment Deployment
 * Paper: bench-001 (DESeq2 Differential Expression Analysis)
 *
 * Deploys the R/Bioconductor environment for DESeq2 analysis.
 * Uses a custom Docker image built from bioconductor/bioconductor_docker:RELEASE_3_18.
 *
 * Note: Nextflow requires Java. If Java is not available, build and verify
 * the Docker image directly:
 *   docker build -t bio-reproducer:bench-001 -f Dockerfile .
 *   docker run --rm bio-reproducer:bench-001 Rscript verify.R
 */

params.outdir = "${launchDir}"
params.image_name = "bio-reproducer:bench-001"
params.dockerfile = "${launchDir}/Dockerfile"

process BUILD_IMAGE {
    publishDir "${params.outdir}/logs", mode: 'copy'

    output:
    stdout

    script:
    """
    echo "Building Docker image: ${params.image_name}"
    docker build -t ${params.image_name} -f ${params.dockerfile} ${launchDir}
    echo "Build complete: ${params.image_name}"
    """
}

process VERIFY_TOOLS {
    container params.image_name
    publishDir "${params.outdir}/logs", mode: 'copy'

    output:
    path "verification.txt"

    script:
    """
    Rscript -e '
    sink("verification.txt")
    cat("=== Verification Report ===\\n")
    cat("R version:", paste(R.version\$major, R.version\$minor, sep = "."), "\\n")

    tools <- list(
        DESeq2 = "1.42.0",
        ggplot2 = "3.5.0",
        apeglm = "1.24.0"
    )

    for (name in names(tools)) {
        expected <- tools[[name]]
        tryCatch({
            actual <- as.character(packageVersion(name))
            status <- if (actual == expected) "PASS" else "WARN (version mismatch)"
            cat(sprintf("%-12s expected=%-10s actual=%-10s [%s]\\n", name, expected, actual, status))
        }, error = function(e) {
            cat(sprintf("%-12s expected=%-10s [FAIL: not installed]\\n", name, expected))
        })
    }

    cat("\\n=== Library Test ===\\n")
    for (pkg in c("DESeq2", "ggplot2", "apeglm")) {
        tryCatch({
            library(pkg, character.only = TRUE)
            cat(pkg, "loaded successfully\\n")
        }, error = function(e) {
            cat(pkg, "FAILED to load:", conditionMessage(e), "\\n")
        })
    }

    cat("\\n=== DESeq2 Quick Test ===\\n")
    tryCatch({
        library("DESeq2")
        dds <- makeExampleDESeqDataSet(n = 100, m = 6)
        dds <- DESeq(dds)
        res <- results(dds)
        cat("DESeq2 workflow: PASS\\n")
        cat("Significant genes (padj < 0.05):", sum(res\$padj < 0.05, na.rm = TRUE), "\\n")
    }, error = function(e) {
        cat("DESeq2 workflow: FAIL -", conditionMessage(e), "\\n")
    })

    sink()
    '
    """
}

workflow {
    BUILD_IMAGE()
    VERIFY_TOOLS()
}