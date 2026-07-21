---
title: Report 004 — 现有 InputBundle 材料审计
description: 记录 bench-001 至 bench-006 的论文原件、派生表示、补充材料、代码、数据、图像和 provenance 缺口。
type: report
status: draft
created: 2026-07-20T00:00:00Z
---

# 审计范围

本报告只检查当前 Git workspace 中 staged InputBundle 的可观察事实，不访问外部网络，
不判断真实论文页面最终有哪些附件。外部论文、supplementary、仓库和 accession 的存在性
均标记为待后续 source audit。

# 总体发现

| 项目 | 观察 |
|------|------|
| 输入形状 | 六个 entry 均为 paper + 小型 counts；没有 supplementary/、code/、resources/ 或 provenance manifest |
| 构造论文 | bench-001/002/004/005/006 同时提供 Markdown 和 PDF，但没有声明两者的权威/派生关系或生成方式 |
| 图像断链 | 五个构造 Markdown 共引用 7 个 `figures/*.png`，InputBundle 中没有对应文件 |
| Supplementary | 构造论文普遍引用 S1/S2 和 analysis script；只有 counts 数据存在，其他材料无文件或状态记录 |
| 代码 | 构造论文引用 `github.com/example/...`，metadata 声明 repo_gone，但 InputBundle 无核查记录 |
| 数据来源 | 多个构造 entry 声称虚构 GEO accession；synthetic/real/injected 的公开 provenance 不完整 |
| bench-003 | 声明 real_published/pdf，实际没有 PDF，只有 82 行人工摘要和 357 基因子集 |
| 未声明文件 | bench-006 暴露 `.counts_full.csv`；它与 `counts.csv` SHA256 完全一致，属于无语义重复文件 |

# Entry 审计

| Entry | 当前材料 | 确认缺口/冲突 | 建议处置 | 风险 |
|-------|----------|---------------|----------|------|
| bench-001 | constructed MD/PDF，10-gene counts | Markdown 引用 volcano PNG、S1、GSE99999 和代码仓库；PNG/代码/availability record 缺失；S1 与 data/counts 的关系未声明 | 建立 L3 manifest；声明 PDF/MD 派生关系；将 counts 同时映射为 data/S1；补 figure 或明确论文表示；记录虚构 accession/repo 的可观察状态 | medium |
| bench-002 | constructed MD/PDF，20-gene counts | 引用 3 个 figure、S1/S2 和代码；只有 counts；metadata 同时写 supplementary:none 与 missing_supplementary:true | 明确缺失 supplementary 是否为测试意图；补齐或建立 unavailable record；修正 complexity profile | high |
| bench-003 | 82 行 MD，357-gene counts + samples | metadata 声明 real_published/pdf，但 PDF 不存在；摘要将真实论文整理为 DESeq2 workflow；输入声称约 64k transcripts，却只提供 357 基因且无裁剪 provenance；无 supplementary/code/source snapshot | 原地重建为真实 L4；获取原始发布物与 cited resources；核查真实方法链；重建 data scope 和 oracle | critical |
| bench-004 | constructed MD/PDF，50-gene counts | 声明 data_source:real 和虚构 GSE88888；引用 2 个 figure、S1/S2、Python/R scripts，均未完整打包 | 保持 L3 constructed；把“real data”改为可证实来源或 synthetic；补齐跨语言脚本材料/状态 | high |
| bench-005 | constructed MD/PDF，30-gene counts | 引用 2 个 figure、S1/S2、analysis.R、GSE77777；仅 counts 存在；环境冲突与材料遗漏混在一起 | 将环境漂移和资源缺失拆成明确注入；manifest 登记每项 cited resource | high |
| bench-006 | constructed MD/PDF，两个相同的 11-row tab-delimited `.csv` | 论文声称 15 genes 和 DataIntegrityR；oracle 声明 truncated/format mismatch；隐藏 dotfile 与公开文件完全相同，不是 full recovery source；引用 figure、S2、script 均缺失 | 删除无语义 dotfile 或重新设计恢复资源；manifest 明确损坏输入；不要把隐藏文件当隐式答案 | critical |

# 设计结论

1. 当前问题不是顶层 `input/` 结构本身，而是缺少层级规则、resource inventory 和 provenance。
2. `supplementary: none` 不能与论文正文中的 S1/S2 引用并存，除非 manifest 解释其状态。
3. constructed paper 可以使用虚构资源，但必须让公开材料自洽；故障注入原因保持私有。
4. bench-003 当前只能证明一个 airway-derived DESeq2 子任务，不能作为真实论文 L4。
5. 在 source audit、manifest validator 和 entry 修复完成前，现有分数不得建立 release baseline。

# 待外部核查

- Himes et al. 2014 的原始 PDF/XML、PLOS/PMC supplementary 清单与许可。
- 论文实际使用的统计方法、代码公开情况和 GSE52778 文件清单。
- airway Bioconductor 数据与论文原始分析输入/方法的关系。
- 构造 PDF 是否由 Markdown 生成、是否实际嵌入 Markdown 中断链的 figure。
- 每个构造场景中 fake DOI/GEO/repository 的预期公开语义。
