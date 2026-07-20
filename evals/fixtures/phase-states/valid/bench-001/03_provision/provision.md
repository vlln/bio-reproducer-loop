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

## Verification
- [x] R 4.3.0 installed and functional
- [x] DESeq2 library loadable
- [x] ggplot2 library loadable
- [x] apeglm library loadable

## Decisions
- Combined R + DESeq2 + ggplot2 + apeglm into a single bioconductor Docker image to reduce pull overhead
- Bioconductor RELEASE_3_18 corresponds to R 4.3.x and includes DESeq2 1.42.0