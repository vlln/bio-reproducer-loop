# Reproduction Plan: RNA-Seq Transcriptome Profiling Identifies CRISPLD2 as a Glucocorticoid Responsive Gene

## Paper Metadata

- **Title:** RNA-Seq Transcriptome Profiling Identifies CRISPLD2 as a Glucocorticoid Responsive Gene that Modulates Cytokine Function in Airway Smooth Muscle Cells
- **Authors:** Blanca E. Himes, Xiaofeng Jiang, Peter Wagner, Ruoxi Hu, Qiyu Wang, Barbara Klanderman, Reid M. Whitaker, Qingling Duan, Jessica Lasky-Su, Christina Nikolos, William Jester, Martin Johnson, Reynold A. Panettieri, Kelan G. Tantisira, Scott T. Weiss, Quan Lu
- **DOI:** 10.1371/journal.pone.0099625
- **PMID:** 24926665
- **PMCID:** PMC4057123
- **Journal:** PLOS ONE, 2014, Volume 9, Issue 6, e99625
- **Organism:** Homo sapiens

## Experimental Design

- **Sample source:** 4 primary human airway smooth muscle (ASM) cell lines
- **Treatment group:** 1 µM dexamethasone for 18 hours (4 samples)
- **Control group:** Untreated (4 samples)
- **Total samples:** 8
- **Design type:** Paired design (each cell line serves as its own control, accounted for by `~ cell + dex` in the model)
- **Data source:** GEO accession GSE52778 / Bioconductor `airway` package
- **Data format:** Count matrix (RangedSummarizedExperiment), ~64,000 transcripts

## Claims to Reproduce

### Claim 1: Number of Differentially Expressed Genes (DEGs)

- **Claim:** 316 genes are significantly differentially expressed between dexamethasone-treated and untreated ASM cells at Benjamini-Hochberg adjusted p-value < 0.05.
- **Reproduction approach:** Run DESeq2 with the design formula `~ cell + dex`, extract results with `alpha = 0.05`, and count the number of genes with `padj < 0.05`.
- **Validation:** The count of DEGs should be 316.

### Claim 2: Direction and Significance of Known Glucocorticoid-Responsive Genes

- **Claim:** The following genes are differentially expressed in the specified direction:

| Gene | Expected Direction |
|------|-------------------|
| DUSP1 | Upregulated (log2FoldChange > 0, padj < 0.05) |
| KLF15 | Upregulated (log2FoldChange > 0, padj < 0.05) |
| PER1 | Upregulated (log2FoldChange > 0, padj < 0.05) |
| TSC22D3 (GILZ) | Upregulated (log2FoldChange > 0, padj < 0.05) |
| CRISPLD2 | Upregulated (log2FoldChange > 0, padj < 0.05) |
| CCDC69 | Upregulated (log2FoldChange > 0, padj < 0.05) |
| C7 | Downregulated (log2FoldChange < 0, padj < 0.05) |

- **Reproduction approach:** Extract DESeq2 results for each of these genes and verify direction and significance.
- **Validation:** Each gene's log2FoldChange sign matches the expected direction and padj < 0.05.

### Claim 3: CRISPLD2 as a Glucocorticoid-Responsive Gene

- **Claim:** CRISPLD2 is significantly upregulated upon dexamethasone treatment, identifying it as a glucocorticoid-responsive gene and an asthma pharmacogenetics candidate.
- **Reproduction approach:** Verify CRISPLD2 is among the significant DEGs with positive log2FoldChange.
- **Validation:** CRISPLD2 has padj < 0.05 and log2FoldChange > 0.

## Analysis Pipeline

### Step 1: Load Data

- Load the `airway` Bioconductor package, which provides the count matrix as a `RangedSummarizedExperiment` object.
- The data contains 8 samples (4 cell lines × 2 conditions) with ~64,000 transcripts.

### Step 2: Run DESeq2

- Create a `DESeqDataSet` with the design formula `~ cell + dex`.
- The factor `cell` (4 levels: N052611, N061011, N080611, N61311) accounts for the paired design.
- The factor `dex` (2 levels: treated, untreated) is the condition of interest.
- Run `DESeq()` with default parameters.

### Step 3: Extract Results

- Extract results using `results(dds, alpha = 0.05)`.
- Filter for genes with `padj < 0.05`.

### Step 4: Validate Claims

- Count the number of DEGs with `padj < 0.05` → should be 316.
- Extract results for the 7 genes of interest (DUSP1, KLF15, PER1, TSC22D3, CRISPLD2, CCDC69, C7) and verify direction and significance.

## Environment Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| R | ≥ 3.2 | Statistical computing environment |
| DESeq2 | ≥ 1.10 | Differential expression analysis |
| airway | Bioconductor package | Data source |

## Expected Outputs

1. A count of DEGs at padj < 0.05 (expected: 316)
2. A table of log2FoldChange and padj values for the 7 genes of interest
3. Confirmation that CRISPLD2 is significantly upregulated

## Data Availability

- **GEO:** GSE52778
- **Bioconductor:** `airway` package (`BiocManager::install("airway")`)
- **Size:** ~10 MB
- **Computation time:** < 1 minute