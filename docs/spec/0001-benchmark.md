---
title: Spec 001 — 基准测试体系
description: bio-reproducer 的五层测试与基准体系：L1-L2 内部测试、L3-L5 黑盒基准，输入输出协议，执行器设计。
type: spec
status: proposed
version: 1
created: 2026-07-15T00:00:00Z
---

# 概要设计

## 一、项目概述

本 Spec 覆盖 bio-reproducer 的**测试与基准体系**（L1-L5）。论文复现系统本身（`loops/bio-reproducer/`）是已有实现，不在本 Spec 范围内——其设计见 `loops/bio-reproducer/agents/` 和 `workflow.py`。

测试体系分为两个域：L1-L2 内部测试（耦合于复现系统实现），L3-L5 黑盒基准（引擎无关，可成为公开标准）。

### 两个域的关键区别

| | L1-L2 (内部测试) | L3-L5 (黑盒基准) |
|---|---|---|
| **耦合对象** | bio-reproducer 的实现细节 | 无（只依赖输入/输出协议） |
| **知道什么** | Phase 结构、output schema、agent 内部状态 | 只知道论文入、结果出 |
| **测试方式** | 构造输入 → 喂给单个/多个 Phase → 检查内部产出 | 给论文包 → 等系统跑完 → 对比结果 JSON |
| **可迁移性** | 换一个复现系统，完全无用 | 换一个复现系统，同样的基准可复用 |
| **目标** | 开发时的快速反馈 | 可发布、可对比的公开标准 |
| **版本** | 随 bio-reproducer 版本 | 独立的 benchmark 版本号 |

---

## 二、用户故事

| 编号 | 角色 | 需求 | 目的 | 优先级 |
|------|------|------|------|--------|
| US-001 | bio-reproducer 开发者 | 修改 prompt 后快速验证 Agent 行为是否退化 | 开发迭代时快速反馈 | P0 |
| US-002 | bio-reproducer 开发者 | 验证 Phase 之间的信息流是否自洽 | 防止 prompt 变更破坏 Phase 链 | P0 |
| US-003 | 系统评测者 | 用构造论文黑盒测试系统端到端能力 | 衡量系统整体复现能力 | P0 |
| US-004 | 系统评测者 | 用真实论文（冻结环境）测试工程能力 | 标准化可比较的复现率测评 | P1 |
| US-005 | 系统评测者 | 监控真实环境下的复现表现 | 发现外部依赖问题和长期趋势 | P2 |
| US-006 | 基准发布者 | 独立发布 L3-L5 基准，供其他复现系统使用 | 建立公开的论文复现 benchmark 标准 | P2 |

---

## 三、模块划分

| 模块 | 提供的能力 | 目录路径 | 优先级 |
|------|-----------|---------|---------|
| L1 单元测试 | 单 Phase Agent 业务逻辑正确性验证、行为稳定性测量 | `tests/unit/` | P0 |
| L2 集成测试 | 跨 Phase 信息流验证、非完美上游处理验证、变更影响检测 | `tests/integration/` | P0 |
| L3 能力基准 | 构造论文端到端黑盒测试、复现场景覆盖 | `benchmarks/entries/` | P0 |
| L4 工程基准 | 真实论文冻结环境测试、工程复杂度覆盖 | `benchmarks/entries/` | P1 |
| L5 生产基准 | 真实环境采样监控、长期趋势追踪 | (无固定目录，按需采样) | P2 |
| Benchmark Runner | 论文包执行、结果采集、期望对比、报告生成 | `benchmarks/runner/` | P0 |
| 引擎适配器 | 将引擎无关的论文包映射为 loopflow 调用 | `benchmarks/runner/adapters/` | P0 |

### L1 详细说明

测单个 Agent 在单个 Phase 内的业务逻辑正确性。通过真实 LLM 调用运行单个 Phase Agent，对比其产出与 golden fixture 的关键业务字段。

不测 schema 合规（字段类型、枚举值、JSON 格式）——那是 loopflow workflow 运行时的基础设施保证，不属于 benchmark 测试范围。

测试方式：给定论文 PDF + 构造的上游产出 → 运行 Phase Agent → 对比产出的结构化关键字段与 golden fixture。

关键字段包括：status、tool list、accession 列表、参数映射、关键决策点。不比较全文。

每 Phase 的关注重点：

| Phase | 核心关注 |
|-------|---------|
| Reader | 能否从论文中提取出复现所需的结构化信息 |
| Bootstrap | 能否正确检测系统环境并报告缺失组件 |
| Provision | 能否制定合理的工具部署计划并执行 |
| Data | 能否识别数据来源并尝试获取 |
| Run | 能否根据计划生成并执行分析流程 |
| Validate | 能否根据 plan 和 run 结果产出完整的验证报告 |
| Package | 能否生成可用的 README 和 run.sh |

