FROM bioconductor/bioconductor_docker:3.18-R-4.3.3

# Install packages in order: ggplot2 first (pin version), then Bioconductor packages
RUN Rscript -e ' \
    install.packages("remotes", repos="https://p3m.dev/cran/2024-04-23"); \
    remotes::install_version("ggplot2", version="3.5.0", repos="https://p3m.dev/cran/2024-04-23", upgrade="never")' \
    && Rscript -e 'BiocManager::install(c("DESeq2", "apeglm"), update=FALSE, ask=FALSE)' \
    && rm -rf /tmp/downloaded_packages /tmp/Rtmp*

# Verify installations
RUN Rscript -e ' \
    pkgs <- c("DESeq2", "ggplot2", "apeglm"); \
    for (pkg in pkgs) { \
        ver <- as.character(packageVersion(pkg)); \
        cat(sprintf("%-12s %s\n", pkg, ver)); \
        library(pkg, character.only = TRUE); \
    }; \
    cat("All packages verified.\n"); \
    '