# 交接说明（0026 容器）

> 写给接手的 agent。**只凭文件即可恢复状态**，不要依赖任何对话历史。
> 最后更新：2026-08-27（单元 06 完成后——容器全部单元 done）

## 先读这些（按序）

1. `docs/README.md` —— 当前阶段（`DESIGN`，设计缺陷退回）与退回定级依据
2. `docs/backlog.md` —— BL-014~BL-026 是本轮全部工程债；**文件末尾有防返工排序（S0-S5）与人类已作决策**
3. `docs/adr/0011-verifiable-self-assessment.md` —— accepted，本容器的唯一设计依据；
   **文末「被废弃的第一稿」记录了三类必须避免的思维惯性**
4. 本容器 `README.md`（单元表 + 状态 + 完成判据）→ `01-report-harness-fixes.md` →
   `02-report-artifact-contract.md` → `03-report-validate-internalization.md` →
   `04-report-evidence-switch.md` → `05-report-doc-sync.md` → `06-report-package-self-contained.md`
5. `benchmarks/calibration-failure-taxonomy.md`、`benchmarks/package-executability-probe.md` —— 35 run 的实测事实基础

## 容器已完成（01-06），下一步：run-entry.sh 端到端首跑

单元 02-06 全部落地（Report 02-06），Spec/Interface/AC 已 promote。
**剩余执行项**：`run-entry.sh` 完整 entry 首跑（新契约端到端 + Package 干净容器
冒烟）——需算力 + 宿主 `export MINERU_API_URL=http://172.16.218.40:8001/`；
跑通后删远端 `bench-v3.sh`，并请人类按容器完成判据验收（README「完成判据」节）。

下游文档同步（Spec 001、Interface 0001/0002、AC），**改完给简报、需人类再次 promote**：

1. **`input/questions.*` 公开问题清单**写入 Interface 0002 / Spec 001：target_id 生成
   规则（metric slug）、系统 answers.csv 对应关系、无期望值（ADR §4.1 的 limitation
   声明也在此补）
2. **新产物契约写入 Interface 0001**：04_data（sha256sums + 每资源日志）、03_provision
   （digests.txt）、05_run（results/ + answers.csv + commands.log）、routing.jsonl
   （键名白名单 ts/target/decision/route_to/reason）
3. **AC 补场景**：FC-001~FC-008 每条对应检出手段（单元 02-04 已实现大部分，AC 需同步）
4. **FC-003 措辞修订**：routing.jsonl 的 reason 字段与 FC-003 字面「不得含理由字段」
   冲突——§3 明示含 reason，以 §3 为准；修订 FC-003 为「键名白名单」
5. **NO-EVIDENCE 语义**写入 AC（不计分不扣分、全无证据 → BLOCKED）

## 系统侧与 benchmark 侧现状（单元 02-04 全部落地）

- 系统侧：04_data/05_run/03_provision 标准格式契约 + `_require_parsable` fail-fast +
  goal 从 plan.md 派生 + Validate 内部路由（routing.jsonl）+ 回环预算（调用方给定）
- benchmark 侧：35 个 claroai entry 已迁移（claims target_id + questions.yaml +
  rubric 重挂 + 新 verify.py；7 个手写 entry 按保护跳过），**评分只读
  answers/sha256sums/digests**，NO-EVIDENCE 三态
- `evaluate_run.py` 只接受新契约 run（旧 pilot run 不可重评——报错，勿绕行）
- 技能（paperutils/mineru-api）已恢复并补齐前置（2026-08-27）

## 远端与脚本部署（必读，否则会白跑）

- 远端：`ssh gs@172.16.209.237`（免密）。**不要用 rex 脚本**（`extra_opts[@]` unbound 变量 bug）
- 仓库内的 harness 脚本**不会自动出现在远端**，用前先 `scp`：
  ```bash
  scp benchmarks/harness/run-entry.sh benchmarks/harness-probe.sh gs@172.16.209.237:/tmp/
  ssh gs@172.16.209.237 'bash /tmp/run-entry.sh selftest'      # 六项边界自检，应 6/6
  ssh gs@172.16.209.237 'bash /tmp/harness-probe.sh'           # 前置探针
  ```
- **新 run 一律用 `run-entry.sh`，不要再用远端 `bench-v3.sh`**（后者挂 docker.sock，违反 ADR-0009，
  且是 Nextflow 挂载失败的根因）
- 归档 run 在 `/storeData/gs/claroai-calibration/runs/bench-2NN/repro-data/`；`*-legacy-*` 忽略
- 单元 02/03 的契约测试 fixture 在 `tests/fixtures/contract/`（bench-234/217 真实产物，
  含裁剪说明），新增契约测试直接复用

