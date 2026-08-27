# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed (Plan 0025 — scored_scope 删除与 ClaroAI claims 模式)

- **删除 `scored_scope` 机制**：`metadata.scored_scope`（bench-100/200~234 全部移除）、
  adapter 透传行、validator CC-002 强制值、verify.py 交叉锚点一并删除。该字段是评分
  维度代码，曾作为系统侧 scope 参数泄漏评估设计给被测系统并被误读（bench-221 误读
  为"膳食模式 D1/D3"），导致越界重活与慢运行。
- **ClaroAI entry 恢复 claims 模式**：converter v0.2.0 从 `scores.json` D5 evidence
  转录论文数值声明（`pub=/repr=`、`reproduced=,published=`、单行 `HR =`、`match
  paper` 计数；35 篇共转录 21 条 + bench-223 AUROC 阈值 claim 手工补），rubric 用
  `check_claim` 确定性数值 comparator（relative/absolute 容差 + gte/lte 阈值）评分；
  D1–D3 数据/代码可用性为同 rubric 辅助 checks。entry 任务语义由
  `reproduction_target` + 自然语言 `task` 表达。
- **系统侧任务说明**：adapter 改读 `metadata.task` 翻译为 loop `scope` 参数；
  validator CC-002 rev. 禁止任何残留评分维度代码（INVALID_BUNDLE）。
- **评估工具**：`evaluate_run.py` 支持 `--claims-evidence` 与 `06_validate/report.md`
  自动装载（role=validate_report）。
- **6 篇校准 run 离线重评**（claims 模式）：bench-220 REPRODUCED 100、bench-221 65、
  bench-203 PARTIAL 30、bench-200/223/229 FAILED —— 修正审计模式高估（bench-200 旧
  REPRODUCED 90 → FAILED 0，其 run 未复现 Fig4A DEG 声明）；与作者 D5 校准对照扩展
  到 D5 维度（bench-200/203/223 作者 D5=2 而系统未复现 claims）。
- 测试：converter/validator/adapter 测试更新 + 新增回归（维度代码禁入系统侧、
  check_claim 容差、scored_scope 拒绝）；全量 141 passed / 4 skipped；42 entry 全过
  bundle gate。

### Changed (Plan 0026-02 — Data phase 产物契约改标准格式文件，ADR-0011 落地)

- **04_data 契约**：`agents/data.md` 状态词表拆分 `completed / partial / unavailable /
  not_attempted`（按终态信号判定，不按尝试次数；传输层失败 ≠ 外部不可得）；每数据资源
  一份获取日志（阻塞也落）；已下载文件汇总 `sha256sums.txt`；下载统一 `curl -C -`
  续传（镜像内无 wget/aria2c）；manifest 降级为从证据文件渲染的散文摘要。
- **workflow 检查升级**：新增 `artifact_checks.py`（终态类别判定器 + 04_data 证据收集）与
  `_require_parsable`；Data 阶段后 fail-fast「存在 + 可被标准工具解析」，抓「声称完成但
  无任何标准格式证据」（BL-014 部分）。
- **死技能声明移除**（BL-019 闭环）：`agents/reader.md` 删除 `paperutils`/`mineru-api`
  声明，标识符解析改直调 Crossref / EuropePMC；PDF 转换不再绑定具体工具；系统 artifact
  skills.lock 收缩 7 → 5，`.skills/` 死目录删除。
  **修订（2026-08-27）**：人类提供真实来源（paperutils = GitHub vlln/paperutils，
  mineru = `http://172.16.218.40:8001/`），按 HANDOFF 约定**恢复**两个技能——reader.md
  声明恢复（技能优先 + 直调 API 兜底）、skills.lock 恢复 7 技能（commit 与源仓库 HEAD
  一致）；两端 `~/.agents/skills/` 同步为源仓库版本（paperutils 的 `requires.bins` 为
  旧版过时声明，源版本无）；`MINERU_API_URL` 宿主 export + run-entry.sh 透传，
  harness-probe.sh 同步补透传；实测 paperutils 解析 DOI 成功、mineru `/health` healthy。
- 测试：新增 `tests/contract/test_data_phase_contract.py`（18 例，正反例用已归档 run
  真实产物 fixture `tests/fixtures/contract/`：bench-234 传输失败→not_attempted、
  中途失败续传完成→completed、bench-217 无证据）；全量 166 passed / 4 skipped。

### Changed (Plan 0026-03 — Validate 内部化 + 动态路由 + goal 派生，BL-016/BL-022)

- **Validate 改为内部自反馈路由**：不产出对外 verdict（内部自评仅供 Package 门控与
  路由参考）；新增 `06_validate/routing.jsonl` 追加式路由输出（键名白名单
  ts/target/decision/route_to/reason，FC-003 lint）；触发条件用通用信号（实际执行与
  声明不一致且未声明即路由，如 `*_patched.py`）；report/metrics 降级为内部草稿。
