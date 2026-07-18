# Paper: Transcriptomic Profiling of Drug Response Reveals Dysregulated Pathways in Inflammatory and Apoptotic Signaling

DOI: 10.1234/bench.002

## Decision Record

| Decision | Reason | Context |
|----------|--------|---------|
| PDF-to-Markdown conversion performed via MinerU API | Paper PDF exists and was successfully converted | 4 images extracted (all tables); output at `01_plan/paper_markdown/paper/` |
| Pre-filtering threshold taken from Figure 1 legend | The mean normalized count < 10 filter is stated in the Figure 1 description, not in Methods | Scattered parameter |
| GO q-value cutoff taken from Table 2 footnote | q-value < 0.05 (Benjamini-Hochberg adjusted) is stated below Table 2, not in Methods | Scattered parameter |
| KEGG pathway ID hsa04668 inferred from paper text | Paper states "TNF signaling pathway" in Results; KEGG ID hsa04668 is the standard TNF signaling pathway for human | metadata.yaml design decision confirms this is intentionally scattered |
| Gene ID conversion (SYMBOL → ENTREZID) treated as required implicit step | clusterProfiler requires ENTREZID; paper uses gene symbols throughout | Standard bioinformatics workflow requirement |
| clusterProfiler and pathview versions marked as not specified | Paper lists "—" for both versions in the Software Versions table | Version gap |
| Supplementary Table S2 treated as missing | Paper references it but no file is provided in the benchmark data directory | Missing supplementary |
| GEO accession GSE99999 recorded as unrelated | GSE99999 resolves to a Systemic Sclerosis study (PMID 28662216), not this paper | Wrong accession |
| GitHub repository recorded as unavailable | https://github.com/example/drug-response-analysis returns HTTP 404 | Dead URL |

## Paper Understanding

### Research Question

This study investigates the transcriptomic response to Compound X, a novel anti-inflammatory agent, using a focused 20-gene RNA-seq panel in a cell line model. The goal is to characterize pathway-level changes induced by drug treatment, specifically identifying which biological pathways are dysregulated through an integrated analysis of differential expression, Gene Ontology enrichment, and KEGG pathway visualization.

### Study Design

The study profiles 20 genes across 6 samples in a two-group design:
- **Control group:** 3 biological replicates (Control_1, Control_2, Control_3)
- **Drug-treated group:** 3 biological replicates (Drug_1, Drug_2, Drug_3)

The 20-gene panel includes inflammatory cytokines (IL6, TNF, CXCL8, IL1B), apoptotic regulators (BCL2, MCL1, TP53, PTEN, CDKN1A), signaling molecules (JUN, FOS, STAT3, EGFR, MYC, VEGFA), and housekeeping controls (GAPDH, ACTB, B2M, HSP90AA1, RPL13A). The count matrix is provided as a CSV file (`counts.csv`).

### Method Overview

The analysis follows a three-stage pipeline:

1. **Differential Expression (DE):** Count data are loaded from CSV, genes with mean normalized count < 10 are excluded (pre-filtering threshold stated in Figure 1 legend), then DESeq2 performs normalization and Wald testing with design formula `~ condition`. Log2 fold change shrinkage is applied using `lfcShrink(type = "apeglm")`. Significant genes are defined at adjusted p-value < 0.05.

2. **GO Enrichment:** The set of differentially expressed genes (gene symbols) undergoes Gene ID conversion from SYMBOL to ENTREZID (implicit step required by clusterProfiler), then clusterProfiler's `enrichGO()` performs enrichment analysis on Biological Process terms with q-value < 0.05 (stated in Table 2 footnote). Results are visualized as a bar plot of the top 10 enriched terms.

3. **KEGG Pathway Visualization:** DE results (log2 fold change values mapped to ENTREZID) are overlaid onto the TNF signaling pathway (hsa04668) using pathview. Upregulated genes are colored red, downregulated genes blue.

### Key Findings

- 6 genes are significantly differentially expressed (padj < 0.05):
  - 4 upregulated: IL6 (log2FC = 3.0), TNF (log2FC = 2.5), CXCL8 (log2FC = 2.2), IL1B (log2FC = 2.0)
  - 2 downregulated: BCL2 (log2FC = -2.2), MCL1 (log2FC = -1.8)
- GO enrichment reveals inflammatory response (GO:0006954, 4/6 genes, padj = 0.0002), cytokine-mediated signaling (GO:0019221, 4/6 genes, padj = 0.0005), and apoptotic process terms
- KEGG pathway visualization confirms TNF signaling pathway (hsa04668) activation
- Conclusion: Compound X induces inflammatory transcriptional program while suppressing anti-apoptotic gene expression

