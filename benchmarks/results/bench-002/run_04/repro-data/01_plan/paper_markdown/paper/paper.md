# Transcriptomic Profiling of Drug Response Reveals Dysregulated Pathways in Inflammatory and Apoptotic Signaling

Authors: C. Pharmacologist, D. Bioinformatician

DOI: 10.1234/bench.002

# Abstract

Background: Understanding the transcriptomic response to pharmacological intervention is critical for drug development. This study profiled 20 genes in a cell line model treated with Compound X, a novel anti-inflammatory agent, to characterize pathway-level changes.

Methods: RNA-seq count data for 20 genes were profiled across 6 samples (3 Control, 3 Drug-treated). Differential expression analysis was performed using DESeq2 v1.42.0 in R v4.3.0. Gene Ontology enrichment analysis was performed using clusterProfiler. KEGG pathway visualization was performed using pathview.

Results: Four genes were significantly upregulated: IL6 (log2FC = 3.0, padj = 0.0003), TNF (log2FC = 2.5, padj = 0.001), CXCL8 (log2FC = 2.2, padj = 0.002), and IL1B (log2FC = 2.0, padj = 0.005). Two genes were significantly downregulated: BCL2 (log2FC = -2.2, padj = 0.0008) and MCL1 (log2FC = -1.8, padj = 0.003). GO enrichment of the significant genes revealed enrichment for inflammatory response and cytokine signaling pathways. KEGG pathway visualization confirmed activation of the TNF signaling pathway.

Conclusions: Compound X induces a pronounced inflammatory transcriptional program while suppressing anti-apoptotic gene expression. The dysregulation of TNF and NF-kappa B signaling pathways suggests a complex mechanism of action involving both pro-inflammatory and pro-apoptotic effects.

# Introduction

RNA-sequencing enables systematic characterization of drug-induced transcriptomic changes. While differential expression analysis identifies individual genelevel changes, pathway enrichment analysis provides biological context by revealing coordinated changes in functional gene sets. The integration of differential expression, gene ontology enrichment, and pathway visualization constitutes a standard multi-step analysis pipeline in transcriptomic pharmacology.

This study examines the transcriptomic response of 20 genes to Compound X treatment. We employ a three-stage analysis: (1) differential expression analysis with DESeq2, (2) Gene Ontology enrichment with clusterProfiler, and (3) KEGG pathway visualization with pathview. The 20-gene panel includes key inflammatory cytokines, apoptotic regulators, and housekeeping controls, enabling a focused but biologically informative analysis.

# Methods

# Sample Preparation

RNA-seq was performed on 6 samples: - Control group: 3 biological replicates (Control\_1, Control\_2, Control\_3) - Drug-treated group: 3 biological replicates (Drug\_1, Drug\_2, Drug\_3)

Each sample was profiled for the same 20 genes. The count matrix is provided as counts.csv (Supplementary Table S1).

# Differential Expression Analysis

Count data were normalized and analyzed using DESeq2 v1.42.0 in R v4.3.0. The analysis followed the standard DESeq2 workflow:

1. Load count matrix from CSV   
2. Create DESeqDataSet with design formula \~ condition   
3. Run DESeq2 with default parameters   
4. Apply log2 fold change shrinkage with lfcShrink(type = "apeglm")   
5. Extract results at adjusted p-value < 0.05

# GO Enrichment Analysis

Gene Ontology enrichment analysis was performed on the set of differentially expressed genes using clusterProfiler. Enriched Biological Process terms were visualized as a bar plot.

# KEGG Pathway Visualization

KEGG pathway visualization was performed using pathview to map differentially expressed genes onto the TNF signaling pathway.

# Visualization

Figure 1: Volcano plot was generated using ggplot2 v3.5.0, displaying -log10(adjusted p-value) on the y-axis against log2 fold change on the x-axis. Significant genes (padj < 0.05) were highlighted in red. Genes with mean normalized count < 10 across all samples were excluded prior to differential expression analysis.

Figure 2: GO enrichment bar plot showing the top 10 enriched Biological Process terms.

Figure 3: KEGG pathway diagram of the TNF signaling pathway, with upregulated genes colored red and downregulated genes colored blue.   
Software Versions 

