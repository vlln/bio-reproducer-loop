# Provision Report — bench-002 run_03

**Date:** 2026-07-18
**Host:** aarch64-apple-darwin25.4.0 (Apple M4)

## Environment

| Property | Value |
|----------|-------|
| Container Engine | None (native R) |
| R Version | 4.6.1 (required: ≥ 4.3.0) |
| Docker | 29.4.0 (OrbStack) — available but not used |
| Nextflow | 24.x (Java unavailable; not required for this paper) |

## Rationale

This paper is a pure R-based analysis (DESeq2, clusterProfiler, ggplot2, pathview). All required R packages are already installed natively on the host. No containerization is needed — the analysis runs directly in R with no system-level dependencies beyond the R packages themselves.

## Tools Provisioned

| Tool | Required Version | Installed Version | Status |
|------|-----------------|-------------------|--------|
| R | 4.3.0 | 4.6.1 | deployed |
| DESeq2 | 1.42.0 | 1.52.0 | deployed |
| ggplot2 | 3.5.0 | 4.0.3 | deployed |
| apeglm | 1.24.0 | 1.34.0 | deployed |
| clusterProfiler | not specified | 4.20.0 | deployed |
| pathview | not specified | 1.52.0 | deployed |
| org.Hs.eg.db | not specified | 3.23.1 | deployed |

## Version Compatibility

All installed versions are ≥ the paper-specified versions. R packages are backward-compatible for the DESeq2/ggplot2/apeglm APIs used in this analysis. The newer versions should produce equivalent or identical results.

## Verification

- [x] All R packages load successfully (`library()` calls pass)
- [x] R version satisfies paper requirement (4.6.1 ≥ 4.3.0)
- [x] DESeq2, apeglm, ggplot2, clusterProfiler, pathview, org.Hs.eg.db all load without errors
- [x] No container or Docker image needed — native R installation is sufficient

## Notes

- Java is not installed on this host, so Nextflow cannot run. This is acceptable — the paper does not use Nextflow or require Java.
- Docker is available but unused — native R packages are sufficient for this 20-gene analysis.
- No `provision.nf` was generated since Nextflow cannot execute without Java, and the paper requires no containerized workflow.