### Reproduction Target

The primary reproduction targets are:
1. **Figure 1:** Volcano plot showing -log10(padj) vs log2FC with 6 significant genes highlighted in red (4 upper-right, 2 upper-left) and 14 non-significant genes near origin
2. **Figure 2:** GO enrichment bar plot of top 10 Biological Process terms ordered by -log10(q-value)
3. **Figure 3:** KEGG pathway diagram of TNF signaling (hsa04668) with upregulated genes in red and downregulated in blue
4. **Quantitative:** Complete DE gene list with direction, log2FC, and padj values matching Table 1
5. **Qualitative:** Pathway-level conclusions about inflammatory and apoptotic dysregulation

## Paper Claims

### Analysis Steps

1. **Pre-filtering:** counts.csv → remove genes with mean normalized count < 10 → filtered count matrix
2. **DE:** filtered count matrix → DESeq2 (design = `~ condition`) → DESeq() → lfcShrink(type = "apeglm") → DE results table (padj < 0.05)
3. **GO:** DE gene list (SYMBOL) → bitr() → ENTREZID → clusterProfiler enrichGO(ontology = "BP", qvalueCutoff = 0.05) → GO BP terms
4. **KEGG:** DE results (log2FC named vector, ENTREZID names) → pathview(pathway.id = "hsa04668", species = "hsa") → pathway diagram PNG

### Code and Data Availability

| Resource | URL/Identifier | Purpose | Location in Paper |
|----------|---------------|---------|-------------------|
| counts.csv | Supplementary Table S1 | Count matrix (20 genes × 6 samples) | Data Availability |
| Supplementary Table S2 | Not provided | Complete DE results | Results ("complete differential expression results") |
| Analysis script | https://github.com/example/drug-response-analysis | R analysis code | Data Availability |
| GEO dataset | GSE99999 | Count matrix deposit | Data Availability |

### System Requirements

| Component | Requirement | Notes | Location in Paper |
|-----------|-------------|-------|-------------------|
| OS | Not specified | — | — |
| R | 4.3.0 | Statistical computing environment | Methods, Software Versions table |

### Environment Requirements

| Software | Version | Purpose | Source in Paper |
|----------|---------|---------|-----------------|
| R | 4.3.0 | Statistical computing environment | Methods / Software Versions table |
| DESeq2 | 1.42.0 | Differential expression analysis | Methods / Software Versions table |
| ggplot2 | 3.5.0 | Volcano plot visualization | Methods / Software Versions table |
| apeglm | 1.24.0 | Log2 fold change shrinkage (lfcShrink) | Methods / Software Versions table |
| clusterProfiler | Not specified | GO enrichment analysis | Methods / Software Versions table (listed as "—") |
| pathview | Not specified | KEGG pathway visualization | Methods / Software Versions table (listed as "—") |
| org.Hs.eg.db | Not specified | Gene ID conversion (SYMBOL → ENTREZID) | Implicit requirement for clusterProfiler |

### Data Requirements

| Database | Accession | Samples | Type | Location in Paper |
|----------|-----------|---------|------|-------------------|
| GEO | GSE99999 | 6 | Count matrix (claimed) | Data Availability |
| Local file | counts.csv (Supplementary Table S1) | 6 (20 genes × 6 samples) | Count matrix | Data Availability / Methods |
| Local file | Supplementary Table S2 | — | Complete DE results (missing) | Results |

### Parameters

| Tool | Parameter | Value | From |
|------|-----------|-------|------|
| DESeq2 | design formula | `~ condition` | Methods |
| DESeq2 | significance threshold | padj < 0.05 | Methods |
| DESeq2 | lfcShrink type | `apeglm` | Methods |
| DESeq2 | pre-filtering | mean normalized count < 10 excluded | Figure 1 legend (scattered) |
| clusterProfiler | ontology | BP (Biological Process) | Methods (default) |
| clusterProfiler | qvalueCutoff | 0.05 | Table 2 footnote (scattered) |
| clusterProfiler | organism/species | hs / "hsa" | Inferred from human gene symbols |
| pathview | pathway.id | hsa04668 (TNF signaling pathway) | Results text ("TNF signaling pathway") |
| pathview | species | "hsa" | Inferred from human gene symbols |
| pathview | gene.idtype | ENTREZID | Implicit (required by pathview) |

### Expected Results

