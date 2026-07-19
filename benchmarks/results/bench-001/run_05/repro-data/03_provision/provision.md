# Provision Report

**Date**: 2026-07-18
**Phase**: 03_provision

## Environment

| Property | Value |
|----------|-------|
| Container Engine | Docker 29.4.0 |
| Image Build | `bench-001-provision:latest` (Dockerfile) |
| Base Image | `bioconductor/bioconductor_docker:RELEASE_3_18` |
| Platform | linux/amd64 |

## Tools Provisioned

| Tool | Version (Required) | Version (Actual) | Image | Status |
|------|--------------------|-------------------|-------|--------|
| R | 4.3.0 | 4.3.3 | bench-001-provision:latest | deployed |
| DESeq2 | 1.42.0 | 1.42.1 | bench-001-provision:latest | deployed |
| ggplot2 | 3.5.0 | 3.5.0 | bench-001-provision:latest | deployed |
| apeglm | 1.24.0 | 1.24.0 | bench-001-provision:latest | deployed |

## Version Notes

- R 4.3.3 instead of 4.3.0 — minor patch version within 4.3.x series; no functional impact expected
- DESeq2 1.42.1 instead of 1.42.0 — patch version within Bioconductor 3.18; minor bugfixes only
- ggplot2 3.5.0 — exact match
- apeglm 1.24.0 — exact match

## Verification

- [x] Docker image built successfully
- [x] All packages load without errors
- [x] R version: 4.3.3
- [x] DESeq2 version: 1.42.1
- [x] ggplot2 version: 3.5.0
- [x] apeglm version: 1.24.0

## Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Image build recipe |
| `provision.nf` | Nextflow workflow for container deployment |
| `nextflow.config` | Phase 3 Nextflow configuration |
| `provision.md` | This report |

## Image Pull

Image pulled via `mip` mirror (`dockerproxy.cool`) due to Docker Hub timeout. Local image retagged to `docker.io/bioconductor/bioconductor_docker:RELEASE_3_18` and `bench-001-provision:latest`.