- **动态回环**：workflow 按 routing.jsonl 重跑 Data/Provision/Run/Reader 及下游，
  预算 `routing_budget` 只来自调用方参数（默认 0 = 线性，FC-007 无系统内硬编码）；
  Reader 回环不重触发 confirm 门。
- **goal 从 plan.md 派生**（BL-016）：Data/Run goal 由 Reproduction Target /
  Data Requirements / Analysis Steps 段落生成（只搬运不判断），删 RNA-seq 硬编码；
  无段落回退注册表默认 goal。
- **Run 结果契约**：`05_run/results/`（CSV/TSV）+ `answers.csv`（target_id,value,unit,
  source_file 表头精确白名单）+ `reports/commands.log`（命令+退出码）；修改作者代码
  必须声明（防 BL-022 类未声明缩减）；workflow 加 `check_run_phase` fail-fast。
- 测试：+24 用例（goal 派生、回环 6 态、routing/answers lint、check_run_phase 四态、
  prompt 契约断言）；全量 190 passed / 4 skipped。

### Changed (Plan 0026-04 — 证据面切换：评分只读真实产物，BL-023/BL-015)

- **外部评分不再读系统自评**（FC-004/FC-006）：converter 生成 rubric 时禁用
  validate_report（C 类 claim 证据 → `05_run/answers.csv`，A1 → 04_data sha256sums+
  日志终态，A2 → 03_provision digests）；adapter 删除 report.md 散文解析回退，
  metrics.json 仅作 claimed_verdict 观测；`06_validate/` 整目录移出证据面。
- **公开问题清单**（ADR §4.1）：converter 生成 `input/questions.yaml`（target_id+
  question+unit，无期望值）；claims.yaml 加 `target_id`（metric slug）；系统按
  target_id 填 answers.csv。
- **answers 强制交叉核对**（FC-005）：值须能在自述 source_file 中定位（容差由书写
  精度导出，无魔数），失败 → NO-EVIDENCE（不计分不扣分，非判错）；全部 check 无
  证据 → BLOCKED。evaluator 三态落地。
- **provision 契约推广**：`03_provision/digests.txt`（docker images --digests 原始
  输出）+ `check_provision_phase` + workflow fail-fast（A2 证据）。
- **verify.py 退役散文解析**：VERIFY_TEMPLATE 重写（302 → 约 180 行，无
  `_parse_data_manifest` 等）；35 个 claroai entry 迁移（backfill 幂等脚本，含手写 entry 保护）；
  `evaluate_run.py` 只接受新契约 run（旧 pilot 不可重评）。
- **routing_budget 透传**（FC-007）：adapter 从执行器 deadline 派生（5h→4、1h→0）。
- 测试：新增 `tests/contract/test_evidence_switch.py`（8 例：交叉核对四态、A1/A2 推导、
  evaluator 三态、provision 契约）；全量 199 passed / 4 skipped；42 entry bundle gate 全过。

- 受影响文档退回 proposed（发布就绪审计要求），promote 后回 active。

### Changed (Plan 0026-06 — 交付包自包含，BL-025/FC-008)

- **自包含纪律**：交付包只要求 Docker，Java/Nextflow/R 全在镜像内（镜像清单 =
  `03_provision/digests.txt`）；run.sh check 不再检查宿主 java/nextflow/R；
  run/validate 用 `docker run` 执行分析镜像（0/6 干净容器失败根因消除）。
- **FC-008 执行证明**：Package 必须执行 `bash run.sh check` 并落
  `07_package/check.log`（退出码 0）；workflow 出口 `check_package_phase`
  fail-fast（无执行证明不得声明 completed）。
- 测试：check_package_phase 五态 + workflow 2 用例 + prompt 断言；
  全量 203 passed / 4 skipped。
- **容器 0026 全部 6 单元完成**（Report 01-06）；FC-001~FC-008 检出手段全部落地；
  完成判据 1/2 ✅、3 待 run-entry.sh 端到端首跑。

### Docs (Plan 0026-05 — 下游文档同步，待人类 promote)

- Interface 0001：InputBundle 加 questions.yaml；BundleResource 扩展（questions/
  benchmark authority）；新增「被测系统标准格式产物」节；NO-EVIDENCE 语义。
- Interface 0002：证据面切换修订（claims target_id、公开问题清单 §2.1、rubric 证据
  角色 answers/data_evidence/environment、submission 约定重写）。
- Spec 001 / AC-0002 / AC-0005：claims 模式节、routing_budget 透传、questions 与
  交叉核对场景。ADR-0011 FC-003 修订为键名白名单（routing 含 reason 以 §3 为准）。
- 受影响文档退回 proposed（发布就绪审计要求），promote 后回 active。

### Changed (Plan 0026-07 — run-entry.sh 首跑 + BL-013 挂起根因修复)

