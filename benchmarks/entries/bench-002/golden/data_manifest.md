# Data Manifest

## Acquisition Summary

| Property | Value |
|----------|-------|
| Status | PARTIAL |
| Strategy | Original (local file) |
| Total Files Acquired | 1 |
| Total Sources Blocked | 2 |
| Total Sources Missing | 1 (regenerable) |

## Data Sources

| Source | Required | Obtained | Location | Notes |
|--------|----------|----------|----------|-------|
| counts.csv (Supplementary Table S1) | Yes | Yes | `raw_data/counts.csv` | 20 genes × 6 samples; 650 bytes; SHA256: `5dadbef4f5c3396624f19a809089ba26bd2353fbe10f41a4b691fa92e842025f` |
| GSE99999 (GEO) | No (redundant with counts.csv) | No | — | Resolves to unrelated Systemic Sclerosis study (PMID 28662216); wrong accession |
| GitHub repository | No (analysis script can be recreated) | No | — | https://github.com/example/drug-response-analysis returns HTTP 404 |
| Supplementary Table S2 | No (regenerable) | No | — | Complete DE results; referenced in paper but not provided; can be regenerated from counts.csv |

## Samples

| Sample ID | Source | Files | Size | Status |
|-----------|--------|-------|------|--------|
| counts.csv | Local (benchmark entry) | `raw_data/counts.csv` | 650 B | Acquired |

## Reference Data

| File | Source | Size | Status |
|------|--------|------|--------|
| KEGG hsa04668 (TNF signaling pathway) | pathview runtime fetch | N/A | Not pre-downloaded; fetched automatically by pathview at analysis time |

## Blocked Data

| Source | Reason | User Decision |
|--------|--------|---------------|
| GSE99999 | GEO accession resolves to unrelated Systemic Sclerosis study (PMID 28662216); does not contain this paper's data | Skip — counts.csv is the authoritative data source |
| GitHub repository (https://github.com/example/drug-response-analysis) | URL returns HTTP 404; repository does not exist | Skip — analysis scripts can be recreated from paper Methods section |

## Verification

- [x] counts.csv present and readable
- [x] SHA256 checksum recorded
- [x] File contents verified (20 genes × 6 samples, valid CSV)
- [ ] GSE99999 — blocked (wrong accession)
- [ ] GitHub repository — blocked (dead URL)
- [ ] Supplementary Table S2 — missing (regenerable from counts.csv during analysis)