## 纪律（违反过，代价已付）

1. **任何「网络坏了 / 技能坏了 / 数据拿不到」的判断，必须先跑 `harness-probe.sh` 实测**。
   BL-019 因为跳过实测被误诊两次（先怪技能注入，再怪出口网络），两次都是拿单行日志当根因
2. **不要拍阈值**（重试几次、偏差多少算复现）：阈值属评分策略，归 oracle，系统内一个魔数都不留
3. **不要发明厚 schema**：已有标准格式的事实必须用标准格式；自定义只允许 `answers` 与
   `routing.jsonl`，且键名白名单（answers 4 列 / routing 5 键，lint 在 artifact_checks.py）
4. **不要在量具冻结前跑批**：35 run 已因此返工一次；单元 03 的 LLM 成对跑（ablation）也
   要等量具冻结后（Report 03 已记录该排期）
5. **不要 push**（人类明确要求）；commit 照常
6. 系统改动要成对跑（同子集 before/after），使改动自动成为 ablation 证据

## 已完成但未部署 / 未验证的部分

- `run-entry.sh` **首跑已完成（2026-08-27）**：bench-220 跑通 Reader→Bootstrap→Provision，
  终止于 Provision 收尾的 agent 挂起（见 `07-report-first-run.md`）；产物已归档
  `/storeData/gs/claroai-calibration/runs/bench-220-0026-run1/`
- **BL-013 挂起根因已确认并修复（2026-08-27 续）**：claude 2.1.126 对非官方端点 SSE
  看门狗默认关闭（v2.1.196 起才默认开）。修复：镜像内 claude 升级 2.1.247
  （`bio-reproducer-runtime:system-idlefix-cc247`）+ settings.json watchdog env +
  loopflow 子进程感知看门狗（develop `4b9bdf7`）。
- **重跑已完成（run2，2026-08-27）**：`/tmp/harness/run-bench-220-20260827-161422`，
  归档 `/storeData/gs/claroai-calibration/runs/bench-220-0026-run2/`——BL-013 修复后
  **7 阶段一次跑通**（REPRODUCED 98/100 自评），Data/Run/Validate/Package 契约全部
  真实落盘（sha256sums/answers.csv/routing.jsonl/check.log，verify-0026-run.sh 19 项全过）。
- **验收发现并修复 target_id 脱节（run2 后）**：answers 用了 plan.md T 编号而非公开
  问题清单键（ADR-0011 §4.1）→ 外部评分 C1-C3 全 NO-EVIDENCE。已修 run.md/reader.md/
  artifact_checks.py（check_run_phase 键对齐 fail-fast）+ 契约测试，全量 206 passed。
  **剩余**：修复后需再跑一次 run3 让外部评分闭环（C1-C3 应真正计分）。
- 宿主先 export `MINERU_API_URL=http://172.16.218.40:8001/`
- 远端 `bench-v3.sh` 暂留，等 `run-entry.sh` 跑通完整 entry 后再删
- `benchmarks/harness/crosscheck-prototype.py` 是交叉核对原型，其 locate 逻辑已内嵌
  `VERIFY_TEMPLATE`（单元 04）；原型与样例（3 PASS / 2 NO-EVIDENCE）保留可复跑
- **单元 04 迁移教训**：backfill 初次运行误改 7 个手写 entry（bench-001~006/100）的
  verify.py 并生成空 questions.yaml——已 git 恢复并加结构保护；迁移脚本必须幂等 +
  只处理目标结构（`backfill_evidence_switch.py` 已含保护）

## 待人类决策（不要自己拍）

1. **Spec 001 / Interface 0001+0002 / AC 的修订 promote**（单元 05）：不可委托门禁，改完给简报
2. qemu 安装：人类已认领，但**只影响可发布正式结果**（ADR-0009/BR-013），不阻塞本容器任何单元
3. `paperutils` CLI 与 MinerU 端点：**已补齐（2026-08-27，人类提供来源）**——paperutils
   = GitHub vlln/paperutils（本机 `~/Project/skill_project/paperutils/`），mineru =
   `http://172.16.218.40:8001/`（/health 200）。两端 `~/.agents/skills/` 已同步为源仓库
   版本（paperutils 的 requires.bins 为旧版过时声明，已随同步消失）；`MINERU_API_URL`
   由宿主 export + run-entry.sh 透传（harness-probe.sh 已同步）。新 run 直接可用两个技能。
   远端同步技能用：`scp -r ~/Project/skill_project/paperutils/skills/paperutils gs@172.16.209.237:~/.agents/skills/`
   （mineru-api 远端已完整）
