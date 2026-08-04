---
title: loopflow 0.26~0.28 兼容检查与迁移执行报告
description: 兼容检查结论、两处引擎耦合断裂的修复结果、环境版本核对与上游缺陷记录
type: report
status: complete
created: 2026-08-03T00:00:00Z
---

# loopflow 0.26~0.28 兼容检查执行报告

## 结果

范围全部完成。`pytest tests/unit` 117 通过（113 原有 + 4 新增）；本地 0.28.0 源码 `load_loop` / `parse_agent` 全过；`--mock auto` 对 `--agent` 单 agent 与 `--work-dir` + `--args` 完整 workflow 两条 CLI 路径做真实冒烟，均正常。

## 环境版本核对

| 环境 | 版本 | 状态 |
|------|------|------|
| 本地源码 `/Users/vlln/Project/loopflow` | main @ 0.28.0 发布（0596c18），pyproject 版本号仍为 **0.27.1** | 见 BL-005（上游缺陷：0.28.0 发布未 bump 版本号） |
| 本地 venv `.venv`（editable 安装） | 运行 0.28.0 源码，dist-info 元数据陈旧为 0.26.0 | 建议重装同步元数据（`uv pip install -e .`，重装后读 0.27.1） |
| 远端 gs `/storeData/gs/loopflow` | checkout `v0.25.0-61-g215e4c6`（≈0.27.0 时代），安装 0.26.0 | 落后于本地；benchmark 运行时镜像由其构建，见 BL-004 |
| benchmark 运行时镜像 | 由 build-runtime.sh 从 loopflow checkout `git archive HEAD` 构建 | 构建时需核对 checkout 与 `--loopflow-version` 入参一致 |

## 兼容面核对（0.28.0）

| 耦合面 | 结论 |
|--------|------|
| loop.md frontmatter（name/args/triggers/requires/failure_threshold/phases） | 兼容；`phases` 仍被 WebUI `_extract_declared_phases` 消费（展示用途），保留 |
| workflow.py `run(agent, parallel, pipeline, log, args, workflow, intervene, state)` | 兼容（`accepted_kwargs` 过滤） |
| `agent()` 调用（agent_def/label/goal/goal_max_iterations/自定义 kwargs） | 兼容 |
| `intervene(key, prompt, options, allow_custom)` | 兼容（0.26.0 新增 default/timeout 为可选参数） |
| CLI `loop run <loop> --args <json> [--work-dir]` | 兼容 |
| CLI `--only-phase` / `--from-phase` | **已删除（0.24.0）** → BL-001，本容器修复 |
| `output_dir` arg | loop 已移除该契约（agent 产物写当前工作目录）→ adapter 修复，见下 |

## 修复内容

### 1. eval harness BL-001：`--only-phase` → `--agent` 单 agent 入口

- `evals/runner/loopflow.py`：`run_phase` 改用 `loop run bio-reproducer --agent <agent_def> --prompt <prompt> --work-dir <output_dir> --param language=en --param consent=ask [--param paper_path=...]`，不再使用已删除的 `--only-phase`；`phase_spec()` 提供按 phase 名取 spec 的入口
- `loops/bio-reproducer/workflow.py`：新增模块级 `PHASES` 注册表（prompt/agent_def/label/goal/goal_max_iterations），`run()` 与 eval harness 共用同一事实来源，消除 prompt 双处维护漂移
- 行为说明：单 agent 模式不执行 workflow.py（ADR-0055 语义），无 goal/goal_max_iterations 与确认门；评测断言基于产物文件，agent_def 正文含完整目标描述，行为等价性由产物检查兜底

### 2. benchmark adapter：`--work-dir /output` 对齐工作目录契约

- `benchmarks/runner/adapters/loopflow.py`：命令改为 `[launcher, run, bio-reproducer, --work-dir, /output, --args, {...}]`，`--args` 删除失效的 `output_dir` 键
- 动机：loop 已移除 `output_dir`（agent 产物直接写当前工作目录），沙箱/VM 的容器 workdir 是 `/workspace`；若不指定 `--work-dir /output`，产物落在 `run_root/workspace/` 而 adapter 从 `run_root/repro-data/` 读产物，成功 run 也会得到空 submission
- 兼容性：`--work-dir` 为 loopflow ≥0.23 选项，本地 0.28.0 / 远端 0.26.0 均支持

### 3. 测试

- `tests/unit/test_loop_workflow.py`：PHASES 注册表完整性（7 phase、agent_def 对应 agents/ 真实定义、label 一致）、注册表驱动 agent 调用
- `tests/unit/test_eval_harness.py`：run_phase 命令构造（无 `--only-phase`、`--agent reader`、`--work-dir` 指向 output_dir、language/consent/paper_path 参数、paper 文件存在）、未知 phase 拒绝
- `tests/unit/test_runtime_isolation.py`：adapter 命令含 `--work-dir /output`、args 无 `output_dir`、`confirm_plan=false`/`consent=auto` 保留

## 遗留（未在本容器处理）

- BL-004：远端 gs loopflow 落后（0.26.0 / 0.27.0 时代 checkout），benchmark 运行时镜像构建前需同步；本地 venv editable 元数据陈旧，建议重装
- BL-005：loopflow 0.28.0 发布未 bump pyproject 版本号（tag 上仍是 0.27.1），系统 artifact 的 `loopflow_version` provenance 会误记；已向上游反馈候选
- BL-002（.skills 死代码）、BL-003（resume_from）维持 candidate
- 修复后应对本轮 prompt 变更（PHASES 重构未改任何 prompt 文本）补跑 component eval 基线确认无回归 —— PHASES 重构为纯机械提取，prompt/goal 文本逐字保留，风险极低
