---
title: loopflow 0.25.1 迁移执行报告
description: bio-reproducer loop 迁移 loopflow 0.25.1 的执行结果与证据留档
type: report
status: complete
created: 2026-07-28T10:04:37Z
---

# loopflow 0.25.1 迁移执行报告

## 结果

全部 9 项范围完成。`pytest tests/unit` 109 通过（102 原有 + 7 新增 smoke），loopflow 0.25.1 源码 `load_loop` / `check_skills` / jsonschema 校验全部通过。

## 关键设计决策

1. **Schema 只保留程序消费的字段**。审计发现 workflow 唯一消费的返回字段是 `payload.verdict`；其余 phase 的 output schema（含 missing[]/decisions[]/status 映射）无消费者，全部删除，agent 改返回自然语言简报。真正的产出契约由阶段文件（plan.md、provision.md、metrics.json 等）承载。validate 保留 `payload.verdict`（enum，Package 门控），详细评分结构留在 metrics.json/report.md 模板。
2. **图表必选**。validate.md/run.md 的"必须"与 .skills 母本的"可选"长期矛盾，裁决为必选；删除 generate/visual-validate 全局模式门控（reproduction_options.md 只保留产出语言配置），保留"无视觉多模态能力记 blocked、不得编造视觉相似性"的诚实性规则。
3. **intervene 走 workflow 侧 replay 模式**，不依赖 backend durable session（deepseek-v4-pro 未验证该能力）；benchmark 无人值守经 `confirm_plan=false` 跳过。
4. **`consent` 权限模式**（ask/auto）解决 agent 定义中"询问用户"无通道的缺陷：ask 下 agent 汇总计划并停止报告，不得假装已询问；benchmark 沙箱传 auto（一次性环境，同意隐含）。
5. **fail-fast 与 replay 缓存的相互作用**已记入失败日志提示：幻觉完成的 phase 缓存会毒害 recover，需开新 run 重跑；框架级解法见 loopflow BL-043。

## 迁移分析结论（12 条旧缺陷裁决）

1 条错误（PARTIAL 路径死代码——混淆引擎层 status 与业务层 verdict）、6 条成立、4 条部分成立、1 条已过时。新发现 2 项：quay skill 缺失（已修）、validate.md 引用 agent 不可见的 SKILL.md Rollback Protocol（已修）。

## 证据

- 测试：`tests/unit/test_loop_workflow.py`（7 用例：happy path、Reader 幻觉 fail-fast、确认门终止/跳过、FAILED 跳过 Package、缺 data_manifest 停 Run 前、phase blocked 传播）
- 加载验证：`load_loop` 解析 loop.md（args/phases/failure_threshold 生效）；8 个 agent `parse_agent` + extends 合并 + `check_skills` 全过
- CHANGELOG Unreleased 已记录全部变更

## 遗留

- loopflow 侧 BL-042~047（框架级候选，已录入其 backlog）
- 本项目 BL-001（eval harness `--only-phase` 断裂）、BL-002（.skills 死代码清理）、BL-003（resume_from 待 loopflow BL-043）
- 远端服务器（gs）同步：loop 代码、pixi install-skills（quay）、远端 loopflow ≥0.25.1
