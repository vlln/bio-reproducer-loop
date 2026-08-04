---
title: ADR-0005 — 独立评估与答案隔离
description: Benchmark 将输入、提交物和私有 oracle 分离，最终分数与 verdict 只能由独立 evaluator 根据实际产物生成。
type: adr
status: accepted
created: 2026-07-19T00:00:00Z
---

# ADR-0005: 独立评估与答案隔离

## 背景

当前 adapter 从被测系统 Validate Phase 生成的 `metrics.json` 读取 `score` 和
`verdict`，evaluator 又基于这些自评字段计算通过率。与此同时，论文输入、
`expected.yaml` 和 `golden/` 位于同一目录。该设计无法保证评分独立，也无法防止
被测系统读取评估答案。

本 ADR supersede ADR-0002 中“被测系统直接产出权威 `result.json`”的决定。

## 决策内容

Benchmark 采用三方协议：

1. **Input bundle**：只包含论文、公开数据和允许使用的补充材料。
2. **Submission bundle**：被测系统生成的 artifact manifest、实际产物和可选的
   claimed verdict。
3. **Private oracle**：包含科学事实、评分规则、容差和验证程序，只对 evaluator
   可见。

最终 `score`、`verdict` 和 `result.json` 只能由 benchmark evaluator 生成。被测
系统的自评结果可以作为“校准能力”评测项，但不得作为最终评分依据。

Runner 必须将 input bundle stage 到隔离工作目录。运行期间不得向被测系统挂载
`oracle/`、历史结果或 baseline。

## 目录约定

```text
benchmarks/entries/<entry-id>/
├── input/
│   ├── paper.pdf
│   └── data/
├── oracle/
│   ├── claims.yaml
│   ├── rubric.yaml
│   ├── expected-results/
│   └── verify.py
└── metadata.yaml
```

公开开发集可以发布 oracle，但 runner 仍须做运行时隔离。用于正式排名的测试集
应隐藏 oracle。

## 选择理由

- Benchmark 的可信度要求评分方与被测方分离。
- 对实际 CSV、图像、日志和可执行脚本评分，比解析 Agent 自述更可靠。
- Input/oracle 隔离可降低答案泄漏和无意污染风险。
- Submission manifest 允许不同复现系统使用不同内部目录结构。

## 后果

### 正面

- 分数具有独立、可审计的来源。
- 系统自评质量可以被单独测量。
- 可支持公开开发集与隐藏测试集。

### 负面

- 需要为每个 entry 维护可执行或结构化 oracle。
- Adapter 需要生成统一的 artifact manifest。
- 现有 entry 和历史 result 需要迁移，旧结果不可与新协议直接比较。

## 约束规则

| 规则编号 | 规则 | 检出方式 |
|----------|------|----------|
| AR-001 | 被测系统运行时不可读取 `oracle/` | 隔离工作目录测试 |
| AR-002 | 最终 score/verdict 只能由 evaluator 生成 | result provenance 检查 |
| AR-003 | evaluator 必须检查实际产物，不接受自报分数作为证据 | evaluator 单元测试 |
| AR-004 | baseline 不得存入 entry metadata 或 oracle | 静态目录检查 |
| AR-005 | 每个自动检查项必须声明 evidence、comparison 和 tolerance | rubric schema 校验 |

## 验证

| 验证项 | 复现步骤 | 预期结论 |
|--------|----------|----------|
| 自评隔离 | 提交伪造的满分 claimed verdict，但提供错误产物 | evaluator 判定失败 |
| 答案隔离 | 在 adapter 执行期间尝试读取 entry oracle | 路径不可见 |
| 产物评分 | 提交正确结果表但 claimed verdict 为 FAILED | 按实际产物评分，自评只进入校准指标 |
