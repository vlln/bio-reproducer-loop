---
title: Plan 025 — scored_scope 删除与 ClaroAI claims 模式落地
description: 删除 scored_scope 机制（字段/adapter 透传/CC-002/verify 锚点），ClaroAI entry 恢复 claims 模式（D5 数值声明转录 + 容差 comparator），6 篇校准 run 离线重评并与作者 D5 校准对照。
type: plan
status: done
created: 2026-08-12T00:00:00Z
---

# 计划

## 目标

1. 删除 `scored_scope` 机制：entries 字段、adapter 透传、validator CC-002、verify.py
   交叉锚点、spec/interface/ADR 文档引用。
2. 任务语义迁移：ClaroAI entry 补填 `reproduction_target` + 自然语言 `task`；
   bench-100 描述迁入 `task`；系统侧不再出现评分维度代码。
3. D5 claims oracle：converter 从 scores.json D5 evidence 转录数值声明
   （`pub=/repr=`、`reproduced=,published=`、单行 `HR =`、`match paper` 计数），
   `check_claim` 容差/阈值比较；6 篇校准 run 离线重评并与作者 D5 校准对照。

## 执行单元

| # | 任务 | 状态 |
|---|------|------|
| 1 | converter v0.2.0 重写（metadata/task/claims/rubric/verify 模板） | done |
| 2 | 35 entry 重生成（零数据漂移验证）+ bench-223 AUROC 阈值 claim 手工补 | done |
| 3 | bench-100 迁移（reproduction_target + task） | done |
| 4 | adapter 改读 task；validator CC-002 rev. + scored_scope 禁令 | done |
| 5 | evaluate_run.py 支持 claims evidence（--claims-evidence / validate report） | done |
| 6 | 测试更新 + 回归（维度代码禁入系统侧、check_claim 容差、scored_scope 拒绝） | done |
| 7 | 6 篇离线重评 + 与作者 D5 校准对照 | done |
| 8 | 文档同步：ADR-0010 修订、Interface 0002 v2、Spec 0001、AC-0005 | done |

## 验证

- 全量测试 141 passed / 4 skipped；
- 42 个 entry 全部通过 bundle gate（含新 CC-002 rev.）；
- 6 篇离线重评结果见 Report 025。
