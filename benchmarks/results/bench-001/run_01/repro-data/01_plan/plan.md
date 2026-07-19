# Paper: Differential Expression Analysis of Synthetic Gene Response to Treatment

DOI: 10.1234/bench.001

## Decision Record

| Decision | Value | Reason |
|----------|-------|--------|
| PDF-to-Markdown conversion | Skipped | `paper.md` (clean Markdown) is available alongside `paper.pdf`; `MINERU_API_URL` is not configured. The Markdown source is the primary paper representation. |
| paperutils for identifier resolution | Not available | `paperutils` binary not found in PATH. External identifier records rely on manual checks and metadata.yaml documentation. |
| Output language | en | Locked by phase spec. |

## Paper Understanding

### Research Question

What are the differentially expressed genes between Control and Treatment conditions in a synthetic 10-gene RNA-seq panel? The study aims to demonstrate a standard DESeq2-based differential expression workflow on a small, transparent dataset where results are fully verifiable.

### Study Design

- 10 genes (Gene_A through Gene_J) measured via RNA-seq
- 2 conditions: Control vs Treatment
- 3 biological replicates per condition (6 samples total)
- Samples: Control_1, Control_2, Control_3, Treatment_1, Treatment_2, Treatment_3
- Count matrix provided as `counts.csv` (Supplementary Table S1) with raw integer counts

### Method Overview

The analysis follows the standard DESeq2 workflow:

1. Load the count matrix from CSV into R
2. Create a DESeqDataSet with design formula `~ condition`
3. Run `DESeq()` with default parameters (median-of-ratios normalization, Wald test)
4. Apply log2 fold change shrinkage using `lfcShrink(type = "apeglm")`
5. Extract results at adjusted p-value < 0.05 significance threshold
6. Visualize results as a volcano plot using ggplot2: -log10(padj) on y-axis vs log2FC on x-axis, with significant genes (padj < 0.05) highlighted in red

### Key Findings

- Gene_A: significantly upregulated (log2FC = 2.5, padj = 0.0008)
- Gene_B: significantly downregulated (log2FC = -1.8, padj = 0.004)
- 8 other genes (Gene_C through Gene_J): no significant change (padj > 0.05)
- Figure 1 (volcano plot): Gene_A in upper-right quadrant, Gene_B in upper-left quadrant, remaining genes clustered near origin

### Reproduction Target

Reproduce the differential expression analysis using DESeq2 and generate the volcano plot (Figure 1) showing Gene_A and Gene_B as significantly differentially expressed genes. The key outputs are:
- A DE results table with log2FC and padj for all 10 genes
- A volcano plot matching the described pattern (Gene_A upper-right, Gene_B upper-left, others centered)

## Paper Claims

### Analysis Steps

1. Load count matrix: `counts.csv` → R → count matrix in memory
2. Create DESeqDataSet: count matrix + colData → DESeqDataSet with design `~ condition`
3. Run DESeq2: DESeqDataSet → `DESeq()` → DESeqDataSet with results (default parameters, Wald test)
4. Shrink log2FC: DESeqDataSet → `lfcShrink(type = "apeglm")` → shrunken results
5. Extract significant results: shrunken results → filter padj < 0.05 → 2 significant genes
6. Generate volcano plot: results table → ggplot2 → Figure 1 (volcano plot)

### Code and Data Availability

| Resource | URL/Identifier | Purpose | Location in Paper |
|----------|----------------|---------|-------------------|
| counts.csv (Supplementary Table S1) | Local: `benchmarks/entries/bench-001/data/counts.csv` | Count matrix (10 genes × 6 samples) | Supplementary Materials |
| GitHub repository | https://github.com/example/deseq2-analysis | Analysis script | Data Availability |
| GEO accession | GSE99999 | Count matrix deposit | Data Availability |

### System Requirements

| Component | Requirement | Notes | Location in Paper |
|-----------|-------------|-------|-------------------|
| OS | Not specified | Linux/macOS compatible | — |
| Container runtime | Not specified | Bioconductor Docker image recommended by metadata | — |

### Environment Requirements

| Software | Version | Purpose | Source in Paper |
|----------|---------|---------|-----------------|
| R | 4.3.0 | Statistical computing environment | Methods → Software Versions |
| DESeq2 | 1.42.0 | Differential expression analysis | Methods → Software Versions |
| ggplot2 | 3.5.0 | Data visualization | Methods → Software Versions |
| apeglm | 1.24.0 | Log2 fold change shrinkage | Methods → Software Versions |

### Data Requirements

| Database | Accession | Samples | Type | Location in Paper |
|----------|-----------|---------|------|-------------------|
| GEO | GSE99999 | 6 | Count matrix | Data Availability |
| Supplementary | counts.csv (Supplementary Table S1) | 6 | Count matrix (10 genes × 6 samples, raw integer counts) | Supplementary Materials |

### Parameters

| Tool | Parameter | Value | From |
|------|-----------|-------|------|
| DESeq2 | design_formula | `~ condition` | Methods |
| DESeq2 | significance_threshold | padj < 0.05 | Methods |
| DESeq2 | lfcShrink_type | apeglm | Methods |
| DESeq2 | DESeq() parameters | default | Methods |

### Expected Results