<table><tr><td>Software</td><td>Version</td><td>Purpose</td></tr><tr><td>R</td><td>4.3.0</td><td>Statistical computing environment</td></tr><tr><td>DESeq2</td><td>1.42.0</td><td>Differential expression analysis</td></tr><tr><td>ggplot2</td><td>3.5.0</td><td>Data visualization</td></tr><tr><td>apeglm</td><td>1.24.0</td><td>Log2 fold change shrinkage</td></tr><tr><td>clusterProfiler</td><td>—</td><td>GO enrichment analysis</td></tr><tr><td>pathview</td><td>—</td><td>KEGG pathway visualization</td></tr></table>

# Results

# Differential Expression

DESeq2 identified 6 significantly differentially expressed genes (padj < 0.05):

Table 1: Differential Expression Results 

<table><tr><td>Gene</td><td>log2FC</td><td>padj</td><td>Direction</td></tr><tr><td>IL6</td><td>3.0</td><td>0.0003</td><td>Upregulated</td></tr><tr><td>TNF</td><td>2.5</td><td>0.001</td><td>Upregulated</td></tr><tr><td>CXCL8</td><td>2.2</td><td>0.002</td><td>Upregulated</td></tr><tr><td>IL1B</td><td>2.0</td><td>0.005</td><td>Upregulated</td></tr><tr><td>BCL2</td><td>-2.2</td><td>0.0008</td><td>Downregulated</td></tr><tr><td>MCL1</td><td>-1.8</td><td>0.003</td><td>Downregulated</td></tr></table>

The complete differential expression results for all 20 genes are available in Supplementary Table S2.

# GO Enrichment

Gene Ontology enrichment analysis of the 6 significant genes revealed enrichment for pathways related to inflammatory response, cytokine signaling, and apoptotic regulation.

Table 2: Top 5 GO Biological Process Terms 

<table><tr><td>GO Term</td><td>Description</td><td>GeneRatio</td><td>p.adjust</td></tr><tr><td>GO:0006954</td><td>inflammatory response</td><td>4/6</td><td>0.0002</td></tr><tr><td>GO:0019221</td><td>cytokine-mediated signaling pathway</td><td>4/6</td><td>0.0005</td></tr><tr><td>GO:0071345</td><td>cellular response to cytokine stimulus</td><td>3/6</td><td>0.001</td></tr><tr><td>GO:0043067</td><td>regulation of programmed cell death</td><td>3/6</td><td>0.003</td></tr><tr><td>GO:0006915</td><td>apoptotic process</td><td>3/6</td><td>0.005</td></tr></table>

Significance threshold: q-value < 0.05 (Benjamini-Hochberg adjusted)

# Figure 1: Volcano Plot

Figure 1 is a volcano plot showing -log10(adjusted p-value) vs log2 fold change for all genes passing the expression filter. The four upregulated genes (IL6, TNF, CXCL8, IL1B) appear in the upper-right quadrant. The two downregulated genes (BCL2, MCL1) appear in the upper-left quadrant. The remaining 14 genes cluster near the origin.

# Figure 2: GO Enrichment Bar Plot

Figure 2 is a bar plot of the top 10 enriched GO Biological Process terms, ordered by -log10(q-value). Terms related to inflammatory response and cytokine signaling show the strongest enrichment.

# Figure 3: KEGG Pathway Diagram

Figure 3 is a KEGG pathway diagram of the TNF signaling pathway (hsa04668). Upregulated genes (IL6, TNF, CXCL8, IL1B) are shown in red, and downregulated genes (BCL2, MCL1) are shown in blue, confirming pathway-level dysregulation consistent with the GO enrichment results.

# Data Availability

The count matrix is available as Supplementary Table S1 (counts.csv), containing 20 rows (genes) and 6 columns (samples). The dataset is also deposited at GEO under accession GSE99999.

The complete differential expression results are provided in Supplementary Table S2.

The analysis script is available at https://github.com/example/drug-response-analysis.

# References

1. Love, M.I., Huber, W., & Anders, S. (2014). Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. Genome Biology, 15(12), 550.   
2. Yu, G., Wang, L.G., Han, Y., & He, Q.Y. (2012). clusterProfiler: an R package for comparing biological themes among gene clusters. OMICS, 16(5), 284-287.   
3. Luo, W., & Brouwer, C. (2013). Pathview: an R/Bioconductor package for pathway-based data integration and visualization. Bioinformatics, 29(14), 1830-1831.