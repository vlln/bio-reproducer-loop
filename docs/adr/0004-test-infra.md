---
title: ADR-0004 — 测试基建：CI 静态检查 + 本地测试
description: 测试基础设施选型：CI 仅做静态检查（YAML/JSON Schema/frontmatter），L1/L2/L3 测试在本地运行，LLM 调用不可在 CI 自动化。
type: adr
status: proposed
created: 2026-07-15T00:00:00Z
---

# ADR-0004: 测试基建：CI 静态检查 + 本地测试

---

## 背景

L1/L2/L3 测试需要真实 LLM 调用，GitHub Actions 上没有 LLM 后端。CI 不能运行任何需要 LLM 的测试。

---

## 决策内容

**CI（GitHub Actions）**：仅做静态检查，不做 LLM 相关测试。

静态检查项：
- YAML 格式校验（expected.yaml、metadata.yaml）
- JSON Schema 校验（result.json 格式）
- Markdown frontmatter 完整性检查
- 文档结构检查（必填字段、编号一致性）

**本地测试**：通过 Makefile 提供一键运行脚本。

- `make test-l1` — 运行 L1 单元测试
- `make test-l2` — 运行 L2 集成测试
- `make bench-l3` — 运行 L3 能力基准

**MR 门禁**：开发者本地跑完 L1/L2，结果附在 PR 描述中。CI 只做静态检查。

---

## 备选方案

### 方案 A: CI 静态检查 + 本地 LLM 测试 (采用)

- 优点：CI 不依赖 LLM，可自动化；LLM 测试在本地可控
- 缺点：门禁依赖人工检查

### 方案 B: CI 全量（需要自建 runner）

- 优点：全自动化
- 缺点：需要自建带 LLM 后端的 runner，成本高，现阶段不必要

---

## 验证

| 验证项 | 复现步骤 | 结论 | 经验 | 验证 Branch |
|--------|---------|------|------|------------|
| CI 静态检查可运行 | 提交 PR，触发 GitHub Actions | 待验证 | — | — |
| make test-l1 可运行 | 本地执行 `make test-l1` | 待验证 | — | — |

---

## 后果

### 正面

- CI 不依赖 LLM，完全自动化
- 本地测试脚本简单，Makefile 即可

### 负面

- MR 门禁依赖开发者自觉跑 L1/L2
- 无法自动检测 LLM 行为回归

---

## 约束范围

- `.github/workflows/` CI 配置
- `Makefile` 本地测试脚本
- `tests/` 目录结构

---

## 约束规则

| 规则编号 | 规则 | 适用范围 | 违反时如何检出 |
|----------|------|---------|--------------|
| AR-001 | CI 不运行任何需要 LLM 调用的测试 | CI 配置 | CI 配置审查 |
| AR-002 | 本地测试通过 `make test-l1` / `make test-l2` / `make bench-l3` 运行 | 开发者本地 | Makefile 存在且可执行 |
| AR-003 | PR 描述必须包含 L1/L2 测试结果 | PR 流程 | PR 模板检查 |