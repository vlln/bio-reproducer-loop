# Validation Checks Plan

## Check Derivation

Checks are derived from plan.md Expected Results, Paper Claims, Key Findings, and Reproduction Target sections.

### From Expected Results table:
- 6 significant DE genes (IL6, TNF, CXCL8, IL1B up; BCL2, MCL1 down) → R1–R7
- Specific log2FC and padj values for each gene → R1–R6
- GO terms: inflammatory response, cytokine signaling, apoptotic process → R9, R10
- Volcano plot pattern → F1
- GO bar plot → F2
- KEGG pathway diagram → F3
- Pathway-level conclusions → F4

### From Paper Claims:
- Pre-filtering threshold → D5
- DESeq2 pipeline → Q1
- GO enrichment → Q2
- KEGG visualization → Q3
- Software versions → Q4

### From Reproduction Target:
- Figure 1 (volcano) → F1
- Figure 2 (GO bar plot) → F2
- Figure 3 (KEGG) → F3
- Quantitative DE results → R1–R8
- Qualitative conclusions → F4

## Check List

| Check ID | Dimension | Metric | Type | Expected | Source |
|----------|-----------|--------|------|----------|--------|
| D1 | Data Integrity | Input gene count | Auto | 20 | plan.md Study Design |
| D2 | Data Integrity | Input sample count | Auto | 6 | plan.md Study Design |
| D3 | Data Integrity | Output files present and non-empty | Auto | All expected files | plan.md Expected Results |
| D4 | Data Integrity | DE results table row count | Auto | 20 | plan.md Study Design |
| D5 | Data Integrity | Pre-filtering outcome | Auto | Genes with mean < 10 removed | plan.md Figure 1 legend |
| Q1 | Process Quality | DESeq2 DE analysis completed | Auto | success | plan.md Methods |
| Q2 | Process Quality | GO enrichment completed | Auto | success with enriched terms | plan.md Methods |
| Q3 | Process Quality | KEGG pathway visualization completed | Auto | success | plan.md Methods |
| Q4 | Process Quality | Software versions match paper | Auto | R 4.3.0, DESeq2 1.42.0, etc. | plan.md Software Versions |
| Q5 | Process Quality | Pipeline stages executed in order | Auto | DE → GO → KEGG | plan.md Method Overview |
| Q6 | Process Quality | Gene ID conversion performed | Auto | true | plan.md Code and Data Availability |
| R1 | Quantitative Concordance | IL6 log2FC | Auto | 3.0 | plan.md Expected Results |
| R2 | Quantitative Concordance | TNF log2FC | Auto | 2.5 | plan.md Expected Results |
| R3 | Quantitative Concordance | CXCL8 log2FC | Auto | 2.2 | plan.md Expected Results |
| R4 | Quantitative Concordance | IL1B log2FC | Auto | 2.0 | plan.md Expected Results |
| R5 | Quantitative Concordance | BCL2 log2FC | Auto | -2.2 | plan.md Expected Results |
| R6 | Quantitative Concordance | MCL1 log2FC | Auto | -1.8 | plan.md Expected Results |
| R7 | Quantitative Concordance | Direction of regulation (6 core genes) | Auto | IL6/TNF/CXCL8/IL1B up; BCL2/MCL1 down | plan.md Key Findings |
| R8 | Quantitative Concordance | Significant gene count | Auto | 6 | plan.md Expected Results |
| R9 | Quantitative Concordance | GO term IDs match paper | Auto | GO:0006954, GO:0019221 | plan.md Expected Results |
| R10 | Quantitative Concordance | GO thematic concordance | Manual | Inflammatory, cytokine, apoptotic terms | plan.md Key Findings |
| F1 | Figure and Finding | Volcano plot pattern | Visual | 4 upper-right, 2 upper-left, 14 near origin | plan.md Reproduction Target |
| F2 | Figure and Finding | GO bar plot top terms | Visual | Top 10 BP terms, inflammatory at top | plan.md Reproduction Target |
| F3 | Figure and Finding | KEGG pathway diagram | Visual | hsa04668 with up=red, down=blue | plan.md Reproduction Target |
| F4 | Figure and Finding | Overall conclusion | Manual | Inflammatory induction + anti-apoptotic suppression | plan.md Key Findings |

## Dimension Weights

Default weights used (no adjustment):
- Data Integrity: 25%
- Process Quality: 25%
- Quantitative Concordance: 30%
- Figure and Finding Reproduction: 20%
