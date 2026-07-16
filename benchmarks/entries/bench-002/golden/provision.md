# Provision Report — bench-002 run_01

Generated: 2026-07-15T11:50 UTC

## Environment

| Property | Value |
|----------|-------|
| R Version | 4.6.1 (2026-06-24, "Happy Hop") |
| Bioconductor | 3.23 (BiocManager 1.30.27) |
| Platform | aarch64-apple-darwin25.4.0 |
| Container Engine | N/A (native R installation) |
| Deployment Method | Direct R package installation via BiocManager |

## Decision Record

| Decision | Reason |
|----------|--------|
| Native R installation instead of containerized deployment | Docker daemon not running (OrbStack not started); Nextflow not installed; paper is pure R analysis with small dataset (20 genes × 6 samples) |
| Newer package versions than paper | Paper specifies R 4.3.0 / Bioc 3.18; system has R 4.6.1 / Bioc 3.23. Exact versions (DESeq2 1.42.0, apeglm 1.24.0) are not available for Bioc 3.23; latest compatible versions installed |
| No Nextflow workflow executed | Nextflow not available; provision.nf provided as documentation of intended deployment strategy |

## Tools Provisioned

| Tool | Paper Version | Installed Version | Image | Status |
|------|--------------|-------------------|-------|--------|
| R | 4.3.0 | 4.6.1 | N/A (native) | deployed |
| DESeq2 | 1.42.0 | 1.52.0 | N/A (native R) | deployed |
| ggplot2 | 3.5.0 | 4.0.3 | N/A (native R) | deployed |
| apeglm | 1.24.0 | 1.34.0 | N/A (native R) | deployed |
| clusterProfiler | Not specified | 4.20.0 | N/A (native R) | deployed |
| pathview | Not specified | 1.52.0 | N/A (native R) | deployed |
| org.Hs.eg.db | Not specified | 3.23.1 | N/A (native R) | deployed |

## Verification

- [x] All 6 required packages load successfully
- [x] DESeq2: makeExampleDESeqDataSet + DESeq() runs
- [x] bitr (org.Hs.eg.db): SYMBOL → ENTREZID conversion works (6/6 genes)
- [x] clusterProfiler enrichGO: enrichment analysis produces results (874 BP terms)
- [x] pathview: package loads without errors

### Smoke Test Results

```
Test 1 PASS: DESeq2 runs
Test 2 PASS: bitr converted 6 genes
Test 3 PASS: enrichGO found 874 terms
Test 4 PASS: pathview loads
```

## Dependencies Installed

83 dependency packages were installed from CRAN and Bioconductor, including:
XML, RSQLite, Rgraphviz, KEGGgraph, KEGGREST, AnnotationDbi, GO.db, GOSemSim, ggtree, DOSE, enrichplot, ggiraph, and others.

## Notes

- Paper-specified versions for DESeq2 (1.42.0), ggplot2 (3.5.0), and apeglm (1.24.0) are from Bioconductor 3.18 / R 4.3 era. The installed versions are the latest compatible with R 4.6.1 / Bioconductor 3.23. API compatibility is expected — DESeq2, clusterProfiler, and pathview maintain stable interfaces across minor versions.
- If exact version reproduction is required, a containerized R 4.3.0 environment with Bioconductor 3.18 should be built. Start OrbStack (`orbstack start`) to enable Docker.