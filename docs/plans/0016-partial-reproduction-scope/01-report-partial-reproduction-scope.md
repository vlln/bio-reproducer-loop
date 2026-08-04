---
title: 部分复现范围 scope 入口执行报告
description: scope 参数实现结果：入口契约、agent prompt 变更、adapter/validator 联动、测试与验证证据
type: report
status: complete
created: 2026-08-04T00:00:00Z
---

# 部分复现范围 scope 入口执行报告

## 结果

范围全部完成。`pytest tests/unit` 124 通过（118 原有 + 6 新增）；loopflow 0.28.0
源码下 `load_loop`（args 含 scope）+ 7 个 agent `parse_agent` + `render_template`
（含 `{{ scope }}`）全部通过。

## 入口契约

| 层 | 变更 |
|----|------|
| `loop.md` args | 新增 `scope`（可选，默认 `""`）。约定写法：`figures=figure4,figure5`、目标 ID（`T1,T2`）或自由文本 |
| `workflow.py` | `common` 增加 `scope=args.get("scope","")`，透传全部 7 个 agent |
| `_base.md` | input schema 增加 `scope`（可选）；新增「复现范围」工作约定：空=全论文；非空=只处理范围内目标，范围外标注 `out-of-scope` 不执行重活、不评分、不声称完成；以 plan.md Reproduction Target 表为范围权威 |
| `reader.md` | 运行上下文显示 `复现范围: {{ scope }}`；Paper Understanding 仍读全文；Reproduction Target 表只列范围内目标（T 从 T1 连续重排）；Decision Record 记录 scope 决策原文与解读 |
| `data/provision/run.md` | 目标节注明只获取/部署/运行范围内目标所需资源，范围外记录但标记 `out-of-scope` |
| `validate.md` | 检查项只从范围内 targets 推导；report 明示 scored scope 与 out-of-scope 说明 |
| `package.md` | README 与入口脚本只覆盖范围内目标并明示范围 |
| `benchmarks/runner/adapters/loopflow.py` | metadata.yaml 可选 `scope` → `--args scope`（物化 ADR-0008：一个 entry = 一个 scored scope） |
| `benchmarks/runner/bundle_validator.py` | metadata `scope` 声明时必须为非空字符串 |

## 测试（新增 6 例）

- `test_bundle_validator.py`：scope 可选接受、空 scope 拒绝
- `test_loop_workflow.py`：scope 透传所有 agent、缺省为空串
- `test_runtime_isolation.py`：adapter 声明 scope 时透传、未声明时省略

## 证据

- 测试：`pytest tests/unit` 124 passed
- 加载验证：loopflow 0.28.0 源码 `load_loop` 解析 args 含 scope；7 agent 模板渲染含「复现范围」块

## 遗留

- **component eval 基线**：CONTRIBUTING §7 要求 agent prompt 变更附 eval 报告；
  当前 eval harness（BL-001 修复后可用）需补跑部分复现语义的 component case
  （如：scope=figure4 时 reader 只产出 figure4 目标、validate 只验证范围内检查项）
- paper-01 可利用新入口重试部分复现（figures=figure4,figure5,figure6），归档远端
  /tmp 素材后可作为首个 scope 真实用例
