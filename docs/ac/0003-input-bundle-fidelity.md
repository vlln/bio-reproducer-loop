---
title: AC 003 — InputBundle 材料真实性与 provenance
description: 验收 L3/L4/L5 分层输入、资源清单、原始与派生材料、cited resource 完整性和答案隔离。
type: ac
status: proposed
created: 2026-07-20T00:00:00Z
---

# AC-0006: InputBundle Manifest

验证所有 staged 文件均可追溯，且 manifest 不泄露 private oracle。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0006-N-1 | L3 bundle 包含 constructed Markdown、构造 CSV 和完整 manifest | 执行 InputBundle validator | 校验通过，所有 path、hash 和 source 一致 | 自动化 |
| AC-0006-N-2 | L4 bundle 包含 original PDF、派生 Markdown、supplementary 和代码快照 | 执行 validator | 校验通过，派生链可追溯到 original | 自动化 + 人工审查 |
| AC-0006-N-3 | L5 bundle 只提供 original paper 和 external DOI/accession | 执行 validator | 校验通过，external resource 允许无本地 path | 自动化 |
| AC-0006-N-4 | entry 同时包含 input 与 private oracle | stage InputBundle | manifest 和公开文件可见，oracle 与 robustness injection intent 不可见 | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0006-B-1 | 论文明确说明未公开代码 | manifest 使用 unavailable 并记录核查 URL/时间 | bundle 有效，不要求虚构 code 文件 | 自动化 + 人工审查 |
| AC-0006-B-2 | 数据受访问控制限制 | manifest 使用 restricted 并记录 accession/访问要求 | L4 bundle 有效，执行结果允许按 paper limitation 降级 | 自动化 + 人工审查 |
| AC-0006-B-3 | L4 使用完整数据的裁剪子集 | 提供原始 descriptor、转换脚本、参数和 checksum | 派生数据有效，但公开 scope 明确只覆盖子集 | 自动化 + 人工审查 |
| AC-0006-B-4 | 构造 L3 引用故意不可用的仓库 | manifest 呈现 unavailable 的可观察事实，private oracle 记录注入意图 | bundle 有效，公开输入不泄露评分答案 | 自动化 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0006-E-1 | bundled 文件 hash 与 manifest 不一致 | 执行 validator | 返回 INVALID_INPUT_PROVENANCE | 自动化 |
| AC-0006-E-2 | `input/data/.counts_full.csv` 未在 manifest 中声明 | 执行 validator | 返回 INVALID_INPUT_PROVENANCE，指出未声明文件 | 自动化 |
| AC-0006-E-3 | resource path 使用绝对路径或 `..` | 执行 validator | 返回 INVALID_INPUT_PROVENANCE，不读取 bundle 外文件 | 自动化 |
| AC-0006-E-4 | derived resource 缺少 derived_from 或 transform | 执行 validator | 返回 INVALID_INPUT_PROVENANCE | 自动化 |
| AC-0006-E-5 | manifest 包含 expected score、rubric 或 expected verdict | 执行 validator | 返回 INVALID_INPUT，指出 forbidden field | 自动化 |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0006-F-1 | entry 声明 L4/real_published，但只提供人工摘要 Markdown | 执行 release fidelity gate | 拒绝进入 L4 或建立 baseline | 自动化 + 人工审查 |
| AC-0006-F-2 | 论文引用 Supplement S1 和代码仓库，bundle 无文件也无状态记录 | 执行 cited-resource audit | gate 失败，列出未处置引用 | 人工审查 |
| AC-0006-F-3 | 裁剪 CSV 静默代表论文完整数据 | 对照 paper claim、manifest 与文件维度 | gate 失败，要求明确 scope 和转换 provenance | 人工审查 |

---

# AC-0007: Level-specific Fidelity

验证 L3、L4、L5 的材料要求不会互相替代。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0007-N-1 | constructed paper、synthetic data、fully known oracle | 标记为 L3 并审查 | 可进入 L3，不被要求伪装真实论文材料 | 人工审查 |
| AC-0007-N-2 | 真实原始论文及可获得 cited resources 均已冻结 | 标记为 L4 并审查 | 可进入 L4，离线重复执行使用同一资源版本 | 自动化 + 人工审查 |
| AC-0007-N-3 | 原始论文/DOI 可用，资源由运行时在线发现 | 标记为 L5 并执行 | 记录实际解析资源与外部失败，不作为 CI gate | 系统观测 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0007-B-1 | L4 原始文件因许可不可入 Git，但可存对象存储 | manifest 提供 resolver、hash 和 license | 可进入 L4，release bundle 可确定性解析同一对象 | 自动化 + 人工审查 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0007-E-1 | metadata、manifest 的 level/paper_type 相互冲突 | 执行 validator | INVALID_INPUT_PROVENANCE | 自动化 |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0007-F-1 | entry 未通过 fidelity gate | 尝试建立 tracked baseline | 操作被拒绝 | 自动化 |
