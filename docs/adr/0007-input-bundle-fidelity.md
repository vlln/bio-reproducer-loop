---
title: ADR-0007 — 分层 InputBundle 与材料真实性
description: 统一 InputBundle 的结构和 provenance 契约，同时按 L3/L4/L5 区分构造输入、冻结真实材料与在线资源发现。
type: adr
status: proposed
created: 2026-07-20T00:00:00Z
---

# ADR-0007: 分层 InputBundle 与材料真实性

## 背景

协议 v2 统一了 `input/`、`oracle/` 和 `metadata.yaml` 的信任边界，但现有六个
entry 的公开输入几乎都被压缩为 `paper.md + counts.csv`。这种形状适合构造型 L3，
却不能代表真实论文 L4 的原始 PDF、补充材料、代码、数据版本和获取记录。

bench-003 声明为 `real_published` 和 `paper_format: pdf`，实际只提供 82 行人工摘要；
输入还将真实论文任务改写成 DESeq2 教学任务，并用 357 基因子集替代论文描述的完整
转录组。其余构造 entry 的论文引用补充表、脚本和仓库，但对应材料未打包，也没有
明确的 unavailable record。目录结构统一被错误地等同于科学内容统一。

本 ADR 补充 ADR-0005 的 InputBundle 决策，不改变 Input/Submission/Oracle 三方隔离。

## 决策内容

### 1. 统一结构，不统一科学载荷

每个 entry 保持 `input/`、`oracle/`、`metadata.yaml` 的顶层结构。`input/` 必须包含
公开的 `manifest.yaml`，其余目录按材料实际情况出现：

```text
input/
├── manifest.yaml
├── paper/
├── supplementary/
├── code/
├── data/
└── resources/
```

`manifest.yaml` 是资源与 provenance 清单，不是科学答案。它声明每项材料的 role、
来源、版本、路径或可用性、checksum、license、原始/派生关系和转换过程。故障注入
意图、expected result 和评分规则仍属于 private oracle 或非 staged metadata。

InputBundle 中除 `manifest.yaml` 外的每个文件都必须被 manifest 声明。论文明确引用
但未打包的 supplementary、代码或数据也必须有资源记录，状态不得用目录缺失隐式表达。

### 2. 按 L3/L4/L5 定义完整性

| Level | 输入起点 | 材料规则 | 主要测量目标 |
|-------|----------|----------|----------------|
| L3 | 构造论文 | 允许 Markdown 和小型构造数据；虚构、缺失或不可用资源必须显式记录 | 可控能力与故障处理 |
| L4 | 真实发表材料的冻结快照 | 原始论文必需；所有可合法获取的 cited supplementary、代码和数据必须冻结或提供受审查 descriptor | 真实工程复现能力 |
| L5 | 原始论文或稳定标识符 | 保留最小可信起点，允许系统通过真实网络发现资源；运行时记录实际解析结果 | 真实生态与外部脆弱性 |

L4 中 PDF/XML/HTML 等原始发布物是权威来源。由解析器生成的 Markdown、抽取图像、
格式转换数据或裁剪数据只能作为 `derived` 资源，并必须声明 `derived_from`、转换工具、
参数和转换脚本。派生表示不得替代原始论文，裁剪数据不得静默代表完整论文数据。

### 3. 区分缺失、受限与未收集

资源状态至少包括：

- `bundled`：文件随 InputBundle 提供；
- `external`：L5 运行时通过稳定标识符获取；
- `restricted`：存在但受许可或访问控制限制；
- `unavailable`：按记录的地址和时间核查后不可获取；
- `not_applicable`：论文未声明该类资源。

`unavailable` 需要核查位置和时间；`restricted` 需要访问要求；二者均不能由 curator
遗漏文件来代替。benchmark 故意注入的不可用性不得在公开 manifest 中泄露“这是故障
注入”，但必须向被测系统呈现与真实不可用资源等价的可观察状态。

### 4. Release gate

Entry 只有通过 InputBundle 人工审查、manifest 校验和层级特定 AC 后，才能进入 RC。
在此之前运行结果只是开发期 observation，不建立 tracked baseline。

## 选择理由

- 保留统一信任边界，避免每个复现系统理解不同 entry 布局。
- 防止 L4 被简化成由 benchmark 作者预先解题的标准分析练习。
- provenance 使数据裁剪、格式转换和资源缺失可审计。
- 分层契约避免用 L4 的重资产要求惩罚构造型 L3，也避免 L3 的简化规则污染 L4。

## 后果

### 正面

- 可以区分“论文没有代码”“代码不可获取”和“benchmark 漏收代码”。
- 真实论文、派生表示和裁剪数据不再混为同一来源。
- Runner 可以在启动昂贵执行前确定性拒绝错误标级或不完整 entry。

### 负面

- Entry 构建成本增加，需要资源审计、hash、license 和转换记录。
- 某些真实材料不能直接进入 Git，需要对象存储或可验证 descriptor。
- 现有六个 entry 都需要审计，bench-003 需要重建后才能继续作为 L4。

## 约束规则

| 规则编号 | 规则 | 检出方式 |
|----------|------|----------|
| AR-001 | 每个 InputBundle 必须有 `manifest.yaml` | schema/contract test |
| AR-002 | 每个 staged 文件必须在 manifest 中声明 | 目录与 manifest 集合比较 |
| AR-003 | L4 必须包含原始论文，派生 Markdown 不能单独满足要求 | level validator |
| AR-004 | L4 的 cited resources 必须 bundled 或有受审查状态记录 | 人工审计 + manifest validator |
| AR-005 | 派生与裁剪资源必须声明来源和可重复转换 | provenance validator |
| AR-006 | manifest 不得包含 oracle、expected result 或评分字段 | schema + forbidden-key test |
| AR-007 | 未通过 fidelity gate 的 entry 不得建立 release baseline | release checklist |

## 验证

| 验证项 | 复现步骤 | 预期结论 |
|--------|----------|----------|
| 假 L4 | 声明 `real_published`，仅提供人工摘要 Markdown | `INVALID_INPUT` |
| 未声明文件 | 在 `input/data/` 放置未登记 dotfile | `INVALID_INPUT` |
| 派生数据 | 提供裁剪 CSV 但不声明原数据和转换过程 | L4 fidelity gate 失败 |
| 合法受限资源 | manifest 声明 restricted accession 和访问条件 | InputBundle 有效，执行可按 paper limitation 降级 |
| Oracle 泄露 | manifest 出现 expected score 或 rubric 字段 | `INVALID_INPUT` |
