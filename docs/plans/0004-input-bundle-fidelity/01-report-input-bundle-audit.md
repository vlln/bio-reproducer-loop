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

# 总体发现（初始审计）

| 项目 | 观察 |
|------|------|
| 输入形状 | 初始审计时六个 entry 均为 paper + 小型 counts，且没有 supplementary/、code/、resources/ 或 runner-only provenance lock |
| 构造论文 | 初始审计时 bench-001/002/004/005/006 同时提供 Markdown 和 PDF，但没有声明两者的权威/派生关系或生成方式 |
| 图像断链 | 五个构造 Markdown 共引用 7 个 `figures/*.png`，InputBundle 中没有对应文件 |
| Supplementary | 构造论文普遍引用 S1/S2 和 analysis script；只有 counts 数据存在，其他材料无文件或状态记录 |
| 代码 | 构造论文引用 `github.com/example/...`，metadata 声明 repo_gone，但 InputBundle 无核查记录 |
| 数据来源 | 多个构造 entry 声称虚构 GEO accession；synthetic/real/injected 的公开 provenance 不完整 |
| bench-003 | 声明 real_published/pdf，实际没有 PDF，只有 82 行人工摘要和 357 基因子集 |
| 未声明文件 | bench-006 暴露 `.counts_full.csv`；它与 `counts.csv` SHA256 完全一致，属于无语义重复文件 |

# Entry 审计

| Entry | 当前材料 | 确认缺口/冲突 | 建议处置 | 风险 |
|-------|----------|---------------|----------|------|
| bench-001 | constructed MD，10-gene counts，runner-only bundle lock | 已移除来源和转换过程不明的冗余 PDF；bundle 登记 primary paper、S1/counts、DOI、GEO、代码和缺图状态 | 自动 gate 已通过；发布前复核外部资源的可观察行为 | medium |
| bench-002 | constructed MD，20-gene counts，runner-only bundle lock | 已移除无 provenance PDF；bundle 登记 S1、缺失 S2、3 个缺图、DOI、GEO 和代码；修正 supplementary 与 KEGG ID 位置 | 自动 gate 已通过；发布前人工复核场景可观察性 | medium |
| bench-003 | 82 行 MD，357-gene counts + samples | metadata 声明 real_published/pdf，但 PDF 不存在；摘要将真实论文整理为 DESeq2 workflow；输入声称约 64k transcripts，却只提供 357 基因且无裁剪 provenance；无 supplementary/code/source snapshot | 原地重建为真实 L4；获取原始发布物与 cited resources；核查真实方法链；重建 data scope 和 oracle | critical |
| bench-004 | constructed MD，50-gene counts，runner-only bundle lock | 已将 data_source 修正为 synthetic；GSE88888 保留为可观察的错误 locator；缺图、S2 和代码均有 disposition | 自动 gate 已通过；发布前人工复核跨语言 scope | medium |
| bench-005 | constructed MD，30-gene counts，runner-only bundle lock | 已登记 DOI、错误 GEO、失效代码、缺失 S2 和 2 个缺图；metadata 修正 wrong_accession | 自动 gate 已通过；环境冲突仍由 private rubric 审查 | medium |
| bench-006 | constructed MD，11-gene TSV，runner-only bundle lock | 已删除与 counts 完全相同的隐藏副本和无 provenance PDF；登记实际 TSV、错误 GEO、DataIntegrityR、代码、S2 和缺图 | 自动 gate 已通过；损坏输入不可恢复性仍需人工确认 | high |

# 设计结论

1. 当前问题不是顶层 `input/` 结构本身，而是缺少层级规则、resource inventory 和 provenance。
2. `supplementary: none` 不能与论文正文中的 S1/S2 引用并存，除非 bundle lock 解释其状态。
3. constructed paper 可以使用虚构资源，但必须让公开材料自洽；故障注入原因保持私有。
4. bench-003 当前只能证明一个 airway-derived DESeq2 子任务，不能作为真实论文 L4。
5. 在 source audit、bundle validator 和 entry 修复完成前，现有分数不得建立 release baseline。

# 实施进度

- `bundle.schema.json` 和无外部 schema 运行时依赖的 validator 已实现。
- `bench-run validate-entry` 对 bench-001/002/004/005/006 通过；bench-003 因没有 bundle lock 被拒绝。
- Runner 在创建结果或调用 adapter 前校验 entry；staging 会清除旧目录并只复制 `input/`。
- AC-0006 的 hash、dotfile、path escape、oracle 字段、派生 provenance、metadata 冲突和
  control-plane 残留已有确定性测试。
- OS/container 级文件系统强隔离不在本次 staging contract 的证明范围内。

# 外部资源核查

2026-07-21 的实际查询结果：

- 构造 entry 的四个 `10.1234/bench.*` DOI 和四个 `github.com/example/...` 仓库均返回 HTTP 404。
- GSE99999、GSE88888、GSE77777、GSE66666 均为公开 GEO series，但分别对应系统性硬化症、
  Parkinson 病、poly(I:C) MEF 和拟南芥研究，与构造论文主题不匹配。
- `DataIntegrityR` 的 CRAN metadata 与 R-universe package 查询均返回 HTTP 404。

# 待外部核查

- Himes et al. 2014 的原始 PDF/XML、PLOS/PMC supplementary 清单与许可。
- 论文实际使用的统计方法、代码公开情况和 GSE52778 文件清单。
- airway Bioconductor 数据与论文原始分析输入/方法的关系。
- 五个构造 entry 的 unavailable/external 状态在目标运行环境中是否保持相同可观察行为。
