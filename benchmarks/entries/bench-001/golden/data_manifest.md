# Data Manifest

## Acquisition Summary

| Property | Value |
|----------|-------|
| Status | COMPLETED |
| Strategy | Original (Supplementary Table S1) |

## Data Sources

| Source | Required | Obtained | Location | Notes |
|--------|----------|----------|----------|-------|
| Supplementary Table S1 (counts.csv) | Yes | Yes | `raw_data/counts.csv` | 10 genes × 6 samples, raw integer counts. Copied from `01_plan/resources/counts.csv`. |
| GSE99999 (GEO) | No | No | — | GEO accession mismatch — GSE99999 is an unrelated Systemic Sclerosis study (PMID 28662216). Not used. |
| https://github.com/example/deseq2-analysis | No | No | — | HTTP 404. Fictional example URL. Analysis script will be reconstructed from Methods. |

## Samples

| Sample ID | Source | Files | Size | Status |
|-----------|--------|-------|------|--------|
| Control_1 | counts.csv | 1 | column | Acquired |
| Control_2 | counts.csv | 1 | column | Acquired |
| Control_3 | counts.csv | 1 | column | Acquired |
| Treatment_1 | counts.csv | 1 | column | Acquired |
| Treatment_2 | counts.csv | 1 | column | Acquired |
| Treatment_3 | counts.csv | 1 | column | Acquired |

## Reference Data

No reference data (genome, annotation) required — this analysis uses a pre-computed count matrix.

## Blocked Data

| Source | Reason | User Decision |
|--------|--------|---------------|
| GSE99999 | Accession mismatch — unrelated Systemic Sclerosis study | N/A (not required; count matrix from Supplementary Table S1) |
| GitHub analysis script | HTTP 404 — fictional example URL | N/A (analysis will be reconstructed from Methods in Phase 5) |

## Verification

- [x] All files present
- [x] Count matrix verified: 10 genes (Gene_A–Gene_J) × 6 samples (Control_1–3, Treatment_1–3)
- [x] Data integrity: raw integer counts, no missing values