# Paper: RNA-Seq Transcriptome Profiling Identifies CRISPLD2 as a Glucocorticoid Responsive Gene that Modulates Cytokine Function in Airway Smooth Muscle Cells

DOI: 10.1371/journal.pone.0099625

## Paper Understanding

### Research Question
What are the transcriptomic changes induced by dexamethasone treatment in primary human airway smooth muscle (ASM) cells?

### Study Design
- 4 primary human ASM cell lines
- 2 conditions: untreated (Control) vs dexamethasone-treated (1 µM, 18h)
- Paired design: each cell line measured under both conditions
- 8 samples total
- RNA-seq profiling of ~64,000 transcripts

### Method Overview
- Count matrix from RangedSummarizedExperiment (airway Bioconductor package)
- Differential expression with DESeq2
- Design formula: `~ cell + dex` (paired design, cell as blocking factor)
- Significance threshold: Benjamini-Hochberg adjusted p-value < 0.05
- 316 DEGs identified

### Key Findings
- 316 differentially expressed genes at padj < 0.05
- 4 well-known dexamethasone-responsive genes confirmed: DUSP1, KLF15, PER1, TSC22D3 (GILZ)
- 3 less investigated genes identified: C7, CCDC69, CRISPLD2
- CRISPLD2 validated as a novel glucocorticoid-responsive gene via qRT-PCR and Western blot
- CRISPLD2 knockdown increased IL1β-induced IL6 and IL8 expression

### Reproduction Target
Reproduce the differential expression analysis and verify that the 7 named dexamethasone-responsive genes (DUSP1, KLF15, PER1, TSC22D3, C7, CCDC69, CRISPLD2) are among the significant DEGs.

## Paper Claims

### Analysis Steps
1. Load data: `airway` Bioconductor package → RangedSummarizedExperiment → counts matrix
2. DE analysis: counts → DESeq2 (`~ cell + dex`) → normalized counts → DE results table
3. Filter: padj < 0.05 → significant DEGs
4. Verify: 7 named genes present in significant DEGs list

### Code and Data Availability
| Resource | URL/Identifier | Purpose | Location in Paper |
|----------|----------------|---------|-------------------|
| airway Bioconductor package | Bioconductor: airway | RNA-seq count data (8 samples) | Data Availability |
| GEO accession | GSE52778 | Raw and processed RNA-seq data | Data Availability |

### System Requirements
| Component | Requirement | Notes | Location in Paper |
|-----------|-------------|-------|-------------------|
| OS | Not specified | Linux/macOS compatible | — |
| Container runtime | Not specified | Docker assumed for bioconductor image | — |

### Environment Requirements
| Software | Version | Purpose | Source in Paper |
|----------|---------|---------|-----------------|
| R | ≥ 3.2 | Statistical computing | Methods |
| DESeq2 | ≥ 1.10 | Differential expression analysis | Methods |
| airway | latest | Data package (GSE52778) | Data Availability |

### Data Requirements
| Database | Accession | Samples | Type | Location in Paper |
|----------|-----------|---------|------|-------------------|
| GEO | GSE52778 | 8 | Count matrix (RNA-seq) | Data Availability |
| Bioconductor | airway | 8 | RangedSummarizedExperiment | Data Availability |

### Parameters
| Tool | Parameter | Value | From |
|------|-----------|-------|------|
| DESeq2 | design_formula | ~ cell + dex | Methods |
| DESeq2 | significance_threshold | padj < 0.05 | Methods |
| DESeq2 | design_type | paired (cell as blocking factor) | Methods |

### Expected Results
| Output | Expected Value |
|--------|----------------|
| Total DEGs (padj < 0.05) | 316 (approximate, version-dependent) |
| DUSP1 | Significantly upregulated |
| KLF15 | Significantly upregulated |
| PER1 | Significantly upregulated |
| TSC22D3 (GILZ) | Significantly upregulated |
| CRISPLD2 | Significantly upregulated |
| C7 | Significantly downregulated |
| CCDC69 | Significantly upregulated |

### Figure Reproduction Inventory
| Figure/Panel | Original Image | Caption/Source | Scientific Claim | Plot Type | Required Data | Author Plotting Code/Notebook | Expected Pattern | Source |
|--------------|----------------|----------------|------------------|-----------|---------------|-------------------------------|------------------|--------|
| N/A | — | — | — | — | — | — | No figure reproduction required | — |

