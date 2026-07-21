---
title: Spec 001 — 测试、评测与基准体系
description: bio-reproducer 的确定性软件测试、内部 LLM 行为评测、分层 InputBundle 和公开黑盒 benchmark，以及独立评估协议。
type: spec
status: proposed
version: 3
created: 2026-07-15T00:00:00Z
---

# 概要设计

## 一、项目概述

本 Spec 覆盖 bio-reproducer 的**软件测试、内部行为评测与公开 benchmark**。论文复现系统本身（`loops/bio-reproducer/`）是已有实现，不在本 Spec 范围内——其设计见 `loops/bio-reproducer/agents/` 和 `workflow.py`。

体系分为三个域：确定性软件测试、耦合于复现系统的内部 LLM 行为评测、引擎无关的公开黑盒 benchmark。L3/L4/L5 仅作为公开 benchmark 内部的环境真实性等级，不再用于命名内部测试。

### 三个域的关键区别

| | 软件测试 | 内部行为评测 | 公开 benchmark |
|---|---|---|---|
| **目录** | `tests/` | `evals/` | `benchmarks/` |
| **执行依赖** | fake/fixture，无真实 LLM 与网络 | 真实 LLM，可使用真实工具 | 完整被测系统与指定环境 |
| **范围** | 代码、契约、状态传播 | 单 Phase、Phase handoff | 论文输入到复现产物 |
| **结果表达** | 确定性 pass/fail | 多次运行的质量分布 | 独立 evaluator 的 score/verdict |
| **版本** | 随 bio-reproducer | 随 bio-reproducer + 模型配置 | 独立 benchmark 版本 |

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
| 确定性单元测试 | Runner、evaluator、adapter、解析和状态机逻辑 | `tests/unit/` | P0 |
| 契约测试 | Phase 协议、状态传播、错误处理 | `tests/contract/` | P0 |
| Component eval | 单 Phase Agent 业务质量和稳定性 | `evals/component/` | P0 |
| Handoff eval | 跨 Phase 语义传递和降级决策 | `evals/handoff/` | P0 |
| L3 能力基准 | 构造论文端到端黑盒测试、复现场景覆盖 | `benchmarks/entries/` | P0 |
| L4 工程基准 | 真实论文冻结环境测试、工程复杂度覆盖 | `benchmarks/entries/` | P1 |
| L5 生产基准 | 真实环境采样监控、长期趋势追踪 | (无固定目录，按需采样) | P2 |
| Benchmark Runner | 论文包执行、结果采集、期望对比、报告生成 | `benchmarks/runner/` | P0 |
| 引擎适配器 | 将引擎无关的论文包映射为 loopflow 调用 | `benchmarks/runner/adapters/` | P0 |

### 确定性软件测试

软件测试验证实现逻辑和接口契约。所有用例必须在无 LLM、断网且不安装工具的环境中运行，使用 fake executor、录制响应或人工 fixture。

`tests/unit/` 覆盖 evaluator 比较器、artifact manifest、runner 补跑逻辑、adapter 错误映射和报告统计。`tests/contract/` 覆盖 Phase 输入输出 schema、blocked/partial 传播、缺失文件和非法状态。真实 LLM 行为不在此域内。

### 内部行为评测

Component eval 给单 Phase 提供论文和构造的上游 fixture，通过真实 LLM 运行。Handoff eval 运行多个 Phase，测量语义信息保留与非完美上游处理。结果按模型、Prompt、工具和环境版本记录，并通过 profile 控制的重复运行报告均值、方差、成功率和失败类别。

内部 eval 以能力分支或失败模式为 case，不按 benchmark entry 与 Phase 做笛卡尔积。Case 可以引用一个代表性 InputBundle，但 benchmark 新增不自动产生 eval；只有新增能力维度或真实回归才新增 case。内部 eval 不与完整 benchmark entry 的参考产物建立 symlink，也不使用 exemplar 做完整输出匹配。

每 Phase 的关注重点：

