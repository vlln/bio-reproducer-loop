# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- loop 适配 loopflow 0.25.1：`loop.md` 声明 phases/args/failure_threshold；workflow 为每个 agent 调用加 label；Reader 后新增人工确认门（`confirm_plan`，无人值守可关闭）；新增 `consent` 权限模式（ask/auto）；phase 间前置产物 fail-fast 检查
- workflow 确定性 smoke 测试（`tests/unit/test_loop_workflow.py`，fake agent 无 LLM 依赖）
- workflow.py 新增模块级 `PHASES` 注册表：全部 phase agent 调用（prompt/agent_def/label/goal/goal_max_iterations）单一事实来源，`run()` 与 eval harness 共用，杜绝 prompt 双处维护漂移
- **部分复现范围入口**：`loop.md` 新增可选 arg `scope`（空=全论文；非空=只复现指定 figure/目标），贯通 Reader（Reproduction Target 表只列范围内目标）→ Data/Run（只执行范围内）→ Validate（只验证范围内、明示 scored scope）→ Package；benchmark metadata 可选 `scope` 字段透传（BL-006，paper-01 试跑暴露的缺口）
- **provision 镜像复用与技能纪律**：provision.md 新增内容无关规则（本地镜像复用优先、容器查找走 biocontainers/quay TRS API、拉取走 image-mirror-skill/mip、Dockerfile 增量构建禁反复全量重建），模板新增 Image & Reuse Decisions 决策节；_base.md 新增工具与技能纪律（BL-007）

### Changed
- agent 返回契约精简：仅 validate 保留程序消费的 `payload.verdict` schema，其余 phase 删除 output schema 改为自然语言返回；移除未消费的 missing[]/decisions[]/status 映射
- 图表生成与验证改为必选，移除 generate/visual-validate 全局模式门控（agents 与 .skills 母本对齐）
- reader targets 增加稳定 `id`，validate 检查项通过 Target ID 追溯到复现目标
- provision 的 quay skill 纳入 pixi 安装任务，不再依赖全局 skill 回退
- eval harness 迁移到 loopflow 0.26.0 单 agent 运行入口：`run_phase` 由 `--only-phase`（0.24.0 已删除）改为 `--agent <agent_def> --prompt <prompt> --work-dir <output_dir> --param ...`，prompt/agent_def 从 `PHASES` 注册表读取（BL-001 闭环）
- benchmark adapter 以 `--work-dir /output` 对齐"agent 产物写当前工作目录"的新契约（loop 已移除 `output_dir`），`--args` 删除失效的 `output_dir` 键，产物回到声明的 repro-data

### Removed
- workflow.py 中已失效的模块级 `meta` dict（loopflow 0.25.1 不再读取）

### Fixed
- 修复 benchmark adapter 在 Docker 无人值守环境下被 intervene 确认门卡死的问题（adapter 传 `confirm_plan=false`、`consent=auto`）
- 修复 system artifact launcher 三处缺陷（Plan 013 正式 smoke 暴露，先于唯一 formal run 阻断）：skills 挂载改到 `~/.loopflow/skills`（原嵌套挂载进只读 loop 目录导致 docker mountpoint 创建失败）、runtime 容器以非 root 用户运行（Claude Code 拒绝 root 下 `--dangerously-skip-permissions`）、预创建并开放 HOME 目录链（docker 以 root 创建的 0755 目录阻断非 root 写入）
- 修复 worker cloud-init 未写 /etc/hosts hostname 条目导致的 `sudo: unable to resolve host bio-reproducer-worker` 警告（build-worker.sh bootcmd 追加 127.0.1.1 条目）

### Changed
- 将确定性软件测试、真实 LLM 内部评测和公开 benchmark 拆分为三个域
- Benchmark 改为 input、submission、private oracle 三方协议，最终评分由独立 evaluator 生成
- 废弃多用途 golden fixture，改用 oracle、fixture、exemplar 和 baseline 四类资产
- 支持从既有 `repro-data` 补建 submission，并保留 legacy 自评用于校准
- 修正 bench-004 的跨脑区对比 oracle；使用独立 evaluator 重评 bench-004 至 bench-006
- 内部 eval 改为 capability case + execution profile，移除多用途 exemplar 和硬编码重复次数
- 清理 protocol v1 entry 残留，拆分科学 claims 与评分 rubric
- 使用独立 evaluator 完成既有 artifacts 的迁移期离线重评
- 完成原 bench-003 的五次远端首跑；结果保留为开发期观测，不建立发布级 baseline
- baseline 改为 release-gated：entry、oracle 与协议冻结前不追踪历史分数
- 退回 DESIGN，提出 L3/L4/L5 分层 InputBundle、runner-only bundle lock 和 provenance 契约
- 完成首批六个 entry 的本地材料审计；原 bench-003 标记为需要重建的假 L4 输入
- 冻结 runner-only bundle lock 契约，实现 schema、validator、staging gate 和 bench-001 pilot
- 完成五个构造 L3 entry 的 bundle 迁移，清理无 provenance PDF 与 bench-006 隐藏重复数据
- 从 PLOS/PMC、GEO、ENA 和 Taffeta 原始材料重建真实论文 entry，重编号为 bench-100，修正 DESeq2/airway 方法误归因并通过 L4 bundle gate
- 划分 entry ID 命名空间：001-099 用于构造论文，100-999 用于真实论文，并由 bundle validator 强制校验
- 完成六个 entry 的人工 fidelity review；将宿主机强隔离移交 Plan 005，将 L4 可执行环境冻结保留在 Plan 002
- 完成 12 个 component 与 2 个 handoff 的真实 LLM smoke，并修复标量断言、blocked 文本误判与 Package phase-only 恢复
- 将被测系统迁入 Docker sandbox，仅挂载只读 InputBundle 与两个可写运行目录；新增 offline/discovery/tool-runtime profile、资源限制、env allowlist、timeout 强制清理和 CI escape probe
- 冻结 paper 与 entry 身份分离、正交任务 taxonomy，以及“manifest 独立声明、内容寻址去重、Curator 物化”的同论文多任务资源复用原则
- 将可发布 benchmark 的唯一正式边界改为 QEMU/KVM disposable VM；Pixi/OCI 保持 guest 内实现细节，Docker sandbox 降为 validation-only backend
- 实现 QEMU/KVM disposable worker、formal ExecutionEnvelope、release-check、最小 worker image 配方与 success/timeout 真实 VM smoke；Docker 运行改为显式 validation backend
- 构建可校验的 opaque bio-reproducer system artifact，固定 loopflow、Pixi runtime、loop source 与 skills provenance，并由 `/system/run-system` 接入 disposable VM
- 强化 worker provisioning 完成条件并修复 release gate 的 JSON 字符串比较；唯一 bench-001 formal smoke 如实保留为 blocked，不建立 baseline

## [0.1.0] — 2026-07-19

### Added
- Benchmark 与测试体系设计（L1-L5）
- devloop 文档体系接入
- 6 个初始 benchmark entries（当时编号 bench-001 ~ bench-006）
- Benchmark runner CLI + engine adapter
- L1/L2 测试骨架（7 个 Phase 单元测试 + 2 个集成测试）
- CI 静态检查（YAML、frontmatter、JSON Schema）