## Source Files Reviewed
| File/URL | Type | Local Path | Status | Notes |
|----------|------|------------|--------|-------|
| paper.md | Paper (Markdown extract) | paper.md | Reviewed | Paper summary extracted from PLOS ONE publication; original PDF at https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0099625 |
| https://doi.org/10.1371/journal.pone.0099625 | DOI landing page | — | Reviewed via paperutils | PLOS ONE publisher page; open access |
| https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52778 | GEO record | — | Reviewed via paperutils | 8 samples, airway smooth muscle cells, dexamethasone treatment |
| https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4057123 | PMC full text | — | Available | Open access full text via PubMed Central |

## Supplementary Materials Inventory
| Item | Type | URL/Path | Mentioned In | Status | Notes |
|------|------|----------|-------------|--------|-------|
| No supplementary materials cited in paper extract | — | — | — | — | Paper does not reference supplementary files in the available extract |

## Resource Locations
| Resource | Type | URL/Identifier | Purpose | Location in Paper | Access Notes |
|----------|------|----------------|---------|-------------------|-------------|
| airway package | Bioconductor data package | Bioconductor: airway | RNA-seq count matrix (RangedSummarizedExperiment) | Data Availability | Install via `BiocManager::install("airway")`; ~10 MB |
| GSE52778 | GEO accession | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52778 | Raw and processed RNA-seq data | Data Availability | 8 samples; publicly accessible |
| PLOS ONE article | Publisher page | https://doi.org/10.1371/journal.pone.0099625 | Full paper PDF and HTML | — | Open access; freely available |
| PMC full text | PubMed Central | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4057123 | Full paper text | — | Open access; freely available |

## External Identifier Records
| Identifier | Database | Resolved Type | Title/Description | Linked IDs | Source API | Retrieved At |
|------------|----------|---------------|-------------------|------------|------------|-------------|
| 10.1371/journal.pone.0099625 | Crossref | Journal article | RNA-Seq Transcriptome Profiling Identifies CRISPLD2 as a Glucocorticoid Responsive Gene that Modulates Cytokine Function in Airway Smooth Muscle Cells | PMID: 24926665, PMCID: PMC4057123 | paperutils | — |
| 24926665 | PubMed | PMID | Himes BE et al. (2014) PLOS ONE 9(6): e99625 | DOI: 10.1371/journal.pone.0099625 | paperutils | — |
| PMC4057123 | PubMed Central | PMCID | Full text of Himes et al. 2014 | PMID: 24926665 | paperutils | — |
| GSE52778 | GEO | GEO Series | Dexamethasone effect on 4 primary human airway smooth muscle cell lines | 8 samples | paperutils | — |

## Source Conflicts And Gaps
| Item | Paper Statement | External Record | Issue |
|------|----------------|-----------------|-------|
| DESeq2 version | "≥ 1.10" | Published 2014; DESeq2 1.10 corresponds to Bioconductor 3.0 (Oct 2014) | Exact version at time of analysis unknown; modern DESeq2 versions will differ |
| R version | "≥ 3.2" | R 3.2 released April 2015, after paper publication | Version constraint may be post-hoc; paper likely used R 3.1.x |
| 316 DEGs | Paper reports 316 DEGs at padj < 0.05 | Modern DESeq2 may produce different count | DEG count expected to vary ±20% due to statistical method updates |
| No figure reproduction | Paper includes figures (volcano, etc.) but extract does not detail them | — | No figure reproduction required per benchmark design |

## Uncertainties
| Item | Issue | Source |
|------|-------|--------|
| Exact DESeq2 version | Paper published 2014; DESeq2 version at time was likely 1.6-1.10 | Methods |
| Exact R version | Paper published 2014; R version likely 3.1-3.2 | Methods |
| Total DEG count | 316 at padj < 0.05; may vary with DESeq2 version | Results |
| Pre-filtering | DESeq2 default pre-filtering may have been applied implicitly | Methods |
| Paper extract completeness | paper.md is a summary extract; full paper PDF may contain additional methodological details | — |