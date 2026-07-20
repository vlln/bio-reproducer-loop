# RNA-Seq Transcriptome Profiling Identifies CRISPLD2 as a Glucocorticoid Responsive Gene that Modulates Cytokine Function in Airway Smooth Muscle Cells

**Authors:** Blanca E. Himes, Xiaofeng Jiang, Peter Wagner, Ruoxi Hu, Qiyu Wang, Barbara Klanderman, Reid M. Whitaker, Qingling Duan, Jessica Lasky-Su, Christina Nikolos, William Jester, Martin Johnson, Reynold A. Panettieri, Kelan G. Tantisira, Scott T. Weiss, Quan Lu

**DOI:** 10.1371/journal.pone.0099625

**PMID:** 24926665 | **PMCID:** PMC4057123

**Journal:** PLOS ONE, 2014, Volume 9, Issue 6, e99625

---

## Abstract

**Background:** Asthma is a chronic inflammatory respiratory disease that affects over 300 million people worldwide. Glucocorticoids are a mainstay therapy for asthma because they exert anti-inflammatory effects in multiple lung tissues, including the airway smooth muscle (ASM). However, the mechanism by which glucocorticoids suppress inflammation in ASM remains poorly understood.

**Methods:** Using RNA-Seq, a high-throughput sequencing method, we characterized transcriptomic changes in four primary human ASM cell lines that were treated with dexamethasone (1 µM for 18 hours). Differential expression analysis was performed using DESeq2. Based on a Benjamini-Hochberg corrected p-value < 0.05, we identified 316 differentially expressed genes.

**Results:** 316 differentially expressed genes were identified, including both well known (DUSP1, KLF15, PER1, TSC22D3/GILZ) and less investigated (C7, CCDC69, CRISPLD2) glucocorticoid-responsive genes. CRISPLD2, which encodes a secreted protein previously implicated in lung development and endotoxin regulation, was found to have SNPs that were moderately associated with inhaled corticosteroid resistance and bronchodilator response among asthma patients.

**Conclusions:** Our findings offer a comprehensive view of the effect of a glucocorticoid on the ASM transcriptome and identify CRISPLD2 as an asthma pharmacogenetics candidate gene that regulates anti-inflammatory effects of glucocorticoids in the ASM.

---

## Methods

### Sample Preparation

RNA-seq was performed on 4 primary human ASM cell lines:
- **Control group:** untreated (4 samples)
- **Dexamethasone-treated group:** 1 µM dexamethasone for 18 hours (4 samples)

Total: 8 samples in a paired design (each cell line serves as its own control).

### Data Processing

Count data were analyzed using DESeq2 in R. The analysis followed the standard DESeq2 workflow:
1. Load count matrix from RangedSummarizedExperiment (airway Bioconductor package)
2. Create DESeqDataSet with design formula `~ cell + dex`
3. Run DESeq2 with default parameters
4. Extract results at adjusted p-value < 0.05 (Benjamini-Hochberg correction)

The paired design accounts for the fact that each cell line was measured under both conditions.

### Software Versions

| Software | Version | Purpose |
|----------|---------|---------|
| R | ≥ 3.2 | Statistical computing environment |
| DESeq2 | ≥ 1.10 | Differential expression analysis |

---

## Results

### Differential Expression

DESeq2 identified 316 significantly differentially expressed genes (padj < 0.05). Key dexamethasone-responsive genes include:

| Gene | Direction | Known Role |
|------|-----------|------------|
| DUSP1 | Upregulated | Dual specificity phosphatase 1 |
| KLF15 | Upregulated | Krüppel-like factor 15 |
| PER1 | Upregulated | Period circadian regulator 1 |
| TSC22D3 (GILZ) | Upregulated | Glucocorticoid-induced leucine zipper |
| CRISPLD2 | Upregulated | Cysteine-rich secretory protein LCCL domain containing 2 |
| C7 | Downregulated | Complement C7 |
| CCDC69 | Upregulated | Coiled-coil domain containing 69 |

---

## Data Availability

The RNA-seq count data are available at GEO under accession **GSE52778** and in the **airway** Bioconductor package (`library(airway)`).

The dataset contains 8 samples (4 cell lines × 2 conditions) with ~64,000 transcripts.

---

## References

1. Love, M.I., Huber, W., & Anders, S. (2014). Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. *Genome Biology*, 15(12), 550.
2. Himes, B.E., et al. (2014). RNA-Seq transcriptome profiling identifies CRISPLD2 as a glucocorticoid responsive gene. *PLOS ONE*, 9(6), e99625.