---
title: ADR-0008 — Entry 分类与共享资源复用
description: 将论文身份与可评分复现任务分离，以正交 taxonomy 描述 entry，并允许通过内容寻址对象去重相同材料而保持每个 InputBundle 语义独立。
type: adr
status: accepted
created: 2026-07-21T00:00:00Z
---

# ADR-0008: Entry 分类与共享资源复用

## 背景

ADR-0007 使用 L3/L4/L5 表达构造输入、冻结真实材料与在线资源发现，但同一篇论文可以有
多个边界不同的复现任务，例如官方 processed output 验证、从 raw data 重建 workflow、
单个 figure 重建和历史环境考古。Level 无法同时表达论文来源、复现目标、资源模式、
证据类型和环境要求；把整篇论文压成一个 entry 会使 scored scope 和成功定义模糊。

同一论文拆成多个 entry 后，原始 PDF、supplementary 和代码 snapshot 可能重复。直接在
每个 `input/` 复制相同字节浪费仓库与分发空间；直接引用共享路径或使用跨目录 symlink，
又会破坏 entry 独立发布、bundle hash、path isolation 和单 entry staging。

本 ADR 补充 ADR-0005/0007，不改变 InputBundle、SubmissionBundle 与 private oracle 的
运行时信任边界。

## 决策内容

### 1. Paper 与 Entry 是不同身份

Paper 表示稳定的发表对象及其资源集合；Entry 表示一个可独立运行和评分的复现任务。
同一 paper 可以对应多个 entry，但每个 entry 必须有明确、单一的 scored scope、自己的
oracle、版本和 execution profile。Entry ID 仍是评分与结果聚合的主键；paper identity
只用于关联、查询和资源复用。

### 2. 分类使用正交维度

L3/L4/L5 继续表达公开 benchmark 的环境真实性和资源冻结层级，不再承担论文或任务的
完整分类。下一次 metadata schema revision 应至少定义以下正交维度：

| 维度 | 典型取值 |
|------|----------|
| `paper_origin` | `constructed` / `real_preprint` / `real_published` |
| `reproduction_target` | `result_verification` / `derived_data_reanalysis` / `raw_workflow` / `figure_reconstruction` |
| `resource_mode` | `bundled` / `external` / `restricted` / `mixed` |
| `environment_mode` | `frozen` / `contemporary` / `historical` / `unavailable` |
| `evidence_type` | `numeric` / `set` / `figure` / `qualitative` / `mixed` |
| `interaction_mode` | `offline` / `discovery` / `tool-runtime` |
| `scientific_domain` | 例如 `bulk_rnaseq` / `single_cell` / `imaging` / `proteomics` |

Taxonomy 用于发现、分层采样和能力覆盖分析，不决定目录布局，也不允许绕过 entry 自己的
bundle、oracle 或 evaluator。一个任务需要多个主要复现目标且不能形成单一成功定义时，
应拆成多个 entry；仅包含多个相互依赖的评分证据时可以保留为一个 mixed-evidence entry。

### 3. Entry 保留完整资源声明

每个 entry 必须独立声明运行时可见的完整 resource inventory，即使相同资源已被其他
entry 声明。该重复是必要的语义冗余：删除、改版或单独发布一个 entry 时，另一个 entry
的输入契约不能隐式变化。

相同内容可以由 benchmark package 或外部对象存储按 SHA256 保存一次。Entry manifest
引用 immutable object identity，并为本 task 声明独立的 role、authority、目标 path 和
provenance。只有内容 hash 相同的资源可以复用对象；语义相似、不同版本或不同派生过程的
文件不能因为文件名相同而合并。

### 4. Curator 物化 entry-local InputBundle

共享对象库属于可信 Curator 控制面，不直接挂载给被测系统。Runner/Curator 在执行前：

1. 解析该 entry manifest 中声明的对象；
2. 校验 content hash 和可用性；
3. 通过 copy、reflink 或受控 hardlink 物化普通文件到本次 staged `input/`；
4. 拒绝 path collision、缺失对象、hash mismatch 和未声明文件；
5. 只将物化后的 entry-local `/input` 只读挂载进 sandbox。

