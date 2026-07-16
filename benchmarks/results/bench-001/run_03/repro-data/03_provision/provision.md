# Provision Report — bench-001 run_03

**Date**: 2026-07-16
**Paper**: bench-001 — Differential Expression Analysis of Synthetic Gene Response to Treatment
**Plan Reference**: `01_plan/plan.md`
**Bootstrap Reference**: `02_bootstrap/bootstrap.md`

## Environment

| Property | Value |
|----------|-------|
| Container Engine | Docker (OrbStack) |
| Docker Context | orbstack |
| Base Image | bioconductor/bioconductor_docker:RELEASE_3_18 |
| Custom Image | bench001-r-analysis:latest |
| Platform | linux/arm64 |

## Tools Provisioned

| Tool | Required Version | Actual Version | Image | Status |
|------|-----------------|----------------|-------|--------|
| R | 4.3.0 | 4.3.3 | bench001-r-analysis:latest | deployed |
| DESeq2 | 1.42.0 | 1.42.1 | bench001-r-analysis:latest | deployed |
| ggplot2 | 3.5.0 | 4.0.3 | bench001-r-analysis:latest | deployed |
| apeglm | 1.24.0 | 1.24.0 | bench001-r-analysis:latest | deployed |

## Version Deviations

| Tool | Required | Actual | Impact |
|------|----------|--------|--------|
| R | 4.3.0 | 4.3.3 | Patch version bump; backward compatible |
| DESeq2 | 1.42.0 | 1.42.1 | Patch version bump; backward compatible |
| ggplot2 | 3.5.0 | 4.0.3 | Major version bump; backward compatible API for volcano plot use case |

## Verification

- [x] R 4.3.3 installed and functional
- [x] DESeq2 1.42.1 loads correctly
- [x] ggplot2 4.0.3 loads correctly
- [x] apeglm 1.24.0 loads correctly
- [x] Nextflow workflow `provision.nf` executes successfully
- [x] Docker image `bench001-r-analysis:latest` built and cached (6.09 GB)

## Notes

- The Bioconductor base image (`RELEASE_3_18`) does not include DESeq2/apeglm pre-installed; these were installed via BiocManager during the Docker build.
- ggplot2 was installed from CRAN, which provided version 4.0.3 instead of the paper's specified 3.5.0. The API is backward compatible for the volcano plot use case.
- Docker Hub access is blocked by the proxy; `--pull=never` is configured in `nextflow.config` to use the local image only.
- The custom image is built as `bench001-r-analysis:latest` and must be available locally for downstream phases.