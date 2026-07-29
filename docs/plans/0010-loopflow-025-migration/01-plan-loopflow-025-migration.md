---
title: loopflow 0.25.1 迁移
description: 将 bio-reproducer loop 适配 loopflow 0.25.1，修复契约缺陷与 benchmark 无人值守接入
type: plan
status: done
created: 2026-07-28T10:04:37Z
---

# loopflow 0.25.1 迁移

## 背景

loop 最后写于 loopflow ~0.19 时代（2026-07-23），loopflow 已发布 0.20~0.25.1 共 8 个版本，其中 0.24.0 删除 phase 抽象（ADR-0052）。迁移分析确认现有写法无 breaking 影响，但有清理空间和若干真实缺陷。

## 范围

1. loop.md 补齐 frontmatter（phases、args、failure_threshold）；workflow.py 删除失效的模块级 meta、为每个 agent 调用加 label
2. Reader 后新增人工确认门（intervene + `confirm_plan` arg）
3. 新增 `consent` 权限模式（ask/auto），消除 agent 定义中无通道的"询问用户"
4. phase 间前置产物 fail-fast 检查（防 LLM 幻觉完成）
5. agent 返回契约精简：仅 validate 保留程序消费的 `payload.verdict`，其余 phase 改自然语言返回
6. 图表生成/验证必选化，移除 generate/visual-validate 模式门控；reader targets 增加 id，validate 检查项 Target ID 追溯
7. quay skill 纳入 pixi 安装任务（原先依赖全局回退，换机即崩）
8. benchmark adapter 兼容无人值守（confirm_plan=false、consent=auto）
9. workflow 确定性 smoke 测试

## 验证

- `pytest tests/` 全绿（MR 门禁）
- loopflow 0.25.1 源码直接 `load_loop` + `check_skills` + schema 校验

## 关联

- loopflow 侧框架级候选：BL-042（跨 agent 文件依赖）、BL-043（phase 级重做）、BL-044（CLI intervene 应答）、BL-045（waiting_input 无人值守策略）、BL-046（agent 侧 waiting_input 协议）、BL-047（单 agent 运行入口）
- 本项目后续候选：BL-001（eval harness `--only-phase` 断裂）、BL-002（.skills 死代码）、BL-003（resume_from）
