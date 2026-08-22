# Backlog

工程需求池。DESIGN 阶段的迭代候选只能从这里拉取；选定后状态改为 `planned` 并记录关联迭代。

状态值：`candidate`（待评估）→ `planned`（已排入迭代）→ `done`（已闭环）/ `dropped`（放弃，需注明原因）

| 编号 | 标题 | 描述 | 来源 | 状态 | 关联迭代 |
|------|------|------|------|------|---------|
| BL-001 | eval harness 修复 `--only-phase` 断裂 | loopflow 0.24.0（ADR-0052）删除 `--only-phase`/`--from-phase`，`evals/runner/loopflow.py` 原使用该选项，component/handoff case 全部无法运行。已修复：loopflow 0.26.0 落地 BL-047 单 agent 运行入口（`--agent` + `--prompt`），`run_phase` 迁移到该入口；prompt/agent_def 从 workflow.py `PHASES` 注册表单一来源读取 | loopflow 0.25.1 迁移时发现 2026-07-28 | done | 0015-loopflow-028-migration |
| BL-002 | 删除 `.skills/bio-reproducer/` 死代码 | 该目录（SKILL.md + 7 个 references，1363 行）不被任何 agent 的 `skills:` 声明，loopflow 永不注入；它是 agents/*.md 的历史母本，曾是多起 drift 矛盾（图表必须性、schema enum、输出清单）的根源。删除前确认 agents/*.md 已完全自包含 | loopflow 0.25.1 迁移分析 2026-07-28 | candidate | — |
| BL-003 | resume_from 阶段级重跑入口 | Validate 发现问题后需重做上游阶段时，目前只能整个新 run。等 loopflow BL-043（phase 级重做/replay 缓存作废）方向明确后，决定用引擎原生机制还是 workflow 参数实现 | loopflow 0.25.1 迁移讨论 2026-07-28 | candidate | — |
| BL-004 | 远端/本地 loopflow 版本对齐 | 本地源码已 0.28.0，本地 venv editable 元数据陈旧（0.26.0）；远端 gs `/storeData/gs/loopflow` checkout `v0.25.0-61-g215e4c6`（≈0.27.0 时代）、安装 0.26.0。已处理：本地 venv `uv pip install -e .` 重装至 0.27.1，远端 checkout 同步至 0.28.0（0596c18）并重装 0.27.1。剩余：benchmark 运行时镜像由 build-runtime.sh 从 loopflow checkout 构建（脚本只接受 `LOOPFLOW_GIT_CHECKOUT` 和 `OUTPUT_OCI_TAR` 两个参数，无 `--loopflow-version`），需确保 checkout 版本与预期一致 | 0013 兼容检查 2026-08-03 | done | 0015-loopflow-028-migration |
| BL-005 | loopflow 0.28.0 版本号未 bump（上游缺陷） | loopflow `v0.28.0` tag 上 pyproject.toml 版本号仍是 0.27.1（0.25.0 起版本号单源化自 pyproject），系统 artifact 的 `loopflow_version` provenance 会误记 0.27.1。已向 loopflow 侧记录；在本项目侧构建运行时镜像时以 `--loopflow-version` 显式传 0.28.0（或等上游补丁） | 0013 兼容检查 2026-08-03 | candidate | — |
| BL-006 | 部分复现范围入口（scope） | paper-01 试跑暴露：论文只需复现部分 figure，但 bio-reproducer 无范围声明入口，reader/validate/data/run 全量执行。已实现：loop.md 新增可选 arg `scope`（空=全论文），贯通 Reader→Data→Run→Validate→Package，范围外标注 out-of-scope 不执行/不评分；benchmark adapter 经 metadata `scope` 透传（物化 ADR-0008 的 entry scored scope）。遗留：补跑 scope 语义的 component eval 基线 | paper-01 试跑 2026-08-04 | done | 0016-partial-reproduction-scope |
| BL-007 | worker /etc/hosts hostname 条目 | 正式 smoke 中 guest 反复出现 `sudo: unable to resolve host bio-reproducer-worker` 警告（无害但噪音）。已修复：build-worker.sh cloud-init bootcmd 追加 `127.0.1.1 bio-reproducer-worker` 到 /etc/hosts（fix/worker-hosts-entry → 5820bd7）。worker 已重建并探测验证（/etc/hosts 条目生效、docker 正常），存储于远端 `/storeData/gs/bio-reproducer-worker/worker.qcow2`（sha256 `e18b50a8…`） | 0013 formal smoke 2026-08-04 | done | — |
| BL-008 | 远端网络限制与镜像策略 | gs 网络对 Ubuntu cloud images 与 Docker Hub 直连被墙（SSL EOF/connection reset）。已建立策略：worker 构建用 `BIO_REPRODUCER_UBUNTU_CLOUD_URL` 指向清华镜像（sha256 固定为权威）；provision 阶段用 image-mirror-skill（mip CLI）/biocontainers/quay TRS API 探测与选择可用镜像源替代 Docker Hub 直连拉取。遗留：正式 run 继续沿用该策略，或评估 registry 镜像加速 | 0013 formal smoke 2026-08-04 | candidate | — |
| BL-009 | provision 镜像复用与技能纪律 | paper-01 scope 运行暴露 Provision 4h44m 根因：无视本地已有镜像从零重建、有 biocontainers/quay/image-mirror 技能不用、Dockerfile 反复全量重建（2GB 层重复下载）、mip 缺失。已修复（内容无关 prompt 规则）：provision.md 新增镜像复用/技能强制使用/镜像构建纪律三节 + Image & Reuse Decisions 模板节；_base.md 新增工具与技能纪律；新增 provision-image-reuse 行为审计 eval case；远端装 mip、建 .pixi、清空技能目录 | paper-01 scope 运行 2026-08-04 | done | 0018-provision-image-reuse |
| BL-010 | README 文档滞后 | README entries 表缺 bench-003 行（0014 新增后未同步）、L3/L4 计数与描述需随 entry 演进维护；建议 entry 变更时同步 README（或改为从 bundle.yaml 生成）。已修复：README 版本号、entries 表（含 bench-003 和 bench-200~234）、L3/L5 计数、项目结构图均已同步至当前状态 | 0014 合并 2026-08-04 | done | — |
| BL-012 | ClaroAI 审计 entry 正式 VM 校准运行 | bench-200~234（35 个 L5 审计 entry）已生成并通过 bundle gate；校准已部分完成：重建 runtime/artifact（docker 模拟 VM 边界跑通 loopflow 全链路），bench-200 完整运行 verdict=BLOCKED（与作者 D2=0/D3=1 结论一致），35 篇批量校准分析转录一致。剩余：其余 entry 的完整校准运行（单篇 ~27h，挂 BL-013 迭代）与正式 VM 边界（qemu 装好后用 disposable-vm） | SYSTEM_TEST 2026-08-05 | done | 0023-claroai-calibration |
| BL-013 | ClaroAI 其余 34 篇 entry 完整校准运行 | bench-200 校准已验证全链路（docker 模拟 VM 边界，~27h/篇）。剩余 34 篇（bench-201~234）完整 loopflow 校准：每篇产出 verdict + 审计产物，对照作者 D1–D3 ground truth。单篇 ~27h → 需并行（远端多 worker 或分批）；建议按作者 D2>0 的 18 篇优先（数据可获取论文的复现路径更可判定）。执行方式：复用 bench-v3.sh + runtime/artifact（已重建），新 run 用时间戳目录避免清理问题。**状态更新（2026-08-07）**：第一批 6 篇（D2=2&D3=2）校准完成，**验证了 bio-reproducer 能端到端跑通 claroai-bench L5 审计 entry（REPRODUCED/BLOCKED/PARTIAL 三种结局）**——当前动机（系统能力验证）已达成。剩余 12 篇属 claroai-bench 可复现性分布评估，非当前动机，挂后续迭代 | 用户指示 2026-08-05 | done | 0024-claroai-calibration-batch |
| BL-014 | 提交协议改结构化 report.json（评分器去正则化） | 现状：`oracle/verify.py` 301 行靠中英关键词表 + 后缀剥离 + token 重叠≥2 解析 agent 写的自然语言 Markdown 表格（证据 `benchmarks/entries/bench-220/oracle/verify.py:20-105`），措辞变化即改分——量具本身不可复现（历史补丁 d487ac8 专为中文列名）。参照 CORE-Bench（arXiv 2409.11363，`siegelz/core-bench`）：input 给出问题清单，agent 写 `report.json`（key=问题/claim_id，value=答案），数值按容差/区间判定，harness 可插拔任意 agent。改造：`input/questions.json`（claim_id + 问题 + 单位 + 类型 + 容差）+ 要求被测系统写 `/output/report.json`，evaluator 只做类型化比较；A1/A2 降为诊断不计分；verify.py 正则退役为 legacy。副作用：现有 35 run 无 report.json，正式数字须重跑（该批降级为 pilot 数据）。**前置于任何正式批次**；同时使 baseline（裸 agent/开源 agent）可比 | 2026-08-22 发布就绪审计 | candidate | — |
| BL-015 | 19/35 ClaroAI entry 无数值 claims，verdict 由 LLM 审计真值驱动 | 逐 entry 统计：bench-202/204/205/207/211/212/213/215/217/218/219/224/226/227/228/230/232/233/234 的 `oracle/claims.yaml` claims 为空，rubric 只剩 A1/A2 各 50 分（证据 `benchmarks/entries/bench-227/oracle/rubric.yaml`），其真值转录自 claroai `scores.json`（另一个 LLM 的审计输出，已知至少两处错误：bench-200 GEO 实际可下载、bench-229 GSE220289 实际有 19 个处理矩阵）。后果：当前「16 REPRODUCED / 13 PARTIAL / 6 FAILED」里 10 个 REPRODUCED 来自零 claims entry，**不构成复现率**。处置（人类已决策 2026-08-22）：逐篇从论文原文手工抽 3-6 条数值 claim（先 pilot 测单篇成本），A1/A2 转诊断；oracle 打 tag 冻结后再跑批 | 2026-08-22 发布就绪审计 | candidate | — |
| BL-016 | workflow 硬编码 RNA-seq goal + 无动态路由 | `loops/bio-reproducer/workflow.py:36-49` 的 Data/Run goal 硬编码「FASTQ 样本、参考基因组、微阵列数据」「完整的 RNA-Seq 分析流水线」，却被原样用于 NHANES 流病（bench-220/221/227）、MRI（203）、胸片（222）等论文；`workflow.py:120-189` 为纯线性 fail-fast，任一 phase 非 complete 即 `return None`，无重试/替代路径/回环（关联 BL-003 resume_from）。修复方向：goal 从 plan.md 派生 + 有限重试与降级路由。**执行纪律**：先出 BL-017 失败分类学再定机制；改动须成对跑（同子集 before/after）以直接产出 ablation 证据，且必须在量具（BL-014/015）冻结之后 | 2026-08-22 发布就绪审计 | candidate | — |
| BL-017 | 35 个已归档 run 的失败分类学（零算力，前置于系统改动） | `/storeData/gs/claroai-calibration/runs/`（35 run，54GB）从未被系统读过死因。产出一张表：每 run × 终止阶段 × 外部阻塞 vs 系统能力（BR-003/004）× 是否降级配置 × 耗时/重试次数 × 关键失败证据行。用途：(a) 决定系统论文的创新轴（环境重建 / 诚实降级归因 / replanning 三选一）；(b) 给 entry 提供经验 difficulty 标注；(c) 给校准短文（Track C）提供失败分布。**唯一永不返工的起点** | 2026-08-22 发布就绪审计 | candidate | — |
| BL-018 | 校准 harness 违反自身隔离契约 | `bench-v3.sh` 第 28/31 行把 `/var/run/docker.sock` 与整个 `$HOMEDIR` 挂进容器，与 ADR-0009「host runtime socket 不进入 VM」直接冲突 → AGENTS.local 中「docker 模拟 VM 边界、与 VM launcher 同构」的表述不成立，该批结果不能作为正式隔离边界证据（BR-013）。远端 `/dev/kvm` 可用、24 核/754G/25T 空间充足，但 qemu 未安装且 `sudo` 需密码（人类已认领安装 `qemu-system-x86 qemu-utils`）。决策（2026-08-22）：开发期继续 Docker，**只对最终发布子集跑 formal VM** | 2026-08-22 发布就绪审计 | candidate | — |
| BL-019 | 5 个 run 技能发现失败导致配置不一致 | bench-206/211/216/224/227 的 `container.log` 出现「paperutils 技能不可用」，而远端 `~/.agents/skills/paperutils` 存在且 `bench-v3.sh:30` 已挂载 → 技能发现存在 bug。后果：这批 35 run 不满足「同一系统配置」，正式批次前必须定位修复并核验（否则跨 entry 结果不可比） | 2026-08-22 发布就绪审计 | candidate | — |
| BL-020 | benchmark 定位须与 ClaroAI/RepliCAI 原作者工作切分 | 派生源 `~/Project/claroai-bench` 不只是数据集，还含 `manuscript/neurips2026/`（NeurIPS 2026 投稿：multi-agent scoring + autonomous reproduction + MIAR 框架）、`RepliCAI_Bench_Manuscript.docx`、`replicai/agents/agentic_d5.py`（作者自己的复现 agent）。许可 MIT（可衍生，须署名/引用）。本项目 35/43 entry 派生自其数据，novelty 必须落在：可执行 + 引擎无关 + oracle 与被测系统隔离 + 确定性 comparator + 多系统可比；任务设定「只给 DOI，自行找数据建环境」严格难于 CORE-Bench 的 capsule 重跑，是可辩护的差异轴。related work 必须处理 CORE-Bench / ReplicationBench / Xu&Yang（政治学 3382 模型）/ OpenPub Copilot。作者 D5 的「quantitative match within 5%」可作 comparator 容差对照 | 2026-08-22 发布就绪审计 | candidate | — |
| BL-011 | ClaroAI-Bench 接入（L4/L5 真实论文基准来源） | 调研完成（2026-08-04，资料在 `~/Project/claroai-bench*`：GitHub 仓库/HF dataset/Zenodo 归档，调研报告 `~/Project/claroai-bench/RESEARCH_REPORT.md`）。35 篇真实 NIH 论文 + 作者 D1–D5 ground truth（scores.json 含 evidence/justification）。接入需 converter：metadata.json/extraction.json/scores.json → 标准 entry（metadata.yaml/bundle.yaml/oracle/claims.yaml+rubric.yaml）；不附带论文全文（版权，与 claroai-bench 归档一致），entry 为 L5，primary paper 用 DOI/PMID locator（external），被测系统运行时自行获取；D1–D3 rubric 可从 evidence 半自动转换，D4–D5 数值 claims 需逐篇人工补全；评分哲学差异（作者多模型审计评分 vs 本项目独立确定性评分）由 ADR-0010 决策。关联 0002-l4-l5 容器（pending）与 ADR-0008 entry taxonomy。已确认：converter 转标准 entry、35 篇 D1-D3 审计先行、bench-200+、确定性 checks+分数校准、远端 gs 运行、不附带论文全文 | claroai-bench 调研 2026-08-04 | planned | 0020-claroai-bench-adapter |

---

## 本轮候选排序建议（2026-08-22 发布就绪审计）

> 背景：35 篇 ClaroAI 批量运行完成后做的一次发布就绪审计。目标是两篇论文
> （benchmark + 复现系统）。审计结论：当前数据不足以支撑任一篇，根因是**量具与被测物
> 同时在变**（35 run 跑完后 oracle 仍在改 → 离线重评、bench-223 claim 被覆盖丢失、
> bench-222 verdict 从 100 翻到 30）。

**人类已作决策（2026-08-22）**

| 决策点 | 选择 |
|--------|------|
| 论文路线 | A（benchmark 论文）+ C（校准/测量学短文）**并行** |
| 19 个零 claims entry | **手工从论文原文抽 claims**，A1/A2 转诊断 |
| 运行边界 | 开发期 Docker，**只对最终发布子集跑 formal VM**（qemu 由人类安装） |
| baseline | **裸 agent（同模型无工作流）+ 一个现成开源 agent** |
| 系统创新轴 | 待定——等 BL-017 失败分布出来再选（不拍脑袋） |

**排序原则（防返工）**

1. 量具先冻结，再花算力：昂贵批次只在 oracle + 协议 + evaluator 打 tag 之后跑
2. 优先做零算力工作：读已有产物、改协议、改评分器——怎么改都不浪费算力
3. 被测物改动必须成对跑（同子集 before/after），使改动自动成为 ablation 证据

**建议顺序**

| 序 | 条目 | 内容 | 算力 | 返工风险 |
|----|------|------|------|---------|
| S0 | BL-017 | 35 run 失败分类学 | 零 | 无 |
| S1 | BL-014 | 协议 v3（questions.json / report.json）+ 类型化 evaluator + fixture | 零 | 无 |
| S2 | BL-015 | claim 策展 → oracle v2.0.0 打 tag 冻结 | 零 | 无 |
| S3 | BL-016 + BL-019 | 修 goal 硬编码 + 动态路由 + 技能发现 bug；系统写 report.json | 小（成对子集） | 低，产出 ablation |
| S4 | — | 裸 agent + 开源 agent baseline harness | 小 | 低 |
| S5 | BL-018 | 冻结量具下正式批次 N≥3 + 发布子集 formal VM | 大 | S1/S2 冻结后为零 |
| 并行 | — | Track C 校准短文（用已有 35 run 数据，主张是测量口径而非复现率） | 零 | 无 |

S0/S1/S2 与 Track C 全部零算力——接下来数周不需要再跑任何 run。当前「不知道下一步做什么」
的根源是默认下一步是「再跑一批」，而那恰好是唯一会返工的选项。
