---
title: ADR-0001 — 技术栈：Python + pytest + loopflow
description: 基准测试体系的技术选型：使用 Python 编写测试和 runner，pytest 作为 L1/L2 测试框架，loopflow 作为 Agent 执行引擎。
type: adr
status: superseded
created: 2026-07-15T00:00:00Z
---

# ADR-0001: 技术栈：Python + pytest + loopflow

> 2026-07-19: 测试框架与结果格式部分已由 ADR-0005/0006 supersede。
> Python、pytest 和 loopflow 仍保留，但真实 LLM 用例迁移到 `evals/`，结果协议改为 submission 与 evaluator result 分离。

---

## 背景

基准测试体系需要：L1/L2 测试框架、L3-L5 执行器、结果评估器。需选择技术栈。

bio-reproducer 本身是 Python loopflow workflow，loopflow 提供 Python API。团队主要使用 Python。

---

## 决策内容

- **L1/L2 测试框架**：pytest
- **L3-L5 执行器**：Python CLI（`benchmarks/runner/`），通过 loopflow Python API 或 CLI 调用 bio-reproducer
- **结果格式**：JSON（result.json）+ YAML（expected.yaml）

---

## 备选方案

### 方案 A: Python + pytest + loopflow (采用)

- 优点：与 bio-reproducer 同语言，loopflow 原生 API，pytest 生态成熟
- 缺点：Python CLI 功能不如 TypeScript 丰富

### 方案 B: TypeScript + reprobench

- 优点：reprobench 已有部分设计文档，ACP 协议支持
- 缺点：reprobench 已搁置，需要额外维护 TypeScript 项目，与 bio-reproducer 不同语言

---

## 选择理由

- bio-reproducer 和 loopflow 都是 Python，同语言降低维护成本
- pytest 是 Python 生态最成熟的测试框架
- reprobench 的设计概念可参考，但不继承其代码

---

## 验证

| 验证项 | 复现步骤 | 结论 | 经验 | 验证 Branch |
|--------|---------|------|------|------------|
| pytest + loopflow 集成 | 用 pytest 编写 L1 测试，通过 loopflow 调用真实 LLM 运行单个 Phase | 待验证 | — | — |

---

## 后果

### 正面

- 单一语言栈，降低维护成本
- loopflow 原生 API 直接可用
- pytest 插件生态丰富

### 负面

- 若有非 Python 的复现系统想用基准，需要额外的适配层

---

## 约束范围

- 所有测试代码（`tests/`）
- 所有 runner 代码（`benchmarks/runner/`）
- 所有 CI 配置

---

## 约束规则

| 规则编号 | 规则 | 适用范围 | 违反时如何检出 |
|----------|------|---------|--------------|
| AR-001 | L1/L2 测试使用 pytest 编写 | `tests/` | CI 配置检查 |
| AR-002 | Runner 使用 Python 编写 | `benchmarks/runner/` | 目录结构检查 |