### L2 详细说明

测 Phase 之间的信息流自洽性。不仅测 happy path，还测上游非完美产出时下游的正确处理。

上游非完美状态及下游处理规则：

| 上游状态 | 下游应如何处理 |
|---------|--------------|
| `status: partial` + 某些字段缺失 | 下游应读取 `missing` 列表，判断自身是否受影响，降级执行或跳过 |
| `status: blocked` | 下游应识别阻塞并停止，不应盲目继续 |
| 某字段标记为 "Not specified" / "TBD" | 下游不应将其当作有效值使用，应标记自身限制 |
| 输出格式正确但内容为空 | 下游应识别空数据，不应假设默认值 |
| `uncertainties` 列表非空 | 下游应知晓不确定性，在自身产出中标注受影响范围 |

关键集成链：

```
Reader → Bootstrap:  Bootstrap 能否从 plan.md 中提取系统需求？
Reader → Provision:  Provision 能否从 plan.md 中提取工具和环境需求？
Reader → Data:       Data 能否从 plan.md 中提取数据 accession？
Reader → Run:        Run 能否从 plan.md 中提取分析步骤和参数？
Reader → Validate:   Validate 能否从 plan.md 中提取 expected results 作为检查项？
Provision → Run:     Run 能否正确引用 provision.md 中已部署的工具？
Data → Run:          Run 能否正确使用 data_manifest.md 中的实际数据路径？
Run → Validate:      Validate 能否正确读取 run_results.md 中的实际结果？
```

### L3 详细说明

构造论文，黑盒端到端。论文是我们写的，数据极小（≤10MB），工具极简（1-2 个容器），ground truth 完全已知。测系统的阅读理解能力和端到端完成率。

复现场景分类：

| 复现场景 | 论文核心产出 | 复现目标 | 验证方式 |
|---------|-------------|---------|---------|
| 图表复现 | 关键 figure/panel | 用复现数据重新生成图表，视觉模式一致 | 图像比较、趋势一致性 |
| 数据复现 | 数值表、统计量、基因列表 | 复现数值在合理容差内 | 数值对比、集合重叠 |
| 结论复现 | 定性论断 | 复现结果支持相同的定性结论 | 方向一致性、统计推断一致 |
| 流程复现 | 分析 pipeline 本身 | 相同的工具链、参数、步骤能跑通 | 流程完整性 |
| 混合 | 上述多种组合 | 根据论文侧重，各维度权重不同 | 综合评分 |

论文中的常见困难模式：

| 模式 | 描述 |
|------|------|
| 参数分散 | 关键参数在补充材料中，不在正文 |
| 版本模糊 | 工具版本号不精确 |
| 数据在末尾 | accession 在 Data Availability 节，不在 Methods |
| 多版本 | 预印本和正式版存在差异 |
| 隐含步骤 | 分析流程中有些步骤未显式写出 |
| 多工具 | 论文使用了多个工具，需要全部部署 |
| 非标准工具 | 工具不在主流生态中 |

### L4 详细说明

真实论文，冻结外部依赖。用真实论文测评，但所有外部依赖（数据、镜像、补充材料）预下载到本地，使每次运行环境一致。类比 SWE-bench。

与 L3 的区别：

| | L3 能力基准 | L4 工程基准 |
|---|---|---|
| 论文 | 构造的 | 真实发表的 |
| 数据 | 极小，自制 | 真实数据，预下载到本地 |
| 环境 | 极简（1-2 个容器） | 真实（可能多个容器、多种工具） |
| 问题 | 系统"脑子"灵不灵 | 系统能不能扛住真实工程复杂度 |
| 运行次数 | N≥5 | N≥1（推荐 2-3 次） |
| expected_verdict | 通常 REPRODUCED | 可以是 REPRODUCED 或 PARTIAL |

L4 的 `expected_verdict: PARTIAL` 的合理原因：
- 论文部分数据需要申请访问（系统正确识别并标记，不应判定为 FAILED）
- 论文部分结果依赖付费工具（系统用替代方案生成了可比结果）
- 论文的某些图表缺乏原始数据无法验证（系统正确标注了限制）

环境冻结：数据预下载到本地对象存储，容器镜像预拉取到本地 registry，外部 URL 映射到本地。

### L5 详细说明

真实论文，真实环境，真实网络。随机采样新论文尝试复现，监控真实世界复现率和外部依赖脆弱性。不做 CI gate，做长期观测。

### 文件系统结构

