# Paper: Differential Expression Analysis of Synthetic Gene Response to Treatment
DOI: 10.1234/bench.001

## Paper Understanding

### Research Question
What are the differentially expressed genes between Control and Treatment conditions in a synthetic 10-gene RNA-seq panel? The study uses a minimal, fully known dataset to demonstrate a complete DESeq2 differential expression workflow, making the analysis transparent and verifiable.

### Study Design
- 10 synthetic genes profiled via RNA-seq
- 2 conditions: Control vs Treatment
- 3 biological replicates per condition (6 samples total)
- Preprocessed count matrix (raw integer counts) provided as CSV
- No raw sequencing data; analysis starts from count matrix

### Method Overview
The analysis follows the standard DESeq2 workflow:
1. Load the count matrix from CSV (10 genes × 6 samples)
2. Create a DESeqDataSet with design formula `~ condition`
3. Run DESeq2 with default parameters (median-of-ratios normalization, Wald test)
4. Apply log2 fold change shrinkage using `lfcShrink(type = "apeglm")`
5. Extract results at adjusted p-value < 0.05
6. Generate a volcano plot with ggplot2 showing -log10(padj) vs log2FC, with significant genes highlighted in red

### Key Findings
- Gene_A: significantly upregulated (log2FC = 2.5, padj = 0.0008)
- Gene_B: significantly downregulated (log2FC = -1.8, padj = 0.004)
- 8 other genes (Gene_C through Gene_J): no significant change (padj > 0.78)
- Volcano plot (Figure 1): Gene_A in upper-right, Gene_B in upper-left, others clustered near origin

### Reproduction Target
Reproduce the differential expression analysis pipeline using DESeq2 and generate the volcano plot (Figure 1) showing Gene_A and Gene_B as the two significantly differentially expressed genes. The primary outputs are: (1) a DE results table with log2FC and padj values, and (2) a volcano plot figure.

## Paper Claims

### Analysis Steps
1. Load count matrix: `counts.csv` → R → DESeq2 → normalized counts
2. Differential expression: normalized counts → DESeq2 (Wald test, default params) → DE results table
3. Shrinkage: DE results → `lfcShrink(type = "apeglm")` → shrunk log2FC values
4. Visualization: DE results → ggplot2 → volcano plot (Figure 1)

### Code and Data Availability
| Resource | URL/Identifier | Purpose | Location in Paper |
|----------|----------------|---------|-------------------|
| counts.csv | Supplementary Table S1 | Count matrix (10 genes × 6 samples) | Supplementary Materials |
| GitHub repository | https://github.com/example/deseq2-analysis | Analysis script | Data Availability |
| GEO accession | GSE99999 | Count matrix deposit | Data Availability |

### System Requirements
| Component | Requirement | Notes | Location in Paper |
|-----------|-------------|-------|-------------------|
| OS | Not specified | Linux/macOS compatible | — |
| Container runtime | Not specified | Docker assumed for bioconductor image | — |

### Environment Requirements
| Software | Version | Purpose | Source in Paper |
|----------|---------|---------|-----------------|
| R | 4.3.0 | Statistical computing environment | Methods |
| DESeq2 | 1.42.0 | Differential expression analysis | Methods |
| ggplot2 | 3.5.0 | Data visualization | Methods |
| apeglm | 1.24.0 | Log2 fold change shrinkage | Methods |

### Data Requirements
| Database | Accession | Samples | Type | Location in Paper |
|----------|-----------|---------|------|-------------------|
| GEO | GSE99999 | 6 | Count matrix | Data Availability |
| Supplementary | counts.csv | 6 | Count matrix | Supplementary Table S1 |

### Parameters
| Tool | Parameter | Value | From |
|------|-----------|-------|------|
| DESeq2 | significance_threshold | padj < 0.05 | Methods |
| DESeq2 | design_formula | ~ condition | Methods |
| DESeq2 | lfcShrink_type | apeglm | Methods |
| DESeq2 | other parameters | default | Methods |

### Expected Results
| Output | Figure/Table | Expected Value |
|--------|--------------|----------------|
| Gene_A log2FC | Results table | 2.5 |
| Gene_A padj | Results table | 0.0008 |
| Gene_B log2FC | Results table | -1.8 |
| Gene_B padj | Results table | 0.004 |
| Significant genes count | Results table | 2 (padj < 0.05) |
| Volcano plot | Figure 1 | Gene_A (upper-right) and Gene_B (upper-left) highlighted |

### Figure Reproduction Inventory
| Figure/Panel | Original Image | Caption/Source | Scientific Claim | Plot Type | Required Data | Author Plotting Code/Notebook | Expected Pattern | Source |
|--------------|----------------|----------------|------------------|-----------|---------------|-------------------------------|------------------|--------|
| Figure 1 | Not provided (no original image in paper or supplementary) | "Volcano plot showing -log10(adjusted p-value) vs log2 fold change for all 10 genes" (Results) | Gene_A and Gene_B are significantly differentially expressed | Volcano plot | DE results table (gene, log2FC, padj) | Not found after checking GitHub repository (404) | Gene_A in upper-right quadrant (high log2FC, high significance), Gene_B in upper-left quadrant (negative log2FC, high significance), remaining 8 genes clustered near origin (log2FC ≈ 0, low significance) | Results |