| Output | Figure/Table | Expected Value |
|--------|--------------|----------------|
| Gene_A log2FC | Results table | 2.5 |
| Gene_A padj | Results table | 0.0008 |
| Gene_A direction | Results table | Upregulated |
| Gene_B log2FC | Results table | -1.8 |
| Gene_B padj | Results table | 0.004 |
| Gene_B direction | Results table | Downregulated |
| Gene_C–Gene_J | Results table | Not significant (padj > 0.05) |
| Number of significant genes | Results | 2 (padj < 0.05) |
| Volcano plot | Figure 1 | Gene_A and Gene_B highlighted in red; others near origin |

### Figure Reproduction Inventory

| Figure/Panel | Original Image | Caption/Source | Scientific Claim | Plot Type | Required Data | Author Plotting Code/Notebook | Expected Pattern | Source |
|--------------|----------------|----------------|------------------|-----------|---------------|-------------------------------|------------------|--------|
| Figure 1 | Not provided in paper | Volcano plot of differential expression results | Gene_A and Gene_B are significantly differentially expressed between Control and Treatment | volcano | DE results table (log2FC, padj for all 10 genes) | Not found — GitHub repository returns 404 | Gene_A: upper-right quadrant (high positive log2FC, high significance); Gene_B: upper-left quadrant (negative log2FC, mid-high significance); Gene_C–Gene_J: clustered near origin (log2FC ≈ 0, low significance) | Results |

## Source Files Reviewed

| File/URL | Type | Local Path | Status | Notes |
|----------|------|------------|--------|-------|
| paper.pdf | Paper (PDF) | benchmarks/entries/bench-001/paper.pdf | Reviewed | 34 KB PDF; conversion skipped — paper.md available as primary source |
| paper.md | Paper (Markdown) | benchmarks/entries/bench-001/paper.md | Reviewed | Primary paper source; clean Markdown with all sections |
| counts.csv | Data file | benchmarks/entries/bench-001/data/counts.csv | Reviewed | 10 genes × 6 samples, raw integer counts |
| metadata.yaml | Benchmark metadata | benchmarks/entries/bench-001/metadata.yaml | Reviewed | Benchmark design, complexity profile, robustness profile |
| claims.yaml | Structured claims | benchmarks/entries/bench-001/claims.yaml | Reviewed | Pre-extracted claims for evaluation |
| https://github.com/example/deseq2-analysis | Code repository | — | Not found (HTTP 404) | Repository does not exist |
| https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE99999 | GEO record | — | Mismatch | GSE99999 resolves to unrelated scleroderma study |

## Supplementary Materials Inventory

| Item | Type | URL/Path | Mentioned In | Status | Notes |
|------|------|----------|-------------|--------|-------|
| Supplementary Table S1 (counts.csv) | CSV | benchmarks/entries/bench-001/data/counts.csv | Supplementary Materials | Downloaded and reviewed | 10 genes × 6 samples, raw integer counts |

## Resource Locations

| Resource | Type | URL/Identifier | Purpose | Location in Paper | Access Notes |
|----------|------|----------------|---------|-------------------|-------------|
| counts.csv | Data file | benchmarks/entries/bench-001/data/counts.csv | Count matrix input for DESeq2 | Supplementary Table S1 | Local file available; no download needed |
| GSE99999 | GEO accession | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE99999 | Count matrix deposit | Data Availability | Points to unrelated study (scleroderma); not usable for data download |
| GitHub repository | Code repository | https://github.com/example/deseq2-analysis | Analysis script | Data Availability | Returns HTTP 404; repository does not exist; script must be reconstructed from Methods |
| Bioconductor Docker image | Container image | bioconductor/bioconductor_docker:latest | Runtime environment | metadata.yaml | Recommended container; provides R + Bioconductor packages |

## External Identifier Records

| Identifier | Database | Resolved Type | Title/Description | Linked IDs | Source API | Retrieved At |
|------------|----------|---------------|-------------------|------------|------------|-------------|
| 10.1234/bench.001 | Crossref | DOI (not resolvable) | Constructed benchmark DOI; not registered with any registration agency | — | Manual check | 2026-07-17 |
| GSE99999 | GEO | GEO Series (mismatch) | Resolves to unrelated scleroderma study, not this paper's data | — | Manual check | 2026-07-17 |

## Source Conflicts And Gaps

| Item | Paper Statement | External Record | Issue |
|------|----------------|-----------------|-------|
| GSE99999 | "The dataset is also deposited at GEO under accession GSE99999" | GSE99999 resolves to an unrelated scleroderma study | Accession mismatch; cannot use for data download. Local counts.csv is the authoritative data source. |
| GitHub repository | "The analysis script is available at https://github.com/example/deseq2-analysis" | URL returns HTTP 404 | Repository not accessible; analysis script must be reconstructed from Methods description. |
| DOI | 10.1234/bench.001 | Not resolvable via Crossref or any DOI registration agency | Constructed benchmark identifier; no external metadata available. |
| No original Figure 1 image | Paper describes a volcano plot as Figure 1 | No original image file provided in paper or supplementary materials | Visual pixel-level comparison not possible; only pattern-based validation (gene positions, quadrant placement). |

## Uncertainties

| Item | Issue | Source |
|------|-------|--------|
| Exact normalization method | Paper says "default parameters" — DESeq2 default is median-of-ratios normalization, but this is not explicitly stated | Methods |
| ggplot2 version compatibility | Listed as 3.5.0; may require specific R version compatibility | Methods |
| No original figure image | Volcano plot described in text but no original image file provided for visual comparison | Results |
| Log2FC precision | Gene_A claimed log2FC = 2.5; actual computed value may differ due to DESeq2/apeglm version differences and normalization | Methods |
| p-value precision | Gene_A claimed padj = 0.0008; actual value may differ substantially across DESeq2 versions | Methods |
