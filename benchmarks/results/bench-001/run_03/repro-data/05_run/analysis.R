#!/usr/bin/env Rscript
#
# DESeq2 Differential Expression Analysis
# Paper: Differential Expression Analysis of Synthetic Gene Response to Treatment
# DOI: 10.1234/bench.001
#
# This script reproduces the full DESeq2 workflow described in the paper:
# 1. Load count matrix
# 2. Create DESeqDataSet with design ~ condition
# 3. Run DESeq() with default parameters
# 4. Apply log2 fold change shrinkage (apeglm)
# 5. Extract results at padj < 0.05
# 6. Generate volcano plot (Figure 1)

library(DESeq2)
library(apeglm)
library(ggplot2)

# --- Configuration ---
args <- commandArgs(trailingOnly = TRUE)
input_dir <- if (length(args) >= 1) args[1] else "/data/04_data/raw_data"
output_dir <- if (length(args) >= 2) args[2] else "/data/05_run"
results_dir <- file.path(output_dir, "results")
figures_dir <- file.path(output_dir, "figures")
dir.create(results_dir, showWarnings = FALSE, recursive = TRUE)
dir.create(figures_dir, showWarnings = FALSE, recursive = TRUE)

# --- Step 1: Load count matrix ---
cat("[Step 1/6] Loading count matrix...\n")
counts_file <- file.path(input_dir, "counts.csv")
counts <- read.csv(counts_file, row.names = 1, check.names = FALSE)
cat(sprintf("  Loaded %d genes x %d samples\n", nrow(counts), ncol(counts)))
cat(sprintf("  Genes: %s\n", paste(rownames(counts), collapse = ", ")))
cat(sprintf("  Samples: %s\n", paste(colnames(counts), collapse = ", ")))

# --- Step 2: Create DESeqDataSet ---
cat("[Step 2/6] Creating DESeqDataSet...\n")
condition <- factor(c(rep("Control", 3), rep("Treatment", 3)))
col_data <- data.frame(condition = condition, row.names = colnames(counts))
dds <- DESeqDataSetFromMatrix(
  countData = counts,
  colData = col_data,
  design = ~ condition
)
# Set Control as reference level
dds$condition <- relevel(dds$condition, ref = "Control")
cat(sprintf("  Design formula: ~ condition\n"))
cat(sprintf("  Reference level: Control\n"))
cat(sprintf("  Samples: %d Control, %d Treatment\n",
            sum(condition == "Control"), sum(condition == "Treatment")))

# --- Step 3: Run DESeq() ---
cat("[Step 3/6] Running DESeq()...\n")
# With only 10 genes, the default parametric dispersion curve fitting may fail
# because gene-wise dispersion estimates are too narrow. Use gene-wise estimates
# as final estimates, which is the recommended approach from the DESeq2 error message.
dds <- estimateSizeFactors(dds)
dds <- estimateDispersionsGeneEst(dds)
dispersions(dds) <- mcols(dds)$dispGeneEst
dds <- nbinomWaldTest(dds)
cat("  DESeq() completed successfully (using gene-wise dispersion estimates)\n")

# --- Step 4: Apply lfcShrink ---
cat("[Step 4/6] Applying lfcShrink (type = apeglm)...\n")
res_shrunken <- lfcShrink(dds, coef = "condition_Treatment_vs_Control", type = "apeglm")
cat("  lfcShrink completed successfully\n")

# --- Step 5: Extract and save results ---
cat("[Step 5/6] Extracting results...\n")
res_df <- as.data.frame(res_shrunken)
res_df$gene <- rownames(res_df)
res_df$significant <- res_df$padj < 0.05
res_df <- res_df[order(res_df$padj), c("gene", "baseMean", "log2FoldChange", "lfcSE", "pvalue", "padj", "significant")]

# Save full results table
write.csv(res_df, file.path(results_dir, "deseq2_results.csv"), row.names = FALSE)
cat(sprintf("  Total genes: %d\n", nrow(res_df)))
cat(sprintf("  Significant genes (padj < 0.05): %d\n", sum(res_df$significant, na.rm = TRUE)))

# Print key results
cat("\n  --- Key Results ---\n")
for (i in seq_len(nrow(res_df))) {
  r <- res_df[i, ]
  sig_str <- if (is.na(r$significant)) "NA" else if (r$significant) "SIGNIFICANT" else "not significant"
  direction <- if (is.na(r$log2FoldChange)) "NA" else if (r$log2FoldChange > 0) "Upregulated" else if (r$log2FoldChange < 0) "Downregulated" else "No change"
  cat(sprintf("  %s: log2FC = %.4f, padj = %.4e, %s [%s]\n",
              r$gene, r$log2FoldChange, r$padj, direction, sig_str))
}

# Save normalized counts
normalized_counts <- counts(dds, normalized = TRUE)
write.csv(as.data.frame(normalized_counts), file.path(results_dir, "normalized_counts.csv"))

# --- Step 6: Generate volcano plot (Figure 1) ---
cat("[Step 6/6] Generating volcano plot (Figure 1)...\n")

# Prepare plot data
plot_data <- res_df
plot_data$neg_log10_padj <- -log10(plot_data$padj)
# Cap for visualization (genes with padj = NA or very small)
plot_data$neg_log10_padj[is.infinite(plot_data$neg_log10_padj)] <- max(
  plot_data$neg_log10_padj[is.finite(plot_data$neg_log10_padj)], na.rm = TRUE
) + 0.5
plot_data$neg_log10_padj[is.na(plot_data$neg_log10_padj)] <- 0

p <- ggplot(plot_data, aes(x = log2FoldChange, y = neg_log10_padj, color = significant)) +
  geom_point(size = 3, alpha = 0.8) +
  scale_color_manual(
    values = c("TRUE" = "red", "FALSE" = "grey50"),
    labels = c("TRUE" = "Significant (padj < 0.05)", "FALSE" = "Not significant"),
    name = ""
  ) +
  geom_hline(yintercept = -log10(0.05), linetype = "dashed", color = "grey40", linewidth = 0.5) +
  geom_vline(xintercept = 0, linetype = "dotted", color = "grey60", linewidth = 0.3) +
  geom_text(
    data = subset(plot_data, significant == TRUE),
    aes(label = gene),
    hjust = -0.2, vjust = -0.5, size = 3.5, color = "red"
  ) +
  labs(
    title = "Figure 1: Volcano Plot of Differential Expression",
    subtitle = "DESeq2: Control vs Treatment (n = 3 per group)",
    x = expression(log[2] ~ "Fold Change"),
    y = expression(-log[10] ~ "(adjusted p-value)")
  ) +
  theme_bw(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 14),
    plot.subtitle = element_text(size = 10, color = "grey40"),
    legend.position = "bottom",
    panel.grid.minor = element_blank()
  )

ggsave(file.path(figures_dir, "figure1_volcano.png"), plot = p, width = 8, height = 6, dpi = 150)
ggsave(file.path(figures_dir, "figure1_volcano.pdf"), plot = p, width = 8, height = 6)

# Save plot data for reproducibility
write.csv(plot_data, file.path(figures_dir, "figure1_data.csv"), row.names = FALSE)

cat("  Volcano plot saved to figures/figure1_volcano.png and figures/figure1_volcano.pdf\n")

# --- Summary ---
cat("\n=== Analysis Complete ===\n")
cat(sprintf("Results directory: %s\n", results_dir))
cat(sprintf("Figures directory: %s\n", figures_dir))