```
bio-reproducer/
├── loops/bio-reproducer/         # 被测系统
├── tests/                        # L1-L2: 内部测试
│   ├── unit/                     # L1: 单 Phase Agent
│   ├── integration/              # L2: 跨 Phase 信息流
│   ├── conftest.py
│   └── fixtures/                 # → symlink to ../../benchmarks/entries/*/golden/
├── benchmarks/                   # L3-L5: 黑盒基准 (引擎无关)
│   ├── VERSION
│   ├── CHANGELOG.md
│   ├── entries/                  # 论文定义
│   ├── runner/                   # benchmark 执行器
│   │   ├── cli.py
│   │   ├── runner.py
│   │   ├── evaluator.py
│   │   ├── reporter.py
│   │   └── adapters/             # 引擎适配 (唯一耦合点)
│   └── results/                  # 运行结果 (gitignored)
└── docs/                         # devloop 文档
```

---

# 详细设计

## 四、数据模型

### BenchmarkEntry

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | str | PK | 论文包唯一标识 |
| version | str | NOT NULL | 论文包版本号 |
| scenario | str | NOT NULL | 复现场景：figure/data/conclusion/pipeline/mixed |
| difficulty | str | NOT NULL | 难度：easy/medium/hard |
| expected_verdict | str | NOT NULL | 期望的最终判定 |
| paper_pdf | path | NOT NULL | 论文 PDF 路径 |
| data_dir | path | NOT NULL | 数据集目录 |
| expected_yaml | path | NOT NULL | 测评期望文件路径 |

### BenchmarkResult

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| run_id | str | PK | 运行实例 ID |
| bench_id | str | FK | 关联的 BenchmarkEntry |
| bench_version | str | NOT NULL | 使用的基准版本 |
| verdict | str | NOT NULL | REPRODUCED/PARTIAL/FAILED/BLOCKED |
| score | int | 0-100 | 复现分数 |
| stages | list[StageResult] | | 各阶段状态 |
| duration_seconds | int | | 总耗时 |
| llm_calls | int | | LLM 调用次数 |
| human_interventions | int | | 人工介入次数 |

### StageResult

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| name | str | NOT NULL | 阶段名称（被测系统定义） |
| status | str | NOT NULL | completed/partial/blocked/failed |

---

## 五、业务规则

| 规则编号 | 描述 | 触发条件 | 约束 |
|----------|------|----------|------|
| BR-001 | L3 每篇论文跑 N≥5 次，L4 跑 N≥1 次 | 执行 benchmark 时 | L3 必须报告 verdict 分布，L4 可单次 |
| BR-002 | 评估基于分布，不要求每次匹配：verdict 匹配率 ≥ 阈值（默认 60%） | 评估对比时 | 5 次中 ≥3 次匹配 expected 即通过 |
| BR-003 | BLOCKED 需区分原因：系统阻塞（能力不足）vs 外部阻塞（依赖不可用） | 评估对比时 | blocked_reason 必须标注来源：system / external |
| BR-004 | 系统阻塞 + expected 为 REPRODUCED → 判定失败；外部阻塞 → 不计入失败 | 评估对比时 | 两种阻塞分开统计 |
| BR-005 | L3-L5 基准独立于引擎 | 定义基准时 | 输入/输出/评估协议不含引擎特定字段 |

### blocked_reason 分类

| 来源 | 示例 | 对测评的影响 |
|------|------|------------|
| `system` | Agent 无法解析 PDF、Prompt 歧义导致错误决策、OOM 崩溃 | 计入系统失败 |
| `external` | GEO 数据不可下载、镜像仓库宕机、论文网页改版 | 不计入系统失败，单独记录 |
| `paper` | 论文数据需申请访问、代码未公开、关键信息缺失 | 标记为论文本身不可复现 |

---

# 约束

## 七、非功能指标

| 维度 | 指标 | 目标值 |
|------|------|--------|
| 性能 | L3 单篇论文执行时间 | < 10 min |
| 性能 | L1 单 Phase 测试时间 | < 30 s |
| 可重复性 | L3 同篇论文 verdict 匹配率 | ≥ 60% (5 次中 ≥3 次) |
| 兼容性 | L3-L5 基准可被其他引擎使用 | 是 |

---

## 八、依赖项

| 依赖 | 版本 | 用途 |
|------|------|------|
| loopflow | ≥0.13.0 | Agent 执行引擎 |
| pytest | ≥8.0 | L1/L2 测试框架 |
| Python | ≥3.10 | 运行环境 |

---

## 九、术语表

| 术语 | 定义 |
|------|------|
| Golden fixture | 人工标注的完美 Phase 产出，用于 L1/L2 对比 |
| 论文包 | L3-L5 基准的输入单元：paper.pdf + data/ + expected.yaml |
| 评估协议 | 对比 expected.yaml 和 result.json 的规则 |
| 引擎适配器 | 将引擎无关的论文包映射为特定引擎调用的桥接模块 |