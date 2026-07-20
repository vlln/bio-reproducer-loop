# Reproduction Plan: Mouse Brain Region Transcriptomics

Status: COMPLETE

Analyze the local `data/counts.csv` matrix containing 50 genes and 16 samples from
Cortex, Hippocampus, Striatum and Thalamus. Use Python 3.10 with pandas for input QC,
then R 4.3 with DESeq2 and design `~ region` for all six pairwise contrasts. Produce
per-contrast CSV result tables, a Cortex-vs-Thalamus volcano plot and a top-gene heatmap.

The referenced GEO accession and author repository are not authoritative; the local
count matrix is the permitted input. Missing supplementary results must be recomputed.
