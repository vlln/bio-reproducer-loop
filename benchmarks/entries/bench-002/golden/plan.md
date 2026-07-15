# Paper: Transcriptomic Profiling of Drug Response Reveals Dysregulated Pathways

DOI: 10.1234/bench.002

## Paper Understanding

### Research Question
What transcriptomic pathways are dysregulated in response to Compound X drug treatment in a 20-gene panel?

### Study Design
- 20 genes measured via RNA-seq
- 2 conditions: Control vs Drug
- 3 biological replicates per condition
- 6 samples total

### Method Overview
- Count matrix loaded from CSV
- Differential expression: DESeq2 Wald test, apeglm shrinkage, padj < 0.05
- Pre-filtering: genes with mean normalized count < 10 excluded (found in Figure 1 legend)
- GO enrichment: clusterProfiler on significant DE genes (padj < 0.05), q-value < 0.05
- Gene ID conversion: SYMBOL → ENTREZID via bitr() (implicit step, required for clusterProfiler)
- KEGG pathway visualization: pathview on TNF signaling pathway (hsa04668), organism="hsa"
- Visualization: volcano plot (ggplot2), GO bar plot, KEGG pathway diagram

### Key Findings
- 4 upregulated: IL6 (log2FC=3.0), TNF (log2FC=2.5), CXCL8 (log2FC=2.2), IL1B (log2FC=2.0)
- 2 downregulated: BCL2 (log2FC=-2.2), MCL1 (log2FC=-1.8)
- GO enrichment: inflammatory response, cytokine signaling, apoptotic regulation
- KEGG: TNF signaling pathway activation

### Reproduction Target
- Figure 1: Volcano plot with 6 significant genes highlighted
- Figure 2: GO enrichment bar plot (top 10 BP terms)
- Figure 3: KEGG pathway diagram (TNF signaling, hsa04668)
- Quantitative: DE gene list with direction, log2FC, and padj
- Qualitative: pathway-level conclusions about inflammatory + apoptotic dysregulation

## Paper Claims

### Analysis Steps
1. DE: counts.csv → DESeq2 → normalized counts → DE results table (padj < 0.05)
2. GO: DE gene list (SYMBOL) → bitr() → ENTREZID → clusterProfiler enrichGO() → GO terms
3. KEGG: DE results (log2FC vector, ENTREZID) → pathview() → pathway diagram (hsa04668)

### Environment Requirements
| Software | Version | Purpose | Source in Paper |
|----------|---------|---------|-----------------|
| R | 4.3.0 | Statistical computing | Methods |
| DESeq2 | 1.42.0 | Differential expression | Methods |
| ggplot2 | 3.5.0 | Volcano plot | Methods |
| apeglm | 1.24.0 | lfcShrink | Methods |
| clusterProfiler | (not specified) | GO enrichment | Methods |
| pathview | (not specified) | KEGG visualization | Methods |

### Data Requirements
| Database | Accession | Samples | Type | Location in Paper |
|----------|-----------|---------|------|-------------------|
| GEO | GSE99999 | 6 | Count matrix | Data Availability |
| Supplementary | counts.csv | 6 | Count matrix | Supplementary Table S1 |
| Supplementary | (missing) | — | DE results | Supplementary Table S2 |

### Parameters
| Tool | Parameter | Value | From |
|------|-----------|-------|------|
| DESeq2 | design_formula | ~ condition | Methods |
| DESeq2 | significance_threshold | padj < 0.05 | Methods |
| DESeq2 | lfcShrink_type | apeglm | Methods |
| DESeq2 | pre_filtering | mean count < 10 | Figure 1 legend (scattered) |
| clusterProfiler | organism | hsa | Code repository (scattered) |
| clusterProfiler | ontology | BP | (default) |
| clusterProfiler | qvalue_cutoff | 0.05 | Table 2 footnote (scattered) |
| pathview | pathway_id | hsa04668 | Code repository (scattered) |
| pathview | gene_id_type | ENTREZID | (implicit) |

### Expected Results
| Output | Figure/Table | Expected Value |
|--------|--------------|----------------|
| DE genes (padj<0.05) | Table 1 | IL6, TNF, CXCL8, IL1B, BCL2, MCL1 (6 genes) |
| Upregulated | Table 1 | IL6, TNF, CXCL8, IL1B |
| Downregulated | Table 1 | BCL2, MCL1 |
| GO terms | Table 2 | inflammatory response, cytokine signaling, apoptosis |
| Volcano plot | Figure 1 | 6 highlighted genes, 14 background |
| GO bar plot | Figure 2 | Top 10 BP terms, -log10(q-value) |
| KEGG diagram | Figure 3 | TNF signaling pathway (hsa04668), colored by log2FC |

### Figure Reproduction Inventory
| Figure/Panel | Caption/Source | Plot Type | Required Data | Expected Pattern |
|--------------|----------------|-----------|---------------|------------------|
| Figure 1 | Volcano plot | volcano | DE results | 4 genes upper-right, 2 upper-left, 14 near origin |
| Figure 2 | GO enrichment bar plot | barplot | GO enrichment results | Top 10 terms, inflammatory terms at top |
| Figure 3 | KEGG pathway diagram | pathway | DE results (log2FC vector) | TNF signaling, red=up, blue=down |

## Uncertainties
| Item | Issue | Source |
|------|-------|--------|
| clusterProfiler version | Not specified in paper | Methods table |
| pathview version | Not specified in paper | Methods table |
| Gene ID conversion | Not explicitly mentioned; bitr() conversion is implicit | Methods |
| Pre-filtering threshold | In Figure 1 legend, not in Methods | Figure 1 |
| GO q-value cutoff | In Table 2 footnote, not in Methods | Table 2 |
| KEGG pathway ID | In code repository, not in paper | Methods |
| Supplementary Table S2 | Referenced but not provided in data/ | Results |
| GEO accession GSE99999 | Points to unrelated study (scleroderma) | Data Availability |
| GitHub repository | https://github.com/example/drug-response-analysis returns 404 | Data Availability |