| Output | Figure/Table | Expected Value |
|--------|--------------|----------------|
| Significant DE genes | Table 1 | 6 genes: IL6, TNF, CXCL8, IL1B (up); BCL2, MCL1 (down) |
| IL6 | Table 1 | log2FC = 3.0, padj = 0.0003, upregulated |
| TNF | Table 1 | log2FC = 2.5, padj = 0.001, upregulated |
| CXCL8 | Table 1 | log2FC = 2.2, padj = 0.002, upregulated |
| IL1B | Table 1 | log2FC = 2.0, padj = 0.005, upregulated |
| BCL2 | Table 1 | log2FC = -2.2, padj = 0.0008, downregulated |
| MCL1 | Table 1 | log2FC = -1.8, padj = 0.003, downregulated |
| Top GO term | Table 2 | GO:0006954 inflammatory response, 4/6, padj = 0.0002 |
| GO terms | Table 2 | inflammatory response, cytokine signaling, apoptotic process |
| Volcano plot | Figure 1 | 4 genes upper-right, 2 upper-left, 14 near origin |
| GO bar plot | Figure 2 | Top 10 BP terms, ordered by -log10(q-value) |
| KEGG diagram | Figure 3 | TNF signaling (hsa04668), red = upregulated, blue = downregulated |

### Figure Reproduction Inventory

| Figure/Panel | Original Image | Caption/Source | Scientific Claim | Plot Type | Required Data | Author Plotting Code/Notebook | Expected Pattern | Source |
|--------------|---------------|----------------|------------------|-----------|---------------|-------------------------------|------------------|--------|
| Figure 1 | Not found after checking paper PDF (no figure images embedded) | "Volcano plot" — Results, Figure 1 section | 6 significant DE genes highlighted among 20-gene panel | volcano | DE results (log2FC, padj for all genes) | Not specified (GitHub repo unavailable) | 4 genes (IL6, TNF, CXCL8, IL1B) upper-right, 2 genes (BCL2, MCL1) upper-left, 14 genes near origin | Results text / Figure 1 description |
| Figure 2 | Not found after checking paper PDF (no figure images embedded) | "GO enrichment bar plot" — Results, Figure 2 section | Inflammatory and cytokine terms are top enriched GO BP terms | barplot | GO enrichment results (top 10 BP terms) | Not specified (GitHub repo unavailable) | Top 10 terms ordered by -log10(q-value); inflammatory/cytokine terms at top | Results text / Table 2 |
| Figure 3 | Not found after checking paper PDF (no figure images embedded) | "KEGG pathway diagram" — Results, Figure 3 section | TNF signaling pathway is dysregulated with up/down gene pattern | pathway | DE results as log2FC named vector (ENTREZID) | Not specified (GitHub repo unavailable) | hsa04668 pathway; IL6/TNF/CXCL8/IL1B in red, BCL2/MCL1 in blue | Results text |

## Source Files Reviewed

| File/URL | Type | Local Path | Status | Notes |
|----------|------|------------|--------|-------|
| paper.pdf | Article (PDF) | benchmarks/entries/bench-002/paper.pdf | Reviewed | Primary paper source; converted to Markdown via MinerU API |
| paper.md (MinerU output) | Article (Markdown) | 01_plan/paper_markdown/paper/paper.md | Reviewed | PDF-to-Markdown conversion output |
| Extracted images | Tables (JPEG) | 01_plan/paper_markdown/paper/images/ | Reviewed | 4 images extracted (all tables: Software Versions, DE Results, GO Terms ×2); no figure images embedded |
| paper.md (benchmark) | Article (Markdown) | benchmarks/entries/bench-002/paper.md | Reviewed | Benchmark-provided Markdown version; matches PDF content |
| counts.csv | Data (CSV) | benchmarks/entries/bench-002/data/counts.csv | Reviewed | 20 genes × 6 samples; Supplementary Table S1 |
| metadata.yaml | Benchmark metadata | benchmarks/entries/bench-002/metadata.yaml | Reviewed | Constructed benchmark paper, difficulty: easy |
| expected.yaml | Benchmark checks | benchmarks/entries/bench-002/expected.yaml | Reviewed | Evaluation criteria and expected values |
| https://github.com/example/drug-response-analysis | Code repository | — | HTTP 404 | Returns 404; unavailable |
| GSE99999 (NCBI GEO) | Data repository | — | Reviewed | Resolves to unrelated Systemic Sclerosis study (PMID 28662216) |

## Supplementary Materials Inventory

