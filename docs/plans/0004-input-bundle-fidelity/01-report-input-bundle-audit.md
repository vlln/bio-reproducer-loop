---
title: Report 004 — 现有 InputBundle 材料审计
description: 记录首批六个 entry 的论文原件、派生表示、补充材料、代码、数据、图像和 provenance 缺口。
type: report
status: complete
created: 2026-07-20T00:00:00Z
---

# 审计范围

初始审计检查 Git workspace 中 staged InputBundle 的可观察事实；后续 source audit 核查了
构造 entry 的外部 locator，并从 PLOS/PMC、GEO、ENA 与 Taffeta 原始材料重建 bench-100。
最终审查逐项对照论文引用、bundle resource、实际文件、oracle scope 与自动门禁。

# 总体发现（初始审计）

| 项目 | 观察 |
|------|------|
| 输入形状 | 初始审计时六个 entry 均为 paper + 小型 counts，且没有 supplementary/、code/、resources/ 或 runner-only provenance lock |
| 构造论文 | 初始审计时 bench-001/002/004/005/006 同时提供 Markdown 和 PDF，但没有声明两者的权威/派生关系或生成方式 |
| 图像断链 | 五个构造 Markdown 共引用 7 个 `figures/*.png`，InputBundle 中没有对应文件 |
| Supplementary | 构造论文普遍引用 S1/S2 和 analysis script；只有 counts 数据存在，其他材料无文件或状态记录 |
| 代码 | 构造论文引用 `github.com/example/...`，metadata 声明 repo_gone，但 InputBundle 无核查记录 |
| 数据来源 | 多个构造 entry 声称虚构 GEO accession；synthetic/real/injected 的公开 provenance 不完整 |
| bench-100（审计时为 bench-003） | 声明 real_published/pdf，实际没有 PDF，只有 82 行人工摘要和 357 基因子集 |
| 未声明文件 | bench-006 暴露 `.counts_full.csv`；它与 `counts.csv` SHA256 完全一致，属于无语义重复文件 |

# Entry 审计

| Entry | 当前材料 | 确认缺口/冲突 | 建议处置 | 风险 |
|-------|----------|---------------|----------|------|
| bench-001 | constructed MD，10-gene counts，runner-only bundle lock | primary paper、S1/counts、DOI、GEO、代码和缺图均有 disposition | PASS；外部 locator 漂移保留为运行风险 | medium |
| bench-002 | constructed MD，20-gene counts，runner-only bundle lock | S1、缺失 S2、3 个缺图、DOI、GEO 和代码均有 disposition | PASS；缺失材料不作为隐藏答案 | medium |
| bench-100（原 bench-003） | 原始 PDF/XML、完整 PMC archive、GEO Cuffdiff/FPKM、ENA resolver 与 Taffeta snapshot | 另登记 GSE34313/GSE13168、历史工具链、iGenomes、DAVID 和两类 GWAS；计分 scope 不含 raw alignment、microarray、GWAS 与湿实验 | PASS；仅对 processed-output L4 scope 签字 | medium |
| bench-004 | constructed MD，50-gene counts，runner-only bundle lock | synthetic data、错误 GSE、缺图、S2 和代码均有 disposition | PASS；跨语言 scope 与 rubric 一致 | medium |
| bench-005 | constructed MD，30-gene counts，runner-only bundle lock | DOI、错误 GEO、失效代码、缺失 S2、缺图与公开方法冲突均可观察或有 disposition | PASS；环境冲突由公开 paper 暴露 | medium |
| bench-006 | constructed MD，11-row TSV with CSV extension，runner-only bundle lock | 行数、分隔符、错误 GEO、DataIntegrityR、代码、S2 和缺图均已核对 | PASS；不可恢复的 4 个缺失基因仍是预期降级边界 | high |

# 设计结论

1. 当前问题不是顶层 `input/` 结构本身，而是缺少层级规则、resource inventory 和 provenance。
2. `supplementary: none` 不能与论文正文中的 S1/S2 引用并存，除非 bundle lock 解释其状态。
3. constructed paper 可以使用虚构资源，但必须让公开材料自洽；故障注入原因保持私有。
4. bench-100 在旧编号 bench-003 下的输入只能证明 airway-derived DESeq2 子任务；该输入与旧 oracle 已删除，不能用于解释重建后的 L4 entry。
5. 在 source audit、bundle validator 和 entry 修复完成前，现有分数不得建立 release baseline。

# 实施进度

- `bundle.schema.json` 和无外部 schema 运行时依赖的 validator 已实现。
- `bench-run validate-entry` 对首批六个 entry 全部通过；bench-100 被识别为 L4。
- Runner 在创建结果或调用 adapter 前校验 entry；staging 会清除旧目录并只复制 `input/`。
- AC-0006 的 hash、dotfile、path escape、oracle 字段、派生 provenance、metadata 冲突和
  control-plane 残留已有确定性测试。
