#!/usr/bin/env nextflow

// Phase 3: Provision — Tool Container Environment
// bench-002: Transcriptomic Profiling of Drug Response
//
// NOTE: This workflow is provided as documentation of the intended deployment
// strategy. Docker daemon was not running during this run (OrbStack not started),
// so packages were installed directly into the system R library instead.
// The workflow is retained for reproducibility and future containerized runs.

params.outdir = "$projectDir/../../.."

process install_r_packages {
    label 'r_packages'
    publishDir "${params.outdir}/03_provision", mode: 'copy'

    output:
    path "install.log", emit: log

    script:
    """
    Rscript -e '
    log <- function(msg) cat(paste0("[", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "] ", msg, "\\n"))
    log("Starting R package installation")
    if (!require("BiocManager")) { log("ERROR: BiocManager not available"); quit(status = 1) }
    log(paste("BiocManager version:", as.character(packageVersion("BiocManager"))))
    pkgs <- c("clusterProfiler", "pathview", "org.Hs.eg.db")
    installed <- installed.packages()
    missing <- pkgs[!pkgs %in% rownames(installed.packages())]
    if (length(missing) > 0) {
      log(paste("Installing:", paste(missing, collapse = ", ")))
      BiocManager::install(missing, update = FALSE, ask = FALSE)
    }
    for (p in c(pkgs, "DESeq2", "ggplot2", "apeglm")) {
      if (require(p, character.only = TRUE, quietly = TRUE)) {
        log(paste("OK:", p, as.character(packageVersion(p))))
      } else {
        log(paste("FAIL:", p))
      }
    }
    log("Done")
    ' > install.log 2>&1
    """
}

workflow {
    install_r_packages()
}