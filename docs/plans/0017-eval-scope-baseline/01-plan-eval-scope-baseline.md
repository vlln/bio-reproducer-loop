---
title: scope 语义 component eval 基线
description: 补跑 BL-006 遗留的 scope 部分复现语义 component eval：新增 reader-scoped-targets case 并用真实 LLM 建立基线
type: plan
status: done
created: 2026-08-04T00:00:00Z
---

# scope 语义 component eval 基线

## 背景

0016 容器实现了 `scope` 部分复现入口，遗留项：按 CONTRIBUTING §7，agent prompt
变更需附 component/handoff eval 报告；当时 eval harness 已可用但未跑 scope 语义。
本容器补跑：新增 scope 语义 eval case，用真实 LLM（deepseek-v4-pro，经 claude CLI
代理）建立基线。

## 范围

1. `evals/runner/loopflow.py`：`run_phase` 支持 `case.scope` → `--param scope=...`
2. 新增 case `reader-scoped-targets`：bench-001，`scope=figures=figure1`；断言
   plan.md Reproduction Target 限定范围内目标、Decision Record 记录 scope 决策、
   不出现范围外 figure
3. case schema 增加可选 `scope` 字段；coverage.yaml 登记
   `partial_reproduction_scope` capability；case 计数 14→15
4. 真实 LLM smoke 运行（1 run）并留档证据

## 验证

- `pytest tests/unit` 全绿（124）
- `pytest evals/component -k scoped --eval-profile smoke` 真实 LLM PASSED

## 关联

- BL-006（部分复现范围入口）的遗留闭环
- 0016-partial-reproduction-scope