- bench-100 rubric 已增加确定性回归，覆盖 316 个显著基因、七个 DEX-induced 基因、
  CRISPLD2 效应值和 Cuffdiff/Taffeta 环境证据。
- OS/container 级文件系统强隔离不在本次 staging contract 的证明范围内。

# 外部资源核查

2026-07-21 的实际查询结果：

- 构造 entry 的四个 `10.1234/bench.*` DOI 和四个 `github.com/example/...` 仓库均返回 HTTP 404。
- GSE99999、GSE88888、GSE77777、GSE66666 均为公开 GEO series，但分别对应系统性硬化症、
  Parkinson 病、poly(I:C) MEF 和拟南芥研究，与构造论文主题不匹配。
- `DataIntegrityR` 的 CRAN metadata 与 R-universe package 查询均返回 HTTP 404。

# bench-100 重建核查

- 论文身份冻结为 DOI `10.1371/journal.pone.0099625`、PMID `24926665`、PMCID `PMC4057123`，许可为 CC BY 4.0。
- PMC supplementary archive 含 29 个发布资产；GEO 官方 Cuffdiff 输出恰有 316 个 q-value < 0.05 的基因。
- 计分 scope 从官方 GEO processed outputs 开始；16 个 ENA runs 共 `50,359,986,052` bytes，仅以 resolver 暴露，不默认 stage FASTQ。
- `airway` Bioconductor 包是后来的教学重分析，不属于论文原始方法契约；旧 DESeq2 baseline 不保留。
- `git bundle verify` 确认 Taffeta snapshot 是 commit `d12f00f74de35e437068349c617869a97856e160` 的完整历史，仓库内含 MIT license。
- GSE34313 与 GSE13168 是 Table 3 的 secondary microarray context，已登记为不参与计分；历史 RNA-seq 可执行包未伪装为冻结环境。

# AC 验收

| AC | 结果 | 证据与说明 |
|----|------|------------|
| AC-0006-N-1 | PASS | 五个 L3 的 constructed paper、数据与 resource inventory 均通过 validator 和人工逐项核对 |
| AC-0006-N-2 | PASS | bench-100 冻结 original PDF/XML、全部 PMC supplementary、官方 GEO outputs 与代码 snapshot；无派生论文替代原件 |
| AC-0006-N-3 | N/A | 当前没有 L5 entry |
| AC-0006-N-4 | PASS | staging 测试证明只复制 `input/`，不复制 bundle、metadata 或 oracle |
| AC-0006-B-1/B-2/B-4 | PASS | unavailable/restricted/constructed-failure resources 均有 source、时间和说明；rubric 不读取 bundle disposition 免责 |
| AC-0006-B-3 | N/A | bench-100 使用官方完整 processed outputs，不使用静默裁剪数据 |
| AC-0006-E-1 至 E-7 | PASS | hash、未声明文件、越界、派生链、oracle 字段、control-plane 泄漏和不可观察限制均有门禁或人工核对 |
| AC-0006-F-1 至 F-3 | PASS | 旧假 L4 已删除；论文引用均有 disposition；不存在静默代表完整数据的裁剪 CSV |
| AC-0007-N-1/N-2 | PASS | 五个 constructed L3 与一个真实材料 L4 的层级和编号契约一致 |
| AC-0007-N-3/B-1 | N/A | 当前没有 L5 entry，也没有依赖对象存储解析的 L4 原件 |
| AC-0007-E-1/F-1 | PASS | metadata/bundle 冲突会被拒绝；所有 entry 冻结前均不建立 tracked baseline |

# 残余风险与移交

- staging isolation 不能阻止拥有宿主机权限的被测系统读取仓库其他路径。OS/container 强隔离移交 Plan 005，不把本轮证明扩大为运行沙箱证明。
- bench-100 的历史可执行工具与容器尚未冻结；这属于 Plan 002 的 L4 环境工作。当前通过的是 processed-output InputBundle fidelity，不是完整发布级 baseline。
- hg19 iGenomes 与历史 DAVID release 缺少不可变版本标识；GWAS participant-level 数据不可公开获得。
- 五个构造 entry 的外部 locator 可能随网络环境漂移；发布运行必须记录实际解析状态。

# 结论

Plan 004 的材料真实性、bundle gate、六个 entry 迁移和人工 fidelity review 均完成。
六个 entry 可以进入后续执行环境与系统测试工作，但在 Plan 002/005 完成且协议进入 RC 前，
仍不得建立 release baseline 或宣称公开 benchmark 已发布完成。
