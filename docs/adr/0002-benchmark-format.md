---
title: ADR-0002 — 基准格式：引擎无关的输入/输出协议
description: L3-L5 黑盒基准采用引擎无关的输入（论文包）和输出（result.json）协议，使基准可被任何复现系统使用。
type: adr
status: superseded
created: 2026-07-15T00:00:00Z
---

# ADR-0002: 基准格式：引擎无关的输入/输出协议

> 2026-07-19: 已由 ADR-0005 supersede。保留本文作为历史决策；新协议将被测
> 系统的 submission 与 evaluator 生成的 result 分离。

---

## 背景

L3-L5 基准的目标是成为可公开的论文复现 benchmark 标准。如果基准格式耦合于 bio-reproducer 的实现细节（如 Phase 名称、特定文件路径），则无法被其他复现系统使用。

---

## 决策内容

L3-L5 基准只定义三件事：

1. **输入协议**：论文包（paper.pdf + data/ + expected.yaml），被测系统接受这些输入
2. **输出协议**：result.json（verdict, score, stages, duration, llm_calls, human_interventions），字段引擎无关
3. **评估协议**：对比 expected.yaml 和 result.json 的规则

`stages` 使用数组 `[{name, status}]`，阶段名由被测系统自定，不硬编码 bio-reproducer 的 Phase 名。

---

## 备选方案

### 方案 A: 引擎无关协议 (采用)

- 优点：可被任何复现系统使用，可成为公开标准
- 缺点：需要 adapter 层桥接

### 方案 B: 直接使用 bio-reproducer 的 output schema

- 优点：无需 adapter，直接可用
- 缺点：耦合于 bio-reproducer，无法迁移

---

## 选择理由

- 类比 SWE-bench：不关心 agent 实现，只定义 issue + 测试用例
- adapter 层是单一的耦合点，换引擎只需换 adapter

---

## 验证

| 验证项 | 复现步骤 | 结论 | 经验 | 验证 Branch |
|--------|---------|------|------|------------|
| 协议完整性 | 用 JSON Schema 校验 result.json 格式 | 待验证 | — | — |

---

## 后果

### 正面

- 基准可独立发布，有自己的版本号
- 其他复现系统可参与评测

### 负面

- 需要维护 adapter 层
- 输出字段不能太细（不能包含 bio-reproducer 特有能力）

---

## 约束范围

- 所有 `benchmarks/entries/` 下的论文包定义
- `benchmarks/runner/evaluator.py`
- `benchmarks/runner/adapters/`

---

## 约束规则

| 规则编号 | 规则 | 适用范围 | 违反时如何检出 |
|----------|------|---------|--------------|
| AR-001 | expected.yaml 不含引擎特定字段 | 所有 entries/*/expected.yaml | CI 静态检查 |
| AR-002 | result.json 的 stages 使用 {name, status} 结构 | 所有 runner 输出 | JSON Schema 校验 |
| AR-003 | 基准有独立版本号，与 bio-reproducer 版本解耦 | benchmarks/VERSION | CI 检查 VERSION 文件存在 |
