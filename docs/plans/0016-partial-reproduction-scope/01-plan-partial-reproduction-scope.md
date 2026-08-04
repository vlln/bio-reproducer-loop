---
title: 部分复现范围 scope 入口
description: 为 bio-reproducer 新增 scope 参数：限定只复现指定 figure/目标的部分复现能力，贯通 Reader→Data→Run→Validate→Package 与 benchmark adapter
type: plan
status: done
created: 2026-08-04T00:00:00Z
---

# 部分复现范围 scope 入口

## 背景

paper-01（ClaroAI-Bench，多组学管线论文）试跑发现：论文只需复现部分目标
（某些 figure），但 bio-reproducer 没有声明"复现范围"的 prompt 入口——
reader 全量枚举目标、validate 全量验证、data/run 全量执行。部分复现是真实
论文与 bench 场景的常见需求（ADR-0008 已定义 entry 的 scored scope 概念，
但执行层无法下达）。

## 范围

1. `loop.md` 新增可选 arg `scope`（空=全论文；非空=限定范围）
2. `workflow.py` common 透传 scope 给全部 7 个 agent
3. `_base.md` 增加 scope input schema 与「复现范围」工作约定（out-of-scope 纪律）
4. reader：Paper Understanding 仍读全文，Reproduction Target 表只列范围内目标、T 连续重编号，Decision Record 记录 scope 决策
5. data/provision/run/validate/package：只处理范围内目标，范围外不执行/不评分/不声称完成；validate 明示 scored scope
6. benchmark adapter：metadata.yaml 可选 `scope` 字段透传 `--args scope`；bundle_validator 校验 scope 非空字符串
7. 确定性测试 + 文档

## 验证

- `pytest tests/unit` 全绿（新增 6 用例）
- loopflow 0.28.0 源码 `load_loop` + 7 agent `parse_agent` + `render_template`（含 scope）全过
- 行为说明：agent prompt 变更按 CONTRIBUTING §7 需 eval 报告，后续补 component eval

## 关联

- BL-006（部分复现范围入口）
- ADR-0008（entry 单一 scored scope）——scope 参数是其执行层物化
- paper-01 试跑（references/benchmark-discuss.md §11）