| Phase | 主要度量 |
|-------|----------|
| Reader | claims 精确率/召回率、参数归属、幻觉数 |
| Bootstrap | 与独立环境探针的一致性 |
| Provision | 需求覆盖、版本约束、替代方案有效性 |
| Data | 数据身份、checksum、维度、错误来源处理 |
| Run | 实际结果表、统计方向、容差、图表产物 |
| Validate | 与独立 evaluator 的一致性和校准误差 |
| Package | 干净环境中的 run.sh smoke test |

### Handoff 详细说明

测 Phase 之间的信息流自洽性。不仅测 happy path，还测上游非完美产出时下游的正确处理。确定性的状态传播进入 `tests/contract/`；需要真实 LLM 判断的语义处理进入 `evals/handoff/`。

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

构造论文，黑盒端到端。论文是我们写的，数据极小（≤10MB），工具极简（1-2 个容器），ground truth 完全已知。测系统的阅读理解能力和端到端完成率。L3 可以使用 Markdown/PDF 和构造数据，但必须通过 runner-only bundle lock 审计所有 staged 文件、虚构引用和不可用资源；不能用 benchmark maintainer 遗漏模拟资源缺失，也不能把审计清单提供给被测系统。

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

真实论文，冻结外部依赖。用真实论文测评，原始发布物是权威输入；所有可合法获取的 cited 数据、代码、补充材料和资源页都冻结到 bundle 或对象存储，使每次运行环境一致。无法再分发、受限或已失效的资源必须有经过人工审查的 descriptor。类比 SWE-bench。

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

环境冻结：数据预下载到本地对象存储，容器镜像预拉取到本地 registry，外部 URL 映射到本地。解析生成的 Markdown、抽取图像、格式转换或裁剪数据只能作为派生材料；必须记录原始资源、checksum、转换工具、参数和脚本，不能静默替代原始论文或完整数据。

### L5 详细说明

真实论文，真实环境，真实网络。InputBundle 提供原始论文或稳定标识符作为最小可信起点，系统自行发现在线资源并记录实际解析结果。随机采样新论文尝试复现，监控真实世界复现率和外部依赖脆弱性。不做 CI gate，做长期观测。

### 文件系统结构

