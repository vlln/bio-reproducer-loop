---
title: loopflow 0.26~0.28 兼容检查与迁移
description: loopflow 更新至 0.28.0 后检查本项目的引擎耦合面：eval harness 单 phase 评测迁移到 --agent 入口，benchmark adapter 工作目录对齐，环境版本核对
type: plan
status: done
created: 2026-08-03T00:00:00Z
---

# loopflow 0.26~0.28 兼容检查与迁移

## 背景

项目在 0010 容器迁移至 loopflow 0.25.1 后，loopflow 又发布了 0.26.0（单 agent 运行入口 `--agent`、`intervene` default/timeout、`--unattended`）、0.27.0（append-prompt、waiting_input 控制协议、declared args 契约）、0.27.1（并行事件 call_id 修复、web 静态资源修复）、0.28.0（本地型发布修订、demo loop 黑盒）。本地 loopflow 源码已更新至 0.28.0（main），需要对项目所有引擎耦合面做一次兼容检查并修复暴露的断裂。

## 范围

1. 核对各环境 loopflow 版本（本地源码、本地 venv、远端 gs、benchmark 运行时镜像）
2. 核对项目引擎耦合面与 0.28.0 的兼容性：loop.md 解析、workflow.py 签名、agent()/intervene() 调用、CLI 选项
3. 修复 eval harness BL-001：`--only-phase`（0.24.0 已删除）→ loopflow 0.26.0 `--agent` 单 agent 运行入口（BL-047 落地），prompt/agent_def 从 workflow PHASES 注册表单一来源
4. 修复 benchmark adapter：loop 已移除 `output_dir`（agent 产物写当前工作目录），adapter 改用 `--work-dir /output` 使产物落在声明的 repro-data，删除失效的 `output_dir` arg
5. 文档与测试同步

## 验证

- `pytest tests/unit` 全绿（含新增：PHASES 注册表一致性、eval harness 单 agent 命令、adapter `--work-dir /output` 契约）
- 本地 0.28.0 源码 `load_loop` + `parse_agent` 全过
- `--mock auto` 真实 CLI 冒烟：`--agent` 单 agent 与 `--work-dir` + `--args` 完整 workflow 两条路径

## 关联

- 本项目 BL-001（eval harness `--only-phase` 断裂）→ 本容器闭环
- 本项目 BL-004（远端/venv loopflow 版本对齐）、BL-005（loopflow 0.28.0 版本号未 bump 的上游缺陷）
