# Provision Report

## Environment
| Property | Value |
|----------|-------|
| Container Engine | Docker |

## Tools Provisioned
| Tool | Version | Image | Status |
|------|---------|-------|--------|
| R | ≥ 4.3.0 | bioconductor/bioconductor_docker:latest | deployed |
| DESeq2 | latest | (included in bioconductor image) | deployed |
| airway | latest | (Bioconductor data package) | deployed |

## Verification
- [x] R installed and functional
- [x] DESeq2 library loadable
- [x] airway data package loadable
- [x] GSE52778 count data accessible via `airway` package

## Decisions
- Single bioconductor Docker image provides all required tools (R + DESeq2 + airway)
- Paired design `~ cell + dex` accounts for cell line as blocking factor
- No external data download needed — `airway` package bundles the count matrix
- Data is small (~10 MB), computation time < 1 minute