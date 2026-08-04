# Backlog

工程需求池。DESIGN 阶段的迭代候选只能从这里拉取；选定后状态改为 `planned` 并记录关联迭代。

状态值：`candidate`（待评估）→ `planned`（已排入迭代）→ `done`（已闭环）/ `dropped`（放弃，需注明原因）

| 编号 | 标题 | 描述 | 来源 | 状态 | 关联迭代 |
|------|------|------|------|------|---------|
| BL-001 | eval harness 修复 `--only-phase` 断裂 | loopflow 0.24.0（ADR-0052）删除 `--only-phase`/`--from-phase`，`evals/runner/loopflow.py` 原使用该选项，component/handoff case 全部无法运行。已修复：loopflow 0.26.0 落地 BL-047 单 agent 运行入口（`--agent` + `--prompt`），`run_phase` 迁移到该入口；prompt/agent_def 从 workflow.py `PHASES` 注册表单一来源读取 | loopflow 0.25.1 迁移时发现 2026-07-28 | done | 0015-loopflow-028-migration |
| BL-002 | 删除 `.skills/bio-reproducer/` 死代码 | 该目录（SKILL.md + 7 个 references，1363 行）不被任何 agent 的 `skills:` 声明，loopflow 永不注入；它是 agents/*.md 的历史母本，曾是多起 drift 矛盾（图表必须性、schema enum、输出清单）的根源。删除前确认 agents/*.md 已完全自包含 | loopflow 0.25.1 迁移分析 2026-07-28 | candidate | — |
| BL-003 | resume_from 阶段级重跑入口 | Validate 发现问题后需重做上游阶段时，目前只能整个新 run。等 loopflow BL-043（phase 级重做/replay 缓存作废）方向明确后，决定用引擎原生机制还是 workflow 参数实现 | loopflow 0.25.1 迁移讨论 2026-07-28 | candidate | — |
| BL-004 | 远端/本地 loopflow 版本对齐 | 本地源码已 0.28.0，本地 venv editable 元数据陈旧（0.26.0）；远端 gs `/storeData/gs/loopflow` checkout `v0.25.0-61-g215e4c6`（≈0.27.0 时代）、安装 0.26.0。已处理：本地 venv `uv pip install -e .` 重装至 0.27.1，远端 checkout 同步至 0.28.0（0596c18）并重装 0.27.1。剩余：benchmark 运行时镜像由 build-runtime.sh 从 checkout 构建，构建前须核对 `--loopflow-version` 入参 | 0013 兼容检查 2026-08-03 | done | 0015-loopflow-028-migration |
| BL-005 | loopflow 0.28.0 版本号未 bump（上游缺陷） | loopflow `v0.28.0` tag 上 pyproject.toml 版本号仍是 0.27.1（0.25.0 起版本号单源化自 pyproject），系统 artifact 的 `loopflow_version` provenance 会误记 0.27.1。已向 loopflow 侧记录；在本项目侧构建运行时镜像时以 `--loopflow-version` 显式传 0.28.0（或等上游补丁） | 0013 兼容检查 2026-08-03 | candidate | — |
| BL-006 | 部分复现范围入口（scope） | paper-01 试跑暴露：论文只需复现部分 figure，但 bio-reproducer 无范围声明入口，reader/validate/data/run 全量执行。已实现：loop.md 新增可选 arg `scope`（空=全论文），贯通 Reader→Data→Run→Validate→Package，范围外标注 out-of-scope 不执行/不评分；benchmark adapter 经 metadata `scope` 透传（物化 ADR-0008 的 entry scored scope）。遗留：补跑 scope 语义的 component eval 基线 | paper-01 试跑 2026-08-04 | done | 0016-partial-reproduction-scope |
| BL-007 | worker /etc/hosts hostname 条目 | 正式 smoke 中 guest 反复出现 `sudo: unable to resolve host bio-reproducer-worker` 警告（无害但噪音）。已修复：build-worker.sh cloud-init bootcmd 追加 `127.0.1.1 bio-reproducer-worker` 到 /etc/hosts（fix/worker-hosts-entry → 5820bd7）。worker 已重建并探测验证（/etc/hosts 条目生效、docker 正常），存储于远端 `/storeData/gs/bio-reproducer-worker/worker.qcow2`（sha256 `e18b50a8…`） | 0013 formal smoke 2026-08-04 | done | — |
| BL-008 | 远端网络限制与镜像策略 | gs 网络对 Ubuntu cloud images 与 Docker Hub 直连被墙（SSL EOF/connection reset）。已建立策略：worker 构建用 `BIO_REPRODUCER_UBUNTU_CLOUD_URL` 指向清华镜像（sha256 固定为权威）；provision 阶段用 apt/BiocManager 本地源（r-bioc-* 包 + cloud.r-project.org）替代 Docker Hub 拉取。遗留：正式 run 继续沿用该策略，或评估 registry 镜像加速（image-mirror-skill） | 0013 formal smoke 2026-08-04 | candidate | — |
| BL-007 | provision 镜像复用与技能纪律 | paper-01 scope 运行暴露 Provision 4h44m 根因：无视本地已有镜像从零重建、有 biocontainers/quay/image-mirror 技能不用、Dockerfile 反复全量重建（2GB 层重复下载）、mip 缺失。已修复（内容无关 prompt 规则）：provision.md 新增镜像复用/技能强制使用/镜像构建纪律三节 + Image & Reuse Decisions 模板节；_base.md 新增工具与技能纪律；新增 provision-image-reuse 行为审计 eval case；远端装 mip、建 .pixi、清空技能目录 | paper-01 scope 运行 2026-08-04 | done | 0018-provision-image-reuse |
