---
title: benchmark 与 bio-reproducer 解耦（scored_scope）执行报告
description: 改名、边界翻译、bench-100 示例、benchmark 2.1.0 发布准备完成
type: report
status: complete
created: 2026-08-04T00:00:00Z
---

# benchmark 与 bio-reproducer 解耦执行报告

## 结果

范围完成。`pytest tests/unit` 125 通过；7 个 entry bundle validator 全过。

## 变更

| 层 | 变更 |
|----|------|
| benchmark 协议 | `metadata.yaml` 字段 `scope` → `scored_scope`（ADR-0008 结构化声明；值用目标 ID/描述等 benchmark 域语义）|
| adapter | 边界翻译：`metadata.scored_scope` → `--args scope`（引擎耦合只发生在此层）|
| bundle_validator | 校验 `scored_scope` 非空字符串 |
| bench-100 | 补声明：`Processed-output RNA-seq scope (DEG analysis and volcano figure), excluding raw alignment, microarray, GWAS and wet-lab components` |
| benchmark 版本 | `benchmarks/VERSION` 2.0.0 → **2.1.0**（新增 bench-003 + scored_scope 协议增强）；CHANGELOG 合并遗留 Unreleased 条目（bundle fidelity、VM 边界、worker、artifact、formal smoke）并归档 |
| loop 侧 | `scope` arg 保持不变（bio-reproducer 引擎特性，与 benchmark 无关）|

## 兼容性

- `scope` 字段从未随任何已发布 benchmark 版本流出（2.0.0 发布于 0016 之前），改名无破坏性
- 项目 v0.2.0 已发布不受影响；benchmark 版本独立演进

## 遗留

- 若后续正式发布 benchmark（2.1.0），需在独立发布渠道（如独立 repo/制品）同步
- scored_scope 的取值规范（目标 ID vs 自由文本）可后续在 Interface 文档细化
