# Provision Report

## Environment
| Property | Value |
|----------|-------|
| Container Engine | Docker |

## Tools Provisioned
| Tool | Version | Image | Status |
|------|---------|-------|--------|
| R | 4.3.0 | rocker/r-base:4.3.0 | deployed |
| DESeq2 | 1.42.0 | bioconductor/bioconductor_docker:RELEASE_3_18 | deployed |
| ggplot2 | 3.5.0 | (included in bioconductor image) | deployed |
| apeglm | 1.24.0 | (included in bioconductor image) | deployed |
| clusterProfiler | (latest in RELEASE_3_18) | (included in bioconductor image) | deployed |
| pathview | (latest in RELEASE_3_18) | (included in bioconductor image) | deployed |

## Verification
- [x] R 4.3.0 installed and functional
- [x] DESeq2 library loadable
- [x] ggplot2 library loadable
- [x] apeglm library loadable
- [x] clusterProfiler library loadable
- [x] pathview library loadable

## Decisions
- Combined R + DESeq2 + ggplot2 + apeglm + clusterProfiler + pathview into a single bioconductor Docker image
- Bioconductor RELEASE_3_18 corresponds to R 4.3.x
- clusterProfiler and pathview versions are not specified in paper; using latest in RELEASE_3_18
- Required Bioconductor dependencies: org.Hs.eg.db (for gene ID conversion), enrichplot (for visualization)