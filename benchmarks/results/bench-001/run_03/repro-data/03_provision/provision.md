# Provision Report

## Environment

| Property | Value |
|----------|-------|
| Container Engine | Docker 29.4.0 (OrbStack) |
| Base Image | bioconductor/bioconductor_docker:RELEASE_3_18 |
| Custom Image | bio-reproducer:bench-001 |
| R Version | 4.3.3 |
| Bioconductor Version | 3.18 |
| Architecture | aarch64 (Apple Silicon) |

## Tools Provisioned

| Tool | Version (Expected) | Version (Actual) | Image | Status |
|------|-------------------|-------------------|-------|--------|
| R | ≥ 4.3.0 | 4.3.3 | bio-reproducer:bench-001 | deployed |
| DESeq2 | 1.42.0 | 1.42.1 | bio-reproducer:bench-001 | deployed |
| ggplot2 | 3.5.0 | 3.5.0 | bio-reproducer:bench-001 | deployed |
| apeglm | 1.24.0 | 1.24.0 | bio-reproducer:bench-001 | deployed |

## Version Notes

- **DESeq2 1.42.1 vs 1.42.0**: Bioconductor 3.18 ships DESeq2 1.42.1, the latest patch in the 1.42.x series. This is functionally equivalent to 1.42.0 — the minor version bump is a patch-level update within the same Bioconductor release. No API or behavioral changes between 1.42.0 and 1.42.1.
- **R 4.3.3 vs 4.3.0**: R 4.3.3 is a patch release within the R 4.3.x series. Fully compatible.

## Verification

- [x] Docker image built successfully (6.08 GB)
- [x] R 4.3.3 available and functional
- [x] Bioconductor 3.18 loaded
- [x] DESeq2 library loaded and functional
- [x] ggplot2 library loaded and functional
- [x] apeglm library loaded and functional
- [x] DESeq2 workflow test passed (makeExampleDESeqDataSet → DESeq → results)

## Nextflow Status

Nextflow was not used for deployment because Java Runtime is not available on this system (`/usr/bin/java` is a stub). The Docker image was built and verified directly. The `provision.nf` workflow file is provided as documentation of the intended deployment workflow but could not be executed.

## Artifacts

| File | Description |
|------|-------------|
| `Dockerfile` | Custom image extending bioconductor/bioconductor_docker:RELEASE_3_18 |
| `provision.nf` | Nextflow workflow definition (not executed, Java unavailable) |
| `provision.md` | This report |