```
bio-reproducer/
├── loops/bio-reproducer/         # 被测系统
├── tests/                        # 快速、确定性软件测试
│   ├── unit/
│   ├── contract/
│   └── fixtures/
├── evals/                        # 真实 LLM 内部行为评测
│   ├── component/
│   ├── handoff/
│   ├── cases/                    # capability/failure-mode case 定义
│   ├── fixtures/                 # 构造或人工确认的上游 Phase 状态
│   ├── runner/                   # profile、执行与结果记录
│   └── results/                  # 真实 LLM 原始观测 (gitignored)
├── benchmarks/                   # L3-L5: 黑盒基准 (引擎无关)
│   ├── VERSION
│   ├── CHANGELOG.md
│   ├── entries/                  # runner-only bundle.yaml + input/ + private oracle/ + metadata.yaml
│   ├── baselines/                # 仅在 benchmark 冻结后记录发布级历史观测
│   ├── runner/                   # benchmark 执行器
│   │   ├── cli.py
│   │   ├── runner.py
│   │   ├── independent_evaluator.py
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
| input_dir | path | NOT NULL | 运行时暴露给被测系统的输入目录 |
| oracle_dir | path | NOT NULL | 仅 evaluator 可见的真值与规则目录 |
| oracle_version | str | NOT NULL | Oracle 版本 |
| complexity_profile | dict | 推荐 | 复杂度维度取值，用于可发现性和能力匹配 |

### EntryBundle

每个 entry 根目录必须包含 `bundle.yaml`。Bundle lock 是 Runner 和 benchmark maintainer
使用的可信控制平面，不属于运行时 InputBundle，不得被 stage 给被测系统。它不包含
oracle、expected result、故障注入意图或评分规则。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| schema_version | str | NOT NULL | Entry bundle schema 版本 |
| entry_id | str | FK | 与 BenchmarkEntry 一致 |
| level | enum | L3/L4/L5 | 决定完整性校验规则 |
| input_root | path | 必须为 input | Runner 唯一允许 stage 的目录 |
| primary_paper | str | FK | 指向 resources 中的主论文资源 |
| resources | list[InputResource] | NOT NULL | staged 与 cited 资源全集 |

### InputResource

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | str | PK | bundle 内稳定 ID |
| role | enum | NOT NULL | paper/supplementary/code/data/metadata/environment/resource_page |
| authority | enum | original/derived | 原始发布物或派生表示 |
| availability | enum | NOT NULL | bundled/external/restricted/unavailable/not_applicable |
| path | path | bundled 时必需 | 相对 input 根目录，禁止越界 |
| source | str | original 时必需 | DOI、accession、仓库/发布页；constructed L3 使用 benchmark URN |
| sha256 | str | bundled 文件时必需 | 内容完整性 |
| derived_from | list[str] | derived 时必需 | 上游资源 ID |
| transform | object | derived 时必需 | 可重复转换工具、版本和命令/脚本 |
| access_notes | str | restricted/unavailable 时必需 | 访问条件或核查事实 |

每个 staged 文件必须且只能由一个 resource path 声明。论文明确引用但未打包的资源也必须
在 bundle lock 中有 record。L4 的 primary paper 必须是 original；只有派生 Markdown 的
entry 不得标记为 L4。Runner 只能 stage `input_root`，不得暴露 bundle、metadata 或 oracle。
完整字段契约见 Interface 0001，架构依据见 ADR-0007。

### 复杂度维度分类法

每个 benchmark entry 在 `metadata.yaml` 中声明 `complexity_profile`，标记该 entry 在各维度上的复杂度水平。所有 entry 共享同一套分类法，外部系统可按维度查询和筛选。

#### 数据层

| 维度 | 取值 | 说明 |
|------|------|------|
| data_size | tiny / small / medium / large / huge | tiny: <10KB, small: <10MB, medium: <100MB, large: <10GB, huge: >10GB |
| data_source | local / public_db / restricted / synthetic | 数据来源：本地文件 / 公共数据库(GEO/SRA) / 需申请权限 / 系统生成 |
| data_format | csv / tsv / rds / fastq / bam / mixed | 主要数据格式 |
| supplementary | none / simple / complex | 补充材料复杂度：无 / 单表或简单文本 / 多附件嵌套格式 |

#### 环境层

| 维度 | 取值 | 说明 |
|------|------|------|
| tool_count | 1-2 / 3-5 / 6+ | 论文所需的工具/包数量 |
| tool_chain | single_language / multi_language / multi_container | 工具链复杂度 |
| version_sensitivity | loose / moderate / strict / critical | 版本差异对结果的影响程度 |
| container | existing_image / custom_dockerfile / manual_build | 容器化难度 |

#### 分析层

| 维度 | 取值 | 说明 |
|------|------|------|
| design | two_group / paired / multi_factor / time_series / meta_analysis | 实验设计类型 |
| method_complexity | standard / multi_step / parameter_tuning | 分析方法复杂度 |
| compute | light / moderate / heavy | 计算资源需求：light(<5min) / moderate(5-30min) / heavy(>1h) |

#### 图表层

| 维度 | 取值 | 说明 |
|------|------|------|
| figure_count | 1 / 2-5 / 6+ | 需复现的图表数量 |
| figure_type | statistical / heatmap / trajectory / multi_panel / mixed | 图表类型 |
| figure_layout | simple / moderate / complex | 单面板 / 多面板 / 多图嵌套 |
| figure_rendering | standard / custom_palette / complex_annotation | 渲染复杂度 |

#### 评估层

| 维度 | 取值 | 说明 |
|------|------|------|
| ground_truth | fully_known / partially_known / unknown | 正确答案的完整性 |
| claim_type | exact_numeric / directional / qualitative / mixed | 论文声称的类型 |
| tolerance | strict / moderate / loose | 数值比对容忍度 |

#### 论文层

| 维度 | 取值 | 说明 |
|------|------|------|
| paper_type | constructed / real_preprint / real_published | 构造论文 / 真实预印本 / 真实发表 |
| paper_format | pdf / markdown / html | 论文格式 |
| multi_version | none / preprint_published / versioned_dataset | 是否存在多版本问题 |
| missing_info | none / implicit_steps / scattered_params / version_gaps | 论文信息的完整程度 |

### 鲁棒性维度分类法

复杂度维度测量"有多难"，鲁棒性维度测量"会不会坏"——benchmark 设计者故意注入故障，测试系统能否正确检测、降级、或绕过。取值均为二元（true/false），true 表示该 entry 注入了此类故障。

#### 外部资源不可用

| 维度 | 说明 | 示例 |
|------|------|------|
| database_down | GEO/SRA/ENA 等公共数据库不可访问 | 网络断开、数据库维护 |
| registry_down | 容器镜像仓库不可用 | Docker Hub/Quay 宕机 |
| tool_not_found | 论文声明的工具不存在或已改名 | 包名变更、仓库归档 |
| repo_gone | 论文声明的代码仓库 404 | 作者删库、链接失效 |
| doi_dead | 论文 DOI 不可解析 | 虚构 DOI、链接失效 |
| image_missing | 论文原始图片缺失，无法做像素级视觉对比 | 预印本无图、PDF 提取失败 |

#### 数据降级

| 维度 | 说明 | 示例 |
|------|------|------|
| empty_data_dir | data/ 目录为空，无可用的本地数据 | 数据未预下载 |
| truncated_file | 数据文件截断或损坏 | 下载中断、文件不完整 |
| format_mismatch | 文件格式与论文声明不符 | 声称 CSV 实为 TSV、声称 RDS 实为 RData |
| wrong_accession | GEO/SRA accession 指向不相关数据 | 论文笔误、accession 重用 |

#### 信息降级

| 维度 | 说明 | 示例 |
|------|------|------|
| missing_supplementary | 补充材料不可获取 | 链接失效、需付费 |
| version_gaps | 工具版本号不精确，只能推断 | "使用最新版"、"DESeq2" |
| implicit_steps | 关键分析步骤未显式写出 | 未提及标准化方法、未说明过滤条件 |
| scattered_params | 参数分散在正文、补充材料、代码注释中 | 阈值在 Methods，模型参数在 Suppl Table 2 |
| conflicting_info | 正文与补充材料/代码中的信息矛盾 | 正文说 n=6，补充材料表显示 n=5 |

#### 环境漂移

| 维度 | 说明 | 示例 |
|------|------|------|
| version_mismatch | 软件版本与论文声明不同 | 论文要求 R 4.3.0，环境为 R 4.6.1 |
| os_mismatch | 操作系统不同 | 论文基于 CentOS，环境为 macOS |
| arch_mismatch | CPU 架构不同 | 论文基于 x86_64，环境为 ARM64 |
| missing_system_dep | 系统级依赖缺失，需手动安装 | libxml2、libcurl 未安装 |

#### 与复杂度维度的关系

| | 复杂度维度 | 鲁棒性维度 |
|---|---|---|
| 问题 | "有多难？" | "会不会坏？" |
| 取值 | 渐进 (tiny/medium/large) | 二元 (true/false) |
| 来源 | 论文本身决定的 | benchmark 设计者故意注入的 |
| 用途 | 筛选匹配能力的 entry | 筛选测试特定故障注入的 entry |
| 查询示例 | "tool_count ≤ 3 的 entry" | "repo_gone=true 的 entry" |

### BenchmarkSubmission

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| submission_id | str | PK | 一次系统提交的唯一标识 |
| bench_id | str | FK | 关联的 BenchmarkEntry |
| system | object | NOT NULL | 被测系统名称与版本 |
| claimed_verdict | str | 可选 | 系统自评，只用于校准指标 |
| artifacts | list[Artifact] | NOT NULL | 带语义 role 的实际产物清单 |
| execution | object | NOT NULL | 时长、阶段和资源等运行观测 |

### EvaluationResult

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| run_id | str | PK | 运行实例 ID |
| bench_id | str | FK | 关联的 BenchmarkEntry |
| benchmark_version | str | NOT NULL | 使用的基准版本 |
| submission_id | str | FK | 被评估的提交 |
| verdict | str | NOT NULL | evaluator 生成的 REPRODUCED/PARTIAL/FAILED/BLOCKED |
| score | float | 0-100 | evaluator 生成的复现分数 |
| checks | list[CheckResult] | NOT NULL | 每个 rubric 检查项的证据与结果 |
| calibration | object | 可选 | 系统自评和独立 verdict 的差异 |
| provenance | object | NOT NULL | evaluator 与 oracle 版本 |

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
| BR-002 | 评估基于独立 evaluator 结果的分布，不信任系统自评 | 评估对比时 | 5 次中达到 rubric 规定 verdict 的比例 ≥ 阈值 |
| BR-003 | BLOCKED 需区分原因：系统阻塞（能力不足）vs 外部阻塞（依赖不可用） | 评估对比时 | blocked_reason 必须标注来源：system / external |
| BR-004 | 系统阻塞 + expected 为 REPRODUCED → 判定失败；外部阻塞 → 不计入失败 | 评估对比时 | 两种阻塞分开统计 |
| BR-005 | L3-L5 基准独立于引擎 | 定义基准时 | 输入/输出/评估协议不含引擎特定字段 |
| BR-006 | InputBundle 与 OracleBundle 运行时隔离 | 执行 benchmark 时 | 被测系统仅能读取 staged input |
| BR-007 | baseline 是冻结 benchmark 上带系统配置的发布级观测，不属于 entry 真值 | entry、oracle 与协议进入 RC/发布后 | 开发期结果只进入 ignored results/report；baseline 独立存储，不写入 metadata/oracle |
| BR-008 | 每个 staged input 文件必须在 bundle lock 中声明 | entry 校验时 | 未声明文件、重复 path、越界 path 均为 INVALID_BUNDLE |
| BR-009 | L4 必须保留真实原始论文 | L4 entry 校验时 | 只有摘要或派生 Markdown 时拒绝进入 L4 |
| BR-010 | cited supplementary/code/data 不得因 benchmark maintainer 省略而隐式缺失 | entry 审查时 | bundled 或在 bundle lock 提供 restricted/unavailable record |
| BR-011 | 派生与裁剪材料必须可追溯、可重复生成 | authority=derived 时 | derived_from 与 transform 必填 |
| BR-012 | bundle lock 不得污染 InputBundle 或包含 oracle | entry 校验与 staging 时 | bundle 不可见；expected/rubric/score/verdict/故障注入字段禁止出现 |

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
| 性能 | 确定性 `pytest tests/` | < 30 s |
| 隔离性 | 被测系统读取 oracle 的能力 | 不可读取 |
| 可重复性 | L3 同篇论文 verdict 匹配率 | ≥ 60% (5 次中 ≥3 次) |
| 兼容性 | L3-L5 基准可被其他引擎使用 | 是 |

---

## 八、依赖项

| 依赖 | 版本 | 用途 |
|------|------|------|
| loopflow | ≥0.13.0 | Agent 执行引擎 |
| pytest | ≥8.0 | 确定性单元与契约测试框架 |
| Python | ≥3.10 | 运行环境 |

---

## 九、术语表

| 术语 | 定义 |
|------|------|
| Oracle | 独立科学真值、评分规则、容差和验证程序 |
| Fixture | 为确定性测试或内部 eval 构造的输入，不代表唯一正确输出 |
| Exemplar | 经人工确认的一个合法输出示例，不用于全文匹配 |
| Baseline | 在冻结 benchmark 版本上，由特定系统、模型、Prompt、工具和环境产生的发布级历史观测 |
| InputBundle | 被测系统运行时唯一可见、带 provenance 的论文、数据、代码、补充材料和资源记录 |
| SubmissionBundle | 被测系统产出的 manifest 与实际 artifacts |
| 评估协议 | evaluator 使用私有 oracle 检查 submission 并生成 result 的规则 |
| 引擎适配器 | 将引擎无关的论文包映射为特定引擎调用的桥接模块 |
