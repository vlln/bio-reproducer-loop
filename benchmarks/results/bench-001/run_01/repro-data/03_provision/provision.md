# Provision Report

## Environment

| Property | Value |
|----------|-------|
| Container Engine | Docker (OrbStack 29.4.0) |
| Base Image | bioconductor/bioconductor_docker:RELEASE_3_18 |
| Custom Image | bio-reproducer:bench-001 |
| Image ID | 7fa0dc5c4479 |
| Image Size | 6.08 GB |

## Build Methodology

A custom Docker image (`bio-reproducer:bench-001`) was built extending the Bioconductor RELEASE_3_18 base image. Required R packages were installed via `BiocManager::install()` during the build, ensuring all dependencies are baked into the image. The Dockerfile is located at `03_provision/Dockerfile`.

## Tools Provisioned

| Tool | Version (Paper) | Version (Deployed) | Image | Status |
|------|-----------------|---------------------|-------|--------|
| R | 4.3.0 | 4.3.3 | bio-reproducer:bench-001 | ✅ Deployed |
| DESeq2 | 1.42.0 | 1.42.1 | bio-reproducer:bench-001 | ✅ Deployed |
| ggplot2 | 3.5.0 | 3.5.0 | bio-reproducer:bench-001 | ✅ Deployed |
| apeglm | 1.24.0 | 1.24.0 | bio-reproducer:bench-001 | ✅ Deployed |

## Version Discrepancies

| Package | Paper | Deployed | Assessment |
|---------|-------|----------|------------|
| R | 4.3.0 | 4.3.3 | Minor patch version; no functional impact |
| DESeq2 | 1.42.0 | 1.42.1 | Minor patch version; no functional impact |

## Decision Record

| Decision | Rationale |
|----------|-----------|
| Used RELEASE_3_18 instead of latest | RELEASE_3_18 (R 4.3.3, Bioc 3.18) is the closest available image to the paper's R 4.3.0 / Bioc 3.18 requirements. The `latest` tag would have pulled a newer Bioconductor release with different package versions. |
| Built custom Docker image instead of installing at runtime | Ensures reproducibility — all packages are baked into the image and verified during build. |
| Used R 4.3.3 instead of 4.3.0 | The Bioconductor RELEASE_3_18 image ships with R 4.3.3; R 4.3.0 is not available as a tagged image. This is a minor patch difference with no functional impact. |

## Verification

- [x] Docker image built successfully (bio-reproducer:bench-001)
- [x] All 3 R packages load without errors (DESeq2, ggplot2, apeglm)
- [x] Package versions match or are close to paper specifications
- [x] R environment functional

## Artifacts

| File | Purpose |
|------|---------|
| Dockerfile | Image build definition |
| provision.nf | Nextflow workflow for provisioning |
| nextflow.config | Nextflow configuration (Docker, env vars) |
| provision.md | This report |