# Data Manifest

## Acquisition Summary
| Property | Value |
|----------|-------|
| Status | PARTIAL |
| Strategy | Original |
| Timestamp | 2026-07-16T03:08:59Z |

## Data Sources
| Source | Required | Obtained | Location | Notes |
|--------|----------|----------|----------|-------|
| counts.csv (Supplementary Table S1) | Yes | Yes | raw_data/counts.csv | 10 genes × 6 samples, raw integer counts. Copied from benchmark entry. |
| GSE99999 (GEO) | No | No | — | Resolves to unrelated scleroderma study; not usable for this analysis. Per Phase 1, local counts.csv is the authoritative data source. |
| Analysis script (GitHub) | No | No | — | https://github.com/example/deseq2-analysis returns HTTP 404. Script must be reconstructed from Methods in Phase 5. |

## Samples
| Sample ID | Source | Files | Size | Status |
|-----------|--------|-------|------|--------|
| Control_1 | counts.csv | raw_data/counts.csv | — | acquired |
| Control_2 | counts.csv | raw_data/counts.csv | — | acquired |
| Control_3 | counts.csv | raw_data/counts.csv | — | acquired |
| Treatment_1 | counts.csv | raw_data/counts.csv | — | acquired |
| Treatment_2 | counts.csv | raw_data/counts.csv | — | acquired |
| Treatment_3 | counts.csv | raw_data/counts.csv | — | acquired |

## Reference Data
| File | Source | Size | Status |
|------|--------|------|--------|
| — | — | — | No reference data required for this analysis. |

## Blocked Data
| Source | Reason | User Decision |
|--------|--------|---------------|
| GSE99999 | Resolves to unrelated scleroderma study (48 samples, ECMs). Already noted in Phase 1 as a source conflict. | Not applicable — local counts.csv is authoritative. |
| https://github.com/example/deseq2-analysis | HTTP 404; repository does not exist. | Script will be reconstructed from Methods in Phase 5. |

## Verification
- [x] counts.csv present and readable
- [x] File contains 10 genes × 6 samples (verified: 10 rows + header, 6 sample columns + Gene column)
- [x] All values are integer counts
- [x] Control and Treatment groups each have 3 replicates
- [ ] Checksums verified (not applicable; no checksums provided by paper)