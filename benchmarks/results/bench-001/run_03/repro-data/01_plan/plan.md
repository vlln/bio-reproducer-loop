# Paper: Differential Expression Analysis of Synthetic Gene Response to Treatment
DOI: 10.1234/bench.001

## Paper Understanding

### Research Question

This paper presents a minimal, synthetic differential expression analysis to demonstrate a complete RNA-seq pipeline. The biological question is whether a 10-gene panel shows differential expression between Control and Treatment conditions. The study uses a synthetic dataset (not real biological samples) to make the analysis transparent and fully verifiable. The computational goal is to reproduce a standard DESeq2 workflow — from count matrix loading through normalization, statistical testing, fold-change shrinkage, and volcano plot visualization.

### Study Design

- **Samples**: 6 synthetic samples total — 3 Control replicates (Control_1, Control_2, Control_3) and 3 Treatment replicates (Treatment_1, Treatment_2, Treatment_3).
- **Genes**: 10 genes (Gene_A through Gene_J) profiled across all samples.
- **Data type**: Raw integer count matrix (10 rows × 6 columns).
- **Design formula**: ~ condition (two-group comparison).
- **Significance threshold**: adjusted p-value < 0.05.

### Method Overview

The analysis follows the standard DESeq2 workflow:
1. Load the count matrix from a CSV file.
2. Create a `DESeqDataSet` with design formula `~ condition`.
3. Run `DESeq()` with default parameters (estimate size factors, estimate dispersions, fit negative binomial GLM, Wald test).
4. Apply log2 fold change shrinkage using `lfcShrink(type = "apeglm")`.
5. Extract results at adjusted p-value < 0.05.
6. Generate a volcano plot with ggplot2 showing -log10(adjusted p-value) vs log2 fold change, highlighting significant genes in red.

### Key Findings

- **Gene_A**: Strongly upregulated, log2FC = 2.5, padj = 0.0008.
- **Gene_B**: Strongly downregulated, log2FC = -1.8, padj = 0.004.
- **Genes C–J**: No significant differential expression (padj range 0.78–0.98, log2FC near 0).
- The volcano plot (Figure 1) shows Gene_A in the upper-right quadrant and Gene_B in the upper-left quadrant, with the remaining 8 genes clustered near the origin.

### Reproduction Target

The primary reproduction target is **Figure 1 (volcano plot)**: a scatter plot of -log10(adjusted p-value) vs log2 fold change for all 10 genes, with significant genes (padj < 0.05) highlighted in red. The expected pattern is two显著 points (Gene_A upper-right, Gene_B upper-left) and 8 non-significant points near the x-axis origin. Secondary targets include reproducing the exact DESeq2 results table (log2FC and padj values for all 10 genes).

## Paper Claims

### Analysis Steps
1. **Count matrix loading**: counts.csv → R data.frame → DESeqDataSet
2. **Normalization and testing**: DESeqDataSet → DESeq() → results object (DESeq2 v1.42.0)
3. **Fold change shrinkage**: results object → lfcShrink(type="apeglm") → shrunken log2FC (apeglm v1.24.0)
4. **Significance filtering**: shrunken results → padj < 0.05 → 2 significant genes
5. **Visualization**: results data.frame → ggplot2 volcano plot → Figure 1 (ggplot2 v3.5.0)

### Code and Data Availability
| Resource | URL/Identifier | Purpose | Location in Paper |
|----------|---------------|---------|-------------------|
| Count matrix (counts.csv) | Supplementary Table S1 | Input count data for DESeq2 | Data Availability; Supplementary Materials |
| Analysis script | https://github.com/example/deseq2-analysis | R analysis code | Data Availability |
| GEO dataset | GSE99999 | Public data deposit | Data Availability |

### System Requirements
| Component | Requirement | Notes | Location in Paper |
|-----------|------------|-------|-------------------|
| OS | Not specified | R is cross-platform | Not specified |
| R | 4.3.0 | Statistical computing environment | Software Versions table |

