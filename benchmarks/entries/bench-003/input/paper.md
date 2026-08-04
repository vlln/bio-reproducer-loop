# Paired RNA-seq Analysis of a Synthetic Treatment Response

**Authors:** A. Researcher, B. Scientist

**DOI:** 10.1234/bench.003

## Abstract

We measured RNA-seq counts in four donors before and after Treatment. Differential expression was
estimated with DESeq2 using donor as a blocking factor. Gene_P was induced and Gene_Q was
repressed after treatment; the remaining genes did not show material changes.

## Methods

The count matrix in `data/counts.csv` contains six genes and eight samples. Each donor contributes
one matched Control and one matched Treatment sample. Analyze raw integer counts in R with DESeq2
using `~ donor + condition`, where donor has four levels and condition is Control/Treatment. Use
the Treatment versus Control contrast, adjust p-values with the default Benjamini-Hochberg method,
and call adjusted p-value below 0.05 significant. Record the R and DESeq2 versions used.

Generate a volcano plot with log2 fold change on the x-axis and -log10 adjusted p-value on the
y-axis. Highlight significant genes.

## Results

Gene_P increased approximately two-fold on the log2 scale (adjusted p-value below 0.01). Gene_Q
decreased approximately two-fold on the log2 scale (adjusted p-value below 0.01). At least these
two genes were significant after donor blocking. The paired design is required because baseline
counts vary substantially across donors.

## Data Availability

Supplementary Table S1 is bundled as `data/counts.csv`. The synthetic DOI is intentionally not
resolvable; the bundled paper and table are the authoritative inputs for this L3 benchmark.