## Source Files Reviewed
| File/URL | Type | Local Path | Status | Notes |
|----------|------|------------|--------|-------|
| paper.pdf | Paper (PDF) | benchmarks/entries/bench-001/paper.pdf | Converted to Markdown via MinerU API | 4 pages; converted to `01_plan/paper_markdown/paper/paper.md` with 3 extracted images |
| paper.md (MinerU output) | Paper (Markdown) | 01_plan/paper_markdown/paper/paper.md | Reviewed | Primary paper representation post-conversion |
| img_001.jpg (MinerU) | Software versions table | 01_plan/paper_markdown/paper/images/img_001.jpg | Reviewed | Extracted table: R 4.3.0, DESeq2 1.42.0, ggplot2 3.5.0, apeglm 1.24.0 |
| img_002.jpg (MinerU) | DE results table (significant genes) | 01_plan/paper_markdown/paper/images/img_002.jpg | Reviewed | Gene_A (2.5, 0.0008, Upregulated), Gene_B (-1.8, 0.004, Downregulated) |
| img_003.jpg (MinerU) | DE results table (non-significant genes) | 01_plan/paper_markdown/paper/images/img_003.jpg | Reviewed | Gene_C through Gene_J, all not significant |
| counts.csv | Data file | benchmarks/entries/bench-001/data/counts.csv | Reviewed | 10 genes × 6 samples, raw integer counts |
| paper.md (entry) | Paper (Markdown) | benchmarks/entries/bench-001/paper.md | Reviewed | Alternative paper source (Markdown format) |
| https://github.com/example/deseq2-analysis | Code repository | — | Not found | Returns HTTP 404; repository does not exist |
| https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE99999 | GEO record | — | Mismatch | GSE99999 resolves to an unrelated scleroderma study |
| https://api.crossref.org/works/10.1234/bench.001 | DOI record | — | Not found | HTTP 404; DOI not registered in Crossref |
| https://www.medrxiv.org/content/10.1234/bench.001 | Preprint landing page | — | Not found | HTTP 404 |
| https://www.biorxiv.org/content/10.1234/bench.001 | Preprint landing page | — | Not found | HTTP 404 |

## Supplementary Materials Inventory
| Item | Type | URL/Path | Mentioned In | Status | Notes |
|------|------|----------|-------------|--------|-------|
| Supplementary Table S1 (counts.csv) | CSV | benchmarks/entries/bench-001/data/counts.csv | Supplementary Materials, Data Availability | Downloaded and reviewed | 10 genes × 6 samples, raw integer counts; available locally |

## Resource Locations
| Resource | Type | URL/Identifier | Purpose | Location in Paper | Access Notes |
|----------|------|----------------|---------|-------------------|-------------|
| counts.csv | Data file | benchmarks/entries/bench-001/data/counts.csv | Count matrix input for DESeq2 | Supplementary Table S1 | Local file; no download needed |
| GSE99999 | GEO accession | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE99999 | Count matrix deposit | Data Availability | Points to unrelated study (scleroderma); not usable for this paper |
| https://github.com/example/deseq2-analysis | GitHub repository | https://github.com/example/deseq2-analysis | Analysis script | Data Availability | Returns 404; repository does not exist |

## External Identifier Records
| Identifier | Database | Resolved Type | Title/Description | Linked IDs | Source API | Retrieved At |
|------------|----------|---------------|-------------------|------------|------------|-------------|
| 10.1234/bench.001 | Crossref | DOI (not resolvable) | Benchmark DOI; not registered in Crossref | — | paperutils get | 2026-07-18 |
| GSE99999 | GEO | GEO Series | Unrelated study: "Increased dermal collagen bundle alignment in Systemic Sclerosis..." | — | paperutils explain | 2026-07-18 |

## Source Conflicts And Gaps
| Item | Paper Statement | External Record | Issue |
|------|----------------|-----------------|-------|
| GSE99999 | "The dataset is also deposited at GEO under accession GSE99999" | GSE99999 resolves to an unrelated scleroderma study (48 samples) | Accession mismatch; cannot use for data download. Fallback to local counts.csv. |
| GitHub repository | "The analysis script is available at https://github.com/example/deseq2-analysis" | URL returns HTTP 404 | Repository not accessible; analysis script must be reconstructed from Methods description |
| DOI | 10.1234/bench.001 | Not resolvable via Crossref (HTTP 404) | Constructed benchmark identifier; no external metadata available |
| No original Figure 1 image | Paper describes volcano plot | No original image file provided in paper or supplementary | Visual comparison of figures not possible; only pattern-based validation |
| Version drift expected | Paper states R 4.3.0 / DESeq2 1.42.0 | Actual environment may have newer versions | log2FC and p-values may differ due to algorithm version changes (~15% log2FC tolerance expected) |

## Uncertainties
| Item | Issue | Source |
|------|-------|--------|
| Exact normalization | "Default parameters" could mean different normalization methods in different DESeq2 versions | Methods |
| ggplot2 version compatibility | Listed as 3.5.0, may need compatible R version | Methods |
| No original figure image | Volcano plot described but no original image file provided for visual comparison | Results |
| Log2FC precision | Gene_A claimed log2FC = 2.5; actual value may differ due to DESeq2/apeglm version differences (paper states ~2.5, raw data suggests ~2.95) | Methods, design_decisions |
| p-value magnitude | Paper states padj = 0.0008 for Gene_A; actual p-values may differ by orders of magnitude due to DESeq2 version differences | Methods |

## Decision Record

| Decision | Reason |
|----------|--------|
| Used MinerU API to convert PDF to Markdown | Phase 1 rule 14: PDF must be converted before reading |
| Used local counts.csv as primary data source | GEO GSE99999 mismatch; local file is the authoritative data |
| No attempt to download from GEO or GitHub | Both resources are inaccessible or mismatched; paper Methods provide sufficient detail to reconstruct analysis |
| Did not search for additional resources beyond paper citations | Phase 1 boundary: only resolve identifiers explicitly given in paper |
| Figure 1 validation will be pattern-based, not pixel-based | No original image available; validation will check gene positions and significance pattern |
