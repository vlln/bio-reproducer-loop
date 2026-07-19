FROM bioconductor/bioconductor_docker:RELEASE_3_18

# Install DESeq2 and apeglm from Bioconductor 3.18
# Install ggplot2 from CRAN
RUN Rscript -e ' \
  BiocManager::install(c("DESeq2", "apeglm", "ggplot2"), \
    version = "3.18", ask = FALSE, update = FALSE) \
'

# Verify installations
RUN Rscript -e ' \
  cat("R:", paste(R.version$major, R.version$minor, sep="."), "\n"); \
  cat("DESeq2:", as.character(packageVersion("DESeq2")), "\n"); \
  cat("ggplot2:", as.character(packageVersion("ggplot2")), "\n"); \
  cat("apeglm:", as.character(packageVersion("apeglm")), "\n") \
'