### Environment Requirements
| Software | Version | Purpose | Source in Paper |
|----------|---------|---------|-----------------|
| R | 4.3.0 | Statistical computing environment | Software Versions table |
| DESeq2 | 1.42.0 | Differential expression analysis | Software Versions table |
| ggplot2 | 3.5.0 | Data visualization | Software Versions table |
| apeglm | 1.24.0 | Log2 fold change shrinkage | Software Versions table |

### Data Requirements
| Database | Accession | Samples | Type | Location in Paper |
|----------|-----------|---------|------|-------------------|
| GEO | GSE99999 | 6 (3 Control + 3 Treatment) | Synthetic count matrix | Data Availability |

### Parameters
| Tool | Parameter | Value | From |
|------|-----------|-------|------|
| DESeq2 | design formula | ~ condition | Methods > Data Processing |
| DESeq2 | run parameters | default | Methods > Data Processing step 3 |
| lfcShrink | type | apeglm | Methods > Data Processing step 4 |
| Results | padj threshold | < 0.05 | Methods > Data Processing step 5; Abstract |

### Expected Results
| Output | Figure/Table | Expected Value |
|--------|-------------|----------------|
| Gene_A log2FC | Results table | 2.5 |
| Gene_A padj | Results table | 0.0008 |
| Gene_A direction | Results table | Upregulated |
| Gene_B log2FC | Results table | -1.8 |
| Gene_B padj | Results table | 0.004 |
| Gene_B direction | Results table | Downregulated |
| Genes C–J padj | Results table | 0.78–0.98 (not significant) |
| Volcano plot | Figure 1 | Gene_A upper-right, Gene_B upper-left, 8 genes near origin |

