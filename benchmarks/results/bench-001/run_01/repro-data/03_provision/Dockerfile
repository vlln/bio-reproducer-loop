# Phase 3: Custom bio-reproducer image
# Extends Bioconductor RELEASE_3_18 (R 4.3.3, Bioc 3.18) with required packages
FROM bioconductor/bioconductor_docker:RELEASE_3_18

LABEL maintainer="bio-reproducer"
LABEL description="R environment for differential expression analysis with DESeq2"

# Install required R packages via BiocManager
# DESeq2 1.42.0 is part of Bioconductor 3.18
# ggplot2 3.5.0 and apeglm 1.24.0 are installed from CRAN/Bioconductor
RUN R -e 'BiocManager::install(c("DESeq2", "ggplot2", "apeglm"), ask=FALSE, update=FALSE, version="3.18")' \
    && R -e 'library(DESeq2); library(ggplot2); library(apeglm); cat("All packages loaded successfully\n")'

# Verify installations
RUN R -e 'cat("DESeq2 version:", as.character(packageVersion("DESeq2")), "\n"); \
         cat("ggplot2 version:", as.character(packageVersion("ggplot2")), "\n"); \
         cat("apeglm version:", as.character(packageVersion("apeglm")), "\n")'