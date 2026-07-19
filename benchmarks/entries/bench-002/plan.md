# Reproduction Plan: Transcriptomic Profiling of Drug Response Reveals Dysregulated Pathways

## Paper Metadata

- **Title:** Transcriptomic Profiling of Drug Response Reveals Dysregulated Pathways in Inflammatory and Apoptotic Signaling
- **Authors:** C. Pharmacologist, D. Bioinformatician
- **DOI:** 10.1234/bench.002

## Paper Claims to Verify

### Claim 1: Differential Expression Results (Table 1)
| Gene | log2FC | padj | Direction |
|------|--------|------|-----------|
| IL6 | 3.0 | 0.0003 | Upregulated |
| TNF | 2.5 | 0.001 | Upregulated |
| CXCL8 | 2.2 | 0.002 | Upregulated |
| IL1B | 2.0 | 0.005 | Upregulated |
| BCL2 | -2.2 | 0.0008 | Downregulated |
| MCL1 | -1.8 | 0.003 | Downregulated |

### Claim 2: GO Enrichment Results (Table 2)
| GO Term | Description | GeneRatio | p.adjust |
|---------|-------------|-----------|-----------|
| GO:0006954 | inflammatory response | 4/6 | 0.0002 |
| GO:0019221 | cytokine-mediated signaling pathway | 4/6 | 0.0005 |
| GO:0071345 | cellular response to cytokine stimulus | 3/6 | 0.001 |
| GO:0043067 | regulation of programmed cell death | 3/6 | 0.003 |
| GO:0006915 | apoptotic process | 3/6 | 0.005 |

Significance threshold for GO: q-value < 0.05 (Benjamini-Hochberg adjusted).

### Claim 3: KEGG Pathway
- TNF signaling pathway (hsa04668) activated
- Upregulated genes (IL6, TNF, CXCL8, IL1B) colored red
- Downregulated genes (BCL2, MCL1) colored blue

### Claim 4: Figures
- **Figure 1:** Volcano plot — -log10(padj) vs log2FC, significant genes (padj < 0.05) in red
- **Figure 2:** GO enrichment bar plot — top 10 enriched Biological Process terms
- **Figure 3:** KEGG pathway diagram of TNF signaling pathway (hsa04668)

## Experimental Design

- **Conditions:** Control vs Drug-treated (Compound X)
- **Replicates:** 3 biological replicates per condition (6 samples total)
- **Genes:** 20 genes including inflammatory cytokines, apoptotic regulators, and housekeeping controls
- **Sample names:** Control_1, Control_2, Control_3, Drug_1, Drug_2, Drug_3

## Analysis Methods

### Tools & Versions
| Software | Version | Purpose |
|----------|---------|---------|
| R | 4.3.0 | Statistical computing |
| DESeq2 | 1.42.0 | Differential expression analysis |
| ggplot2 | 3.5.0 | Data visualization |
| apeglm | 1.24.0 | Log2 fold change shrinkage |
| clusterProfiler | — (unspecified) | GO enrichment analysis |
| pathview | — (unspecified) | KEGG pathway visualization |

### Workflow

**Stage 1 — Differential Expression:**
1. Load count matrix from CSV (`counts.csv`)
2. Filter: exclude genes with mean normalized count < 10 across all samples
3. Create DESeqDataSet with design formula `~ condition`
4. Run DESeq2 with default parameters
5. Apply log2 fold change shrinkage with `lfcShrink(type = "apeglm")`
6. Extract results at adjusted p-value < 0.05
7. Convert gene symbols (SYMBOL) to Entrez IDs (ENTREZID) for enrichment analysis

**Stage 2 — GO Enrichment:**
1. Perform GO enrichment analysis on significant DE genes using clusterProfiler
2. Focus on Biological Process (BP) ontology
3. Extract top 10 enriched terms
4. Generate bar plot ordered by -log10(q-value)

**Stage 3 — KEGG Pathway Visualization:**
1. Map DE genes onto the TNF signaling pathway (hsa04668) using pathview
2. Color upregulated genes red, downregulated genes blue

## Data Sources

- **Primary:** `counts.csv` (Supplementary Table S1) — 20 genes × 6 samples, raw integer counts
- **Supplementary Table S2:** Complete differential expression results for all 20 genes
- **GEO Accession:** GSE99999
- **Code Repository:** https://github.com/example/drug-response-analysis

## Expected Outputs

1. **Differential expression table:** Full results for all 20 genes with log2FC, padj, direction
2. **Volcano plot (Figure 1):** ggplot2 volcano plot, significant genes in red
3. **GO enrichment bar plot (Figure 2):** Top 10 enriched BP terms
4. **KEGG pathway diagram (Figure 3):** TNF signaling pathway with gene-level coloring

## Reproduction Steps

1. **Environment Setup:** Install R 4.3.0 with DESeq2 1.42.0, ggplot2 3.5.0, apeglm 1.24.0, clusterProfiler, pathview, and org.Hs.eg.db (for gene ID conversion)
2. **Data Loading:** Read `counts.csv` into R
3. **Differential Expression Analysis:**
   - Filter low-expression genes (mean normalized count < 10)
   - Create DESeqDataSet with `design = ~ condition`
   - Run `DESeq()` and `lfcShrink(type = "apeglm")`
   - Extract significant genes (padj < 0.05)
4. **Gene ID Conversion:** Convert SYMBOL to ENTREZID using `bitr()` from clusterProfiler
5. **GO Enrichment Analysis:**
   - Run `enrichGO()` on significant DE genes (BP ontology)
   - Extract top 10 terms
   - Generate bar plot with `barplot()` or `dotplot()`
6. **KEGG Pathway Visualization:**
   - Run `pathview()` on the TNF signaling pathway (hsa04668)
   - Map gene-level fold changes for coloring
7. **Validation:** Compare reproduced DE results, GO terms, and pathway with paper claims