跨 entry symlink、指向共享仓库的 runtime path 和共享对象库 mount 均被禁止。分发单个
entry 时，publisher 必须随包物化所需对象或提供可验证的对象获取机制；消费者不需要了解
其他 entry。

### 5. 延迟实现共享对象层

当前只有 bench-100 一个真实论文 task，现有 entry 继续使用自包含 `input/` 和
`bundle.yaml`。出现同一论文的第二个 task，或重复材料显著影响 Git/发布包体积时，再通过
独立 Plan 扩展 bundle schema、validator、Curator 和 packaging。不得在 schema 未冻结前
将 ad hoc `object_sha256` 字段加入现有 bundle。

### 6. 版本与结果失效规则

| 变化 | 版本/结果处理 |
|------|---------------|
| 只增加不影响执行的 taxonomy 标签 | 旧运行仍有效 |
| 修改 paper identity 的文字或 locator，内容 hash 不变 | 保留运行，更新审计记录 |
| 修改 InputBundle 字节、resource availability 或 scored scope | 提升 entry/benchmark version，重新执行 |
| 修改 rubric/check/tolerance | 提升 oracle version，至少重新 evaluation |
| 修改 sandbox/runtime 要求 | 旧结果仅作历史观测，重新执行后才能进入当前 baseline |
| 修改 Input/Submission/Oracle 信任关系 | 新 protocol major version |

## 选择理由

- Entry 保持可独立运行、评分、发布和撤回。
- 正交分类避免继续给 L3/L4/L5 增加互不相关的含义。
- 内容寻址复用消除大文件字节重复，同时不牺牲 manifest 可审计性。
- Curator 物化保持 Plan 005 的 sandbox mount 和路径边界不变。
- 延迟实现避免在只有一个真实论文 task 时提前引入对象存储复杂度。

## 后果

### 正面

- 同一论文可以安全承载不同成本和成功定义的 benchmark task。
- 可按论文来源、复现目标、科学域或环境模式分别统计表现。
- 单 entry 分发与全量 benchmark 分发都能保持可验证和可去重。

### 负面

- Manifest 会重复声明公共资源，Curator 需要维护 object-to-path materialization。
- Taxonomy 需要受控词表与 schema 演进，不能继续依赖自由文本 `scenario`。
- Hardlink/reflink 优化具有平台差异，正确性必须以 hash 和 staged 普通文件为准。

## 约束规则

| 规则编号 | 规则 | 检出方式 |
|----------|------|----------|
| ET-001 | 一个 entry 必须有明确 scored scope 和独立 oracle | metadata/oracle review |
| ET-002 | 同 paper 的多个 entry 不共享隐式输入状态 | bundle contract test |
| ET-003 | 资源只按 content hash 去重，不按名称或描述去重 | object resolver test |
| ET-004 | 被测系统只能看到物化后的 entry-local InputBundle | Docker escape probe |
| ET-005 | 禁止跨 entry symlink 和共享对象库 runtime mount | validator + mount inspection |
| ET-006 | Input、oracle 或 runtime 边界变化必须按表中规则使旧结果失效 | release checklist |

## 验证

| 验证项 | 复现步骤 | 预期结论 |
|--------|----------|----------|
| 同 paper 双 task | 两个 entry 引用同一 PDF object、不同 task data | 两个 manifest 独立有效，对象只存一份 |
| 独立发布 | 只打包其中一个 entry | 物化包包含该 entry 所需全部普通文件 |
| 对象漂移 | 用不同字节替换共享对象但保留 object ID | hash mismatch，拒绝 staging |
| 路径逃逸 | entry 使用 symlink 指向共享对象库 | `INVALID_BUNDLE` |
| 任务变更 | 将 processed verification 改成 raw workflow 但不提升版本 | release gate 拒绝沿用旧结果 |
