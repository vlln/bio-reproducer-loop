# Backlog

工程需求池。DESIGN 阶段的迭代候选只能从这里拉取；选定后状态改为 `planned` 并记录关联迭代。

状态值：`candidate`（待评估）→ `planned`（已排入迭代）→ `done`（已闭环）/ `dropped`（放弃，需注明原因）

| 编号 | 标题 | 描述 | 来源 | 状态 | 关联迭代 |
|------|------|------|------|------|---------|
| BL-001 | eval harness 修复 `--only-phase` 断裂 | loopflow 0.24.0（ADR-0052）删除 `--only-phase`/`--from-phase`，`evals/runner/loopflow.py:40` 仍使用该选项，12 个 component case 全部无法运行。修法：run_phase 生成临时单 agent loop（workflow 一行调用 `agent(agent_def=case["phase"])`），复用 `loops/bio-reproducer/agents/`；长期方案见 loopflow BL-047（单 agent 运行入口） | loopflow 0.25.1 迁移时发现 2026-07-28 | candidate | — |
| BL-002 | 删除 `.skills/bio-reproducer/` 死代码 | 该目录（SKILL.md + 7 个 references，1363 行）不被任何 agent 的 `skills:` 声明，loopflow 永不注入；它是 agents/*.md 的历史母本，曾是多起 drift 矛盾（图表必须性、schema enum、输出清单）的根源。删除前确认 agents/*.md 已完全自包含 | loopflow 0.25.1 迁移分析 2026-07-28 | candidate | — |
| BL-003 | resume_from 阶段级重跑入口 | Validate 发现问题后需重做上游阶段时，目前只能整个新 run。等 loopflow BL-043（phase 级重做/replay 缓存作废）方向明确后，决定用引擎原生机制还是 workflow 参数实现 | loopflow 0.25.1 迁移讨论 2026-07-28 | candidate | — |
