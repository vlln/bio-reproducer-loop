---
title: AC 003 — InputBundle 材料真实性与 provenance
description: 验收 L3/L4/L5 分层输入、资源清单、原始与派生材料、cited resource 完整性和答案隔离。
type: ac
status: proposed
created: 2026-07-20T00:00:00Z
---

# AC-0006: Entry Bundle Lock

验证所有 staged 文件均可追溯，且 bundle lock 与 private oracle 都不会暴露给被测系统。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0006-N-1 | L3 entry 包含 constructed Markdown、构造 CSV 和完整 bundle.yaml | 执行 bundle validator | 校验通过，所有 path、hash 和 source 一致 | 自动化 |
| AC-0006-N-2 | L4 entry 包含 original PDF、派生 Markdown、supplementary、代码快照和 bundle.yaml | 执行 validator | 校验通过，派生链可追溯到 original | 自动化 + 人工审查 |
| AC-0006-N-3 | L5 entry 只提供 original paper 和 external DOI/accession | 执行 validator | 校验通过，external resource 允许无本地 path | 自动化 |
| AC-0006-N-4 | entry 同时包含 bundle、metadata、input 和 private oracle | stage InputBundle | 工作目录只出现 input 内容；bundle、metadata、oracle 和 injection intent 均不可见 | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0006-B-1 | 论文明确说明未公开代码 | bundle lock 使用 unavailable 并记录核查 URL/时间 | entry 有效；被测系统不直接看到审计结论 | 自动化 + 人工审查 |
| AC-0006-B-2 | 数据受访问控制限制，且限制可从论文或运行环境观察 | bundle lock 使用 restricted 并记录 accession/访问要求 | L4 entry 有效，执行结果允许按可观察 limitation 降级 | 自动化 + 人工审查 |
| AC-0006-B-3 | L4 使用完整数据的裁剪子集 | 提供原始 descriptor、转换脚本、参数和 checksum | 派生数据有效，但 staged material 明确 scope 只覆盖子集 | 自动化 + 人工审查 |
| AC-0006-B-4 | 构造 L3 引用故意不可用的仓库 | bundle lock 记录目标状态，private oracle 记录注入意图 | 被测系统只能通过论文和环境观察不可用，不看到控制面结论 | 自动化 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0006-E-1 | bundled 文件 hash 与 bundle lock 不一致 | 执行 validator | 返回 INVALID_BUNDLE | 自动化 |
| AC-0006-E-2 | `input/data/.counts_full.csv` 未在 bundle lock 中声明 | 执行 validator | 返回 INVALID_BUNDLE，指出未声明文件 | 自动化 |
| AC-0006-E-3 | resource path 使用绝对路径或 `..` | 执行 validator | 返回 INVALID_BUNDLE，不读取 entry 外文件 | 自动化 |
| AC-0006-E-4 | derived resource 缺少 derived_from 或 transform | 执行 validator | 返回 INVALID_BUNDLE | 自动化 |
| AC-0006-E-5 | bundle lock 包含 expected score、rubric 或 expected verdict | 执行 validator | 返回 INVALID_BUNDLE，指出 forbidden field | 自动化 |
| AC-0006-E-6 | Runner 将 bundle.yaml 或 metadata.yaml 复制到工作目录 | 执行 staging contract test | 测试失败，禁止调用被测系统 | 自动化 |
| AC-0006-E-7 | bundle lock 声明 restricted，但 input 和环境均无法观察该限制 | 执行 fidelity review | 不得据此放宽 evaluator 判定 | 自动化 + 人工审查 |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0006-F-1 | entry 声明 L4/real_published，但只提供人工摘要 Markdown | 执行 release fidelity gate | 拒绝进入 L4 或建立 baseline | 自动化 + 人工审查 |
| AC-0006-F-2 | 论文引用 Supplement S1 和代码仓库，bundle 无文件也无状态记录 | 执行 cited-resource audit | gate 失败，列出未处置引用 | 人工审查 |
| AC-0006-F-3 | 裁剪 CSV 静默代表论文完整数据 | 对照 paper claim、bundle lock 与文件维度 | gate 失败，要求明确 scope 和转换 provenance | 人工审查 |

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
| AC-0007-B-1 | L4 原始文件因许可不可入 Git，但可存对象存储 | bundle lock 提供 resolver、hash 和 license | 可进入 L4，release bundle 可确定性解析同一对象 | 自动化 + 人工审查 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0007-E-1 | metadata、bundle 的 level/paper_type 相互冲突 | 执行 validator | INVALID_BUNDLE | 自动化 |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0007-F-1 | entry 未通过 fidelity gate | 尝试建立 tracked baseline | 操作被拒绝 | 自动化 |
