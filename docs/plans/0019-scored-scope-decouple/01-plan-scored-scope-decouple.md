---
title: benchmark 与 bio-reproducer 解耦（scored_scope）
description: 修正 0016 设计缺陷——把 bio-reproducer 的 scope 概念改名为引擎无关 scored_scope，翻译留在 adapter 边界，benchmark 版本 2.1.0
type: plan
status: done
created: 2026-08-04T00:00:00Z
---

# benchmark 与 bio-reproducer 解耦（scored_scope）

## 背景

0016 把 loop 的 `scope` 参数（bio-reproducer 引擎特性，`figures=` 语法）直接
写进了 benchmark `metadata.yaml` 协议。违反 ADR-0005/0006「三域拆分 + 引擎
无关」原则：benchmark 应可独立发布、被任何复现系统采用，协议不应携带
bio-reproducer 特有概念。ADR-0008 本就要求 entry 声明 scored scope，但当前
只有描述文本、无结构化字段。

## 范围

1. `metadata.yaml`：`scope` → 引擎无关 `scored_scope`（值用 benchmark 域语义）
2. adapter（唯一引擎耦合层）在边界翻译 `scored_scope` → loop `--args scope`
3. bundle_validator 校验 `scored_scope` 非空字符串
4. bench-100 补 scored_scope 示例声明
5. benchmark 版本 2.0.0 → 2.1.0 + benchmarks/CHANGELOG（含遗留 Unreleased 归位）

## 验证

- `pytest tests/unit` 全绿（125）
- 7 个 entry bundle validator 全过

## 关联

- ADR-0005/0006（引擎无关）、ADR-0008（scored scope 结构化）
- 0016 设计缺陷修正；loop 侧 `scope` arg 保持不变（引擎特性）
