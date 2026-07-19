FROM bioconductor/bioconductor_docker:RELEASE_3_18

LABEL description="R environment for DESeq2 differential expression analysis"
LABEL paper="bench-001"
LABEL r_version="4.3.3"
LABEL bioc_version="3.18"

# Install Bioconductor packages (DESeq2, apeglm) and CRAN package (ggplot2)
RUN Rscript -e 'BiocManager::install(c("DESeq2", "apeglm"), ask = FALSE, update = FALSE)' \
    && Rscript -e 'install.packages("ggplot2", repos = "https://cloud.r-project.org")' \
    && Rscript -e 'BiocManager::install(ask = FALSE, update = FALSE)' \
    && rm -rf /tmp/downloaded_packages /tmp/Rtmp*

# Verify installed packages
RUN Rscript -e ' \
    cat("R version:", paste(R.version$major, R.version$minor, sep = "."), "\n"); \
    for (pkg in c("DESeq2", "ggplot2", "apeglm")) { \
        v <- as.character(packageVersion(pkg)); \
        cat(pkg, "version:", v, "\n"); \
    }'