| Item | Type | URL/Path | Mentioned In | Status | Notes |
|------|------|----------|--------------|--------|-------|
| Supplementary Table S1 (counts.csv) | CSV data | benchmarks/entries/bench-002/data/counts.csv | Data Availability, Methods | Available locally | 20 genes × 6 samples count matrix |
| Supplementary Table S2 | CSV/TSV (complete DE results) | Not provided | Results ("complete differential expression results are provided in Supplementary Table S2") | Not found after checking data/ directory | Referenced but file not provided; DE results can be regenerated from counts.csv |
| Analysis script (GitHub) | R code | https://github.com/example/drug-response-analysis | Data Availability | URL found; deferred (HTTP 404) | Repository does not exist |

## Resource Locations

| Resource | Type | URL/Identifier | Purpose | Location in Paper | Access Notes |
|----------|------|---------------|---------|-------------------|--------------|
| counts.csv | Count matrix (local) | benchmarks/entries/bench-002/data/counts.csv | Input data for DESeq2 | Data Availability / Supplementary Table S1 | Available locally; 20 genes × 6 samples |
| GSE99999 | GEO accession | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE99999 | Claimed data deposit | Data Availability | Resolves to unrelated study (Systemic Sclerosis, PMID 28662216); not this paper's data |
| GitHub repository | Code repository | https://github.com/example/drug-response-analysis | Analysis R scripts | Data Availability | HTTP 404; repository does not exist |
| Supplementary Table S2 | DE results table | Not provided | Complete DE results for all 20 genes | Results | Referenced but not provided; can be regenerated |

## External Identifier Records

| Identifier | Database | Resolved Type | Title/Description | Linked IDs | Source API | Retrieved At |
|------------|----------|---------------|-------------------|------------|------------|--------------|
| 10.1234/bench.002 | DOI (Crossref) | Not resolved | Benchmark constructed DOI; not a real publication DOI | — | Not queried (synthetic DOI) | 2026-07-18 |
| GSE99999 | GEO (NCBI) | Series | "Increased dermal collagen bundle alignment in Systemic Sclerosis..." | PMID 28662216, GSM2667599–GSM2667615 | NCBI GEO API | 2026-07-18 |

## Source Conflicts And Gaps

| Item | Paper Statement | External Record | Issue |
|------|----------------|-----------------|-------|
| GEO accession GSE99999 | Paper claims count matrix deposited at GEO under GSE99999 | GSE99999 is a Systemic Sclerosis fibroblast study (PMID 28662216), submitted Jun 2017 | Wrong accession — GSE99999 does not contain this paper's data |
| GitHub repository | Paper claims analysis script at https://github.com/example/drug-response-analysis | URL returns HTTP 404 | Dead URL — repository does not exist |
| Supplementary Table S2 | Paper claims "complete differential expression results are provided in Supplementary Table S2" | No file provided in benchmark data directory | Missing supplementary — DE results can be regenerated from counts.csv |
| clusterProfiler version | Software Versions table lists "—" | Not specified | Version gap — must be inferred |
| pathview version | Software Versions table lists "—" | Not specified | Version gap — must be inferred |

## Uncertainties

| Item | Issue | Source |
|------|-------|--------|
| clusterProfiler version | Not specified in paper; listed as "—" in Software Versions table | Methods / Software Versions |
| pathview version | Not specified in paper; listed as "—" in Software Versions table | Methods / Software Versions |
| Gene ID conversion (bitr) | Not explicitly mentioned in paper; SYMBOL → ENTREZID conversion is required for clusterProfiler but not stated | Implicit workflow step |
| Pre-filtering threshold | "Genes with mean normalized count < 10 across all samples were excluded" is stated in Figure 1 description, not in Methods section | Figure 1 legend (scattered parameter) |
| GO q-value cutoff | "q-value < 0.05 (Benjamini-Hochberg adjusted)" is stated in Table 2 footnote, not in Methods | Table 2 footnote (scattered parameter) |
| KEGG pathway ID | Paper states "TNF signaling pathway" but does not give KEGG ID hsa04668 explicitly; code repository (unavailable) likely contained this | Results / metadata.yaml design decision |
| Supplementary Table S2 | Referenced in Results but not provided in data directory | Results / Data Availability |
| GEO accession GSE99999 | Points to unrelated Systemic Sclerosis study, not this paper's data | Data Availability |
| GitHub repository | https://github.com/example/drug-response-analysis returns 404 | Data Availability |
| org.Hs.eg.db version | Required for gene ID conversion but version not specified | Implicit dependency |
