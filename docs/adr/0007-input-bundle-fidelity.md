---
title: ADR-0007 — 分层 InputBundle 与材料真实性
description: 统一 InputBundle 的结构和 provenance 契约，同时按 L3/L4/L5 区分构造输入、冻结真实材料与在线资源发现。
type: adr
status: accepted
created: 2026-07-20T00:00:00Z
---

# ADR-0007: 分层 InputBundle 与材料真实性

## 背景

协议 v2 统一了 `input/`、`oracle/` 和 `metadata.yaml` 的信任边界，但现有六个
entry 的公开输入几乎都被压缩为 `paper.md + counts.csv`。这种形状适合构造型 L3，
却不能代表真实论文 L4 的原始 PDF、补充材料、代码、数据版本和获取记录。

bench-100（审计时编号 bench-003）声明为 `real_published` 和 `paper_format: pdf`，实际只提供 82 行人工摘要；
输入还将真实论文任务改写成 DESeq2 教学任务，并用 357 基因子集替代论文描述的完整
转录组。其余构造 entry 的论文引用补充表、脚本和仓库，但对应材料未打包，也没有
明确的 unavailable record。目录结构统一被错误地等同于科学内容统一。

本 ADR 补充 ADR-0005 的 InputBundle 决策，不改变 Input/Submission/Oracle 三方隔离。

## 决策内容

### 1. 统一控制平面，不统一科学载荷

每个 entry 增加可信控制平面的 `bundle.yaml`。Runner 校验它，但绝不将其 stage 给被测
系统。`input/` 只包含该场景中系统实际获得的材料：

```text
entry/
├── bundle.yaml            # Runner/benchmark maintainer 可见，不 stage
├── input/                  # 被测系统唯一可见
│   ├── paper/
│   ├── supplementary/
│   ├── code/
│   ├── data/
│   └── resources/
├── oracle/                 # evaluator 私有
└── metadata.yaml           # Runner 元数据，不 stage
```

`bundle.yaml` 是资源与 provenance 锁文件，不是被测系统输入。它声明每项材料的 role、
来源、版本、相对 `input/` 的 path 或可用性、checksum、license、原始/派生关系和转换过程。
故障注入意图、expected result 和评分规则仍属于 private oracle。

InputBundle 中的每个文件都必须被 `bundle.yaml` 声明。论文明确引用但未打包的
supplementary、代码或数据也必须有控制平面记录，状态不得用目录缺失隐式表达。公开仓库
中的 `bundle.yaml` 仍受运行时隔离；正式隐藏测试集可以同时隐藏其仓库内容。

真实论文随附的 README、数据说明或 provenance 文件可以作为普通材料进入 `input/`，
但 benchmark 自动生成的 bundle lock 不得借此暴露给被测系统。

### 2. 按 L3/L4/L5 定义完整性

| Level | 输入起点 | 材料规则 | 主要测量目标 |
|-------|----------|----------|----------------|
| L3 | 构造论文 | 允许 Markdown 和小型构造数据；控制平面记录虚构、缺失或不可用资源，但系统只观察场景材料和环境行为 | 可控能力与故障处理 |
| L4 | 真实发表材料的冻结快照 | 原始论文必需；所有可合法获取的 cited supplementary、代码和数据必须冻结或在控制平面提供受审查 descriptor | 真实工程复现能力 |
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

`unavailable` 需要核查位置和时间；`restricted` 需要访问要求；二者均不能由 benchmark
maintainer 遗漏文件来代替。benchmark 故意注入的不可用性由 `bundle.yaml` 锁定可观察
条件、由 private oracle 记录注入意图；被测系统只能通过论文、材料和运行环境观察状态。
Evaluator 只有在限制确实可由这些运行时输入或环境观察到时，才能据此允许降级；控制面
记录本身不能成为宽免依据。

### 4. Release gate

Entry 只有通过 InputBundle 人工审查、bundle 校验和层级特定 AC 后，才能进入 RC。
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
- 现有六个 entry 都需要审计，bench-100（原 bench-003）需要重建后才能继续作为 L4。

## 约束规则

| 规则编号 | 规则 | 检出方式 |
|----------|------|----------|
| AR-001 | 每个 entry 必须有 runner-only `bundle.yaml` | schema/contract test |
| AR-002 | 每个 staged 文件必须在 bundle lock 中声明 | 目录与 bundle resource 集合比较 |
| AR-003 | Runner 只能 stage `input/`，不得 stage bundle/metadata/oracle | 隔离工作目录测试 |
| AR-004 | L4 必须包含原始论文，派生 Markdown 不能单独满足要求 | level validator |
| AR-005 | L4 的 cited resources 必须 bundled 或有受审查状态记录 | 人工审计 + bundle validator |
| AR-006 | 派生与裁剪资源必须声明来源和可重复转换 | provenance validator |
| AR-007 | bundle lock 不得包含 oracle、expected result 或评分字段 | schema + forbidden-key test |
| AR-008 | 未通过 fidelity gate 的 entry 不得建立 release baseline | release checklist |

## 验证

| 验证项 | 复现步骤 | 预期结论 |
|--------|----------|----------|
| 假 L4 | 声明 `real_published`，仅提供人工摘要 Markdown | `INVALID_INPUT` |
| 未声明文件 | 在 `input/data/` 放置未登记 dotfile | `INVALID_INPUT` |
| 派生数据 | 提供裁剪 CSV 但不声明原数据和转换过程 | L4 fidelity gate 失败 |
| 控制面隔离 | bundle 声明完整资源清单后运行被测系统 | 工作目录中只有 input 内容 |
| 合法受限资源 | bundle 声明 restricted accession 和访问条件 | Entry 有效，执行可按 paper limitation 降级 |
| Oracle 污染 | bundle 出现 expected score 或 rubric 字段 | `INVALID_BUNDLE` |