### Figure Reproduction Inventory
| Figure/Panel | Original Image | Caption/Source | Scientific Claim | Plot Type | Required Data | Author Plotting Code/Notebook | Expected Pattern | Source |
|-------------|---------------|----------------|-----------------|-----------|---------------|------------------------------|-----------------|--------|
| Figure 1: Volcano Plot | Not extracted by mineru (only table images were captured) | "Figure 1: Volcano Plot" — Results section, page with Figure 1 heading | Gene_A upregulated (log2FC=2.5, padj=0.0008); Gene_B downregulated (log2FC=-1.8, padj=0.004); 8 genes not significant | Volcano plot (scatter: -log10(padj) vs log2FC) | DESeq2 results table: gene names, log2FC, padj for all 10 genes | Not found after checking GitHub repo (https://github.com/example/deseq2-analysis returns 404) | Gene_A in upper-right quadrant (high positive log2FC, high -log10(padj)); Gene_B in upper-left quadrant (negative log2FC, high -log10(padj)); 8 genes clustered near origin (log2FC≈0, low -log10(padj)) | Paper Results section |

## Source Files Reviewed
| File/URL | Type | Local Path | Status | Notes |
|----------|------|-----------|--------|-------|
| paper.pdf | Article PDF | benchmarks/entries/bench-001/paper.pdf | Downloaded and reviewed | Source PDF provided in benchmark entry |
| paper.md | Markdown (mineru output) | 01_plan/paper_markdown/paper/paper.md | Downloaded and reviewed | Converted from PDF via mineru-api |
| img_001.jpg | Software versions table | 01_plan/paper_markdown/paper/images/img_001.jpg | Downloaded and inventoried | Extracted by mineru |
| img_002.jpg | Results table (Genes C–J) | 01_plan/paper_markdown/paper/images/img_002.jpg | Downloaded and inventoried | Extracted by mineru |
| img_003.jpg | Results table (Genes A–B) | 01_plan/paper_markdown/paper/images/img_003.jpg | Downloaded and inventoried | Extracted by mineru |
| https://doi.org/10.1234/bench.001 | DOI landing page | — | Not found after checking DOI resolver | Returns 404; synthetic DOI |
| https://github.com/example/deseq2-analysis | Code repository | — | Not found after checking GitHub | Returns 404; example URL |

## Supplementary Materials Inventory
| Item | Type | URL/Path | Mentioned In | Status | Notes |
|------|------|---------|-------------|--------|-------|
| Supplementary Table S1 (counts.csv) | CSV data file | Not provided as downloadable file; described in Supplementary Materials section | Data Availability; Supplementary Materials section | Not found after checking PDF and supplementary section | Described as 10 rows × 6 columns raw integer counts; no actual CSV file embedded or linked in PDF |

## Resource Locations
| Resource | Type | URL/Identifier | Purpose | Location in Paper | Access Notes |
|----------|------|---------------|---------|-------------------|-------------|
| Count matrix | CSV | Supplementary Table S1 (counts.csv) | Input data for DESeq2 analysis | Data Availability; Supplementary Materials | Described but not provided as actual file; must be reconstructed from paper description |
| GEO dataset | GEO accession | GSE99999 | Public data repository deposit | Data Availability | Synthetic accession; likely does not exist in GEO |
| Analysis script | GitHub repo | https://github.com/example/deseq2-analysis | R analysis code | Data Availability | Returns 404; example placeholder URL |

## External Identifier Records
| Identifier | Database | Resolved Type | Title/Description | Linked IDs | Source API | Retrieved At |
|-----------|----------|--------------|-------------------|-----------|-----------|-------------|
| 10.1234/bench.001 | Crossref/DOI | Unresolved | Differential Expression Analysis of Synthetic Gene Response to Treatment | — | DOI resolver (doi.org) | 2026-07-18 | Returns 404; synthetic DOI |
| GSE99999 | GEO | Unresolved | Not found | — | NCBI GEO | 2026-07-18 | Synthetic accession; paperutils unavailable for verification |

## Source Conflicts And Gaps
| Item | Paper Statement | External Record | Issue |
|------|----------------|-----------------|-------|
| DOI | 10.1234/bench.001 | Returns 404 on doi.org | Synthetic DOI; no landing page available for supplementary material check |
| GitHub repo | https://github.com/example/deseq2-analysis | Returns 404 | Example placeholder URL; no analysis code available |
| GEO accession | GSE99999 | Likely does not exist | Synthetic accession; no public data to verify |
| counts.csv | Described as Supplementary Table S1 | No actual file in PDF or linked | Count matrix must be reconstructed from paper description (10 genes × 6 samples) |
| Volcano plot figure | Figure 1 described in text | Not extracted as image by mineru | Only table images were captured; volcano plot figure not available for visual comparison |

## Uncertainties
| Item | Issue | Source |
|------|-------|--------|
| Exact count values | Paper describes counts.csv structure (10 genes × 6 samples, raw integer counts) but does not provide actual count values. The exact integer counts for each gene-sample pair are not stated in the text. | Supplementary Materials section |
| Volcano plot visual details | No original figure image available. Exact axis ranges, point sizes, colors (beyond "red for significant"), labels, and title are not specified. | Figure 1 description |
| Author plotting code | GitHub repo returns 404. No R script or notebook available to verify exact ggplot2 code used. | Data Availability |
| paperutils unavailable | paperutils CLI has a module import error (`ModuleNotFoundError: No module named 'paperutils'`). Could not resolve DOI or GEO accession programmatically. | Environment |

## Decision Record
| Decision | Reason |
|----------|--------|
| Treat as synthetic benchmark paper | DOI, GitHub URL, and GEO accession all return 404 or are clearly placeholder values. Paper content describes a minimal synthetic dataset. |
| Reconstruct count matrix from description | counts.csv is described but not provided. Downstream phases will need to generate or obtain the count matrix. |
| No supplementary material page check | DOI landing page returns 404, so no supplementary material tab could be checked. |
| Figure 1 original image not available | mineru extracted only table images (software versions, results tables). The volcano plot figure was not captured as an image. |