- **run-entry.sh 端到端首跑**（bench-220，2026-08-27）：跑通 Reader→Bootstrap→
  Provision，验证 dind 新基建、三个 harness 修复、技能补齐、digests.txt 契约；
  终止于 Provision 收尾的 agent 挂起，产物归档（Report 07）。
- **BL-013 根因确认（实测）**：claude 2.1.126 对非官方端点（ANTHROPIC_BASE_URL）
  的 SSE 流式空闲看门狗默认关闭（官方 v2.1.196 起才对所有 provider 默认开启，
  v2.1.210 起支持 `CLAUDE_STREAM_IDLE_TIMEOUT_MS`）；`API_TIMEOUT_MS` 实测对流式
  无效。挂起点 = thinking 后 SSE 静默中断（「Fixed a hang where the assistant
  could finish thinking but show no output」官方条目精确对应）。
- **修复**：(a) runtime 镜像内 claude 2.1.126→2.1.247，commit
  `bio-reproducer-runtime:system-idlefix-cc247`，run-entry.sh 默认镜像改指；
  (b) settings.json env 加 `CLAUDE_ENABLE_STREAM_WATCHDOG=1` +
  `CLAUDE_STREAM_IDLE_TIMEOUT_MS=300000`；(c) loopflow `CliTransport` 空闲看门狗
  子进程感知化（长命令不误杀、无子进程才 kill，默认 7200s，loopflow develop
  `4b9bdf7`，446 测试全绿）。backlog 新增 BL-027。
- **重跑完成（run2）**：BL-013 修复后 bench-220 7 阶段一次跑通（REPRODUCED 98/100
  自评），归档 `bench-220-0026-run2/`；Data/Run/Validate/Package 新契约全部真实
  落盘（sha256sums/answers.csv/routing.jsonl/check.log），`verify-0026-run.sh`
  19 项契约检查全过。
- **修复 answers target_id 与公开问题清单脱节**（run2 验收实证）：answers 用
  plan.md T 编号 → 外部评分 C1-C3 全 NO-EVIDENCE。修 `agents/run.md`（target_id
  必须用 `input/questions.yaml` 键）、`agents/reader.md`（Target 表标注 questions
  target_id）、`artifact_checks.py`（`check_run_phase` 键对齐 fail-fast）+ 契约
  测试 +3（206 passed / 4 skipped）。

### Docs
- ADR-0010 修订块、Interface 0002 v2（claims 评分协议）、Spec 0001（接入段/BR-018/
  术语）、AC-0005、Plan 0025（plan+report+README）。

## [0.2.0] — 2026-08-04

### Added
- loop 适配 loopflow 0.25.1：`loop.md` 声明 phases/args/failure_threshold；workflow 为每个 agent 调用加 label；Reader 后新增人工确认门（`confirm_plan`，无人值守可关闭）；新增 `consent` 权限模式（ask/auto）；phase 间前置产物 fail-fast 检查
- workflow 确定性 smoke 测试（`tests/unit/test_loop_workflow.py`，fake agent 无 LLM 依赖）
- workflow.py 新增模块级 `PHASES` 注册表：全部 phase agent 调用（prompt/agent_def/label/goal/goal_max_iterations）单一事实来源，`run()` 与 eval harness 共用，杜绝 prompt 双处维护漂移
- **部分复现范围入口**：`loop.md` 新增可选 arg `scope`（空=全论文；非空=只复现指定 figure/目标），贯通 Reader（Reproduction Target 表只列范围内目标）→ Data/Run（只执行范围内）→ Validate（只验证范围内、明示 scored scope）→ Package；benchmark metadata 可选 `scope` 字段透传（BL-006，paper-01 试跑暴露的缺口）
- **provision 镜像复用与技能纪律**：provision.md 新增内容无关规则（本地镜像复用优先、容器查找走 biocontainers/quay TRS API、拉取走 image-mirror-skill/mip、Dockerfile 增量构建禁反复全量重建），模板新增 Image & Reuse Decisions 决策节；_base.md 新增工具与技能纪律（BL-009）
- **正式路径首次全链路跑通**（0013）：`bench-001` 在 QEMU/KVM disposable VM 中全 7 阶段真实执行，claimed_verdict REPRODUCED（93/100），release-check FORMAL，teardown 完整
- 新增配对 L3 entry `bench-003`（0014，配对 RNA-seq 差异表达）
- scope 语义 component eval 基线（0017：reader-scoped-targets）与 provision 镜像决策行为审计 case（0018：provision-image-reuse）

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

## [0.1.0] — 2026-07-19

### Added
- Benchmark 与测试体系设计（L1-L5）
- devloop 文档体系接入
- 6 个初始 benchmark entries（当时编号 bench-001 ~ bench-006）
- Benchmark runner CLI + engine adapter
- L1/L2 测试骨架（7 个 Phase 单元测试 + 2 个集成测试）
- CI 静态检查（YAML、frontmatter、JSON Schema）

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
