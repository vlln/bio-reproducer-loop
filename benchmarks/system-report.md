# bio-reproducer 测评系统架构报告

> 描述对象：`benchmarks/` 下的公开 benchmark（L3-L5）测评系统——引擎无关、独立评分的
> 论文复现基准，可被任何复现系统采用。
> 版本：benchmarks/VERSION = 2.1.0；协议 protocol_version 2.0；oracle v2.0.0（冻结，
> tag `oracle-v2.0.0`）。
> 本文回答：系统由哪些文件/程序组成、各自功能、如何产生（演化来源）。
> 配套文档：docs/adr/0001~0011、docs/interface/0001-benchmark-protocol.md、
> 0002-claroai-converter.md、docs/plans/0025、0026。

---

## 0. 系统全景（一张图）

```
┌────────────────────────────── 测评方（本系统） ─────────────────────────────┐
│                                                                              │
│  ┌─ entries/（35+6 个 entry 束）──┐                                          │
│  │  metadata.yaml  bundle.yaml    │                                          │
│  │  input/ (paper/questions)      │                                          │
│  │  oracle/ (claims/rubric/verify)│                                          │
│  └──────────────┬────────────────┘                                          │
│                 │ validate_entry (bundle_validator)                          │
│  ┌──────────────▼────────────────┐        ┌───────────────────────────┐      │
│  │ runner/adapters/loopflow.py   │        │ harness/run-entry.sh      │      │
│  │ (唯一引擎耦合层)               │◄──────►│ (dind sidecar 沙箱)         │      │
│  └──────────────┬────────────────┘        └───────────────────────────┘      │
│                 │ 执行被测系统（loopflow bio-reproducer，7 阶段工作流）        │
│                 ▼                                                           │
│  ┌──────────────────────────────┐                                          │
│  │  run 产物 repro-data/         │  标准格式文件：01_plan … 06_validate       │
│  │  05_run/answers.csv          │  sha256sums、digests、answers/routing     │
│  └──────────────┬───────────────┘                                          │
│                 ▼ 独立评估（证据面=真实产物，不读系统散文）                    │
│  ┌──────────────────────────────┐        ┌───────────────────────────┐      │
│  │ independent_evaluator.py     │        │ converters/claroai/        │      │
│  │ + entry/oracle/verify.py     │        │  converter.py (生成入口)     │      │
│  └──────────────────────────────┘        │  evaluate_run.py (评归档 run)│     │
│                                          └───────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────────┘
```

三层职责分离（ADR-0005 独立评估原则）：
1. **入口层（entries/）**：被评论文的"考试题"——公开输入 + 私有 oracle
2. **执行层（runner/ + harness/）**：把入口翻译成被测系统调用，隔离沙箱运行
3. **评估层（independent_evaluator + oracle/verify.py）**：只读真实产物，独立评分

---

## 1. 入口层：`benchmarks/entries/`（考试题）

### 1.1 一个 entry 的结构（以 bench-220 为例）

```
benchmarks/entries/bench-220/
├── metadata.yaml          # 任务声明：id、DOI/PMID、task（自然语言任务）、language、protocol_version
├── bundle.yaml            # 输入束清单：资源（paper/数据/代码）定位 + sha256 + 依赖图
├── input/
│   ├── paper/locator.md   # 论文定位器（DOI/URL）
│   └── questions.yaml     # 公开问题清单（target_id 列表，评测方生成，系统侧不感知）
└── oracle/                # ★ 私有，不进被测系统
    ├── claims.yaml        # 数值声明：paper_value + 容差 + target_id + 出处 + 作者复现值
    ├── rubric.yaml        # 评分权重：A1/A2 诊断(10/10) + C1-Cn 平分 80
    └── verify.py          # 生成的自校验器：check_claim / check_data_refs / check_code_refs
```

### 1.2 各文件功能

| 文件 | 功能 | 谁看 |
|------|------|------|
| `metadata.yaml` | 声明协议版本、任务自然语言描述、语言 | 适配器（读 task → loop scope） |
| `bundle.yaml` | 输入束完整性契约：每个资源必须可定位、可验证（sha256），资源依赖图无环 | bundle_validator（评分前强校验） |
| `input/paper/locator.md` | 论文定位（DOI 或文件） | 适配器 → 系统 |
| `input/questions.yaml` | 公开问题清单（复现目标键） | 评测方 → 注入通道（`questions_inject.py`） |
| `oracle/claims.yaml` | **数值 ground truth**：论文报告值、容差、出处 | 只被 verify.py / 评估器读取 |
| `oracle/rubric.yaml` | 评分权重配置 | 评估器汇总 |
| `oracle/verify.py` | 单条 check 的可执行实现 | 独立评估器动态加载 |

### 1.3 关键设计：oracle 与"证据面"

ADR-0011（可验证的自我判定）是本系统最核心的架构决策，三条约束：

1. **事实以标准格式文件持久化**：sha256sums 输出、docker digests、CSV、curl 日志、退出码——不用散文。
2. **自定义格式仅两个**：`05_run/answers.csv`（4 列：target_id, value, unit, source_file）和
   `06_validate/routing.jsonl`（5 键：ts, target, decision, route_to, reason）。
3. **外部评分证据面收缩到真实产物**：`06_validate/` 不在证据面内——评估器不读系统的
   自我报告，只读 answers.csv + sha256sums + digests。

### 1.4 entries 从哪来

- **bench-001~006**：手工构建的 L3/L4 层测试 entry（v1 风格 rubric，T 编号路径，无 questions.yaml）
- **bench-100**：早期单一 entry
- **bench-200~234（35 个）**：**由 converter 从 ClaroAI-Bench 数据集自动转换生成**
  （`converters/claroai/converter.py`，BL-011 / ADR-0010 / Interface 0002），
  来源 `~/Project/claroai-bench/`（GitHub/HF/Zenodo 副本）。

---

## 2. 转换器：`benchmarks/converters/claroai/`

### 2.1 `converter.py`（728 行）——ClaroAI → 标准 entry 生成器

功能：把 ClaroAI-Bench 的论文目录 + `scores.json` 审计输出转成标准 entry 束。

关键函数：
- `_extract_d5_claims(scores)`：从作者审计的 D5 evidence 转录数值声明
- `_build_claims()`：生成 claims.yaml（数值 + 容差 + 出处）
- `_build_questions()`：生成公开问题清单（target_id 逐字）
- `_build_rubric()`：生成评分权重（A1/A2 + C1-Cn）
- `_build_bundle()`：生成 bundle.yaml（含 paper locator 的 sha256）
- `_build_metadata()`：从论文 metadata + claims 推导自然语言任务
- `convert_snapshot()`：批量转换整个数据集（35 entry，start_id=200）
- 尾部 `check_claim / check_data_references / check_code_references`：**生成的
  verify.py 模板**——被转换进每个 entry 的 oracle/

产生方式：BL-011 需求 → ADR-0010 决策 → Interface 0002 定义 → 本实现（fe2aff0 起，
35 entry 首批落地）。**演化教训**：converter 重生成会覆盖手工补的 claims（P1-1 事故，
bench-223 AUROC 丢失），故新增幂等保护 + 回归检查。

### 2.2 `evaluate_run.py`（100 行）——归档 run 独立评分器

功能：对已完成 run 重新跑独立评估，输出 verdict/score/checks + 作者校准对照。
`evaluate_run.py <run_dir> <entry_dir>`。

证据面演变（重要）：
- **旧协议**（读 06_validate/report.md 等系统散文）→ 已废弃
- **新证据面**（ADR-0011 §4）：只读 `05_run/answers.csv` + `04_data/sha256sums.txt`
  + `03_provision/digests.txt`；旧 pilot run 无这些文件 → 明确拒绝重评
  （"旧协议 run 不可用新口径重评"）

### 2.3 `s2_apply_claims.py`（120 行）——S2 claim 策展落盘器

功能：幂等地把人工提取的数值 claims 写入 17 个零 claims entry：
claims.yaml（数值+target_id+容差+出处）、questions.yaml（同步键）、rubric（A1/A2→10/10、
C1-Cn 平分 80）、bundle sha256 更新。

产生方式：BL-015 决策（2026-08-22）→ S2 执行（2026-08-28）。**为何必须存在**：
converter 转录自作者审计输出（scores.json）有已知错误，且 19/35 篇零 claims——
必须从论文原文人工策展，量具才可信。S2 后 oracle v2.0.0 冻结。

### 2.4 `cli.py`（转换器入口）

- `cli.py`：转换器命令行入口
- `backfill_evidence_switch.py`：证据面切换时对既有产物的回填工具（**一次性**，
  2026-08-26 已用完 → 归档至 `docs/plans/0026-file-centric-artifacts/archive/`）

---

## 3. 执行层：`benchmarks/runner/`

### 3.1 `cli.py`（455 行）——runner 命令行

```
python -m benchmarks.runner.cli run --entry bench-00X --runs 5
```
子命令：run（跑 entry）、validate（校验 bundle）、evaluate（评产物）等。是引擎无关
的测评执行入口（benchmark 协议侧），与具体引擎解耦。

### 3.2 `runner.py`（83 行）——编排器

"Run a single benchmark entry N times, collect results." 负责：N 次重复、结果收集、
汇总到 `benchmarks/results/summary.json`（gitignored，观测非基准真值）。

### 3.3 `adapters/loopflow.py`（580 行）——唯一引擎耦合层

**本系统最关键的"翻译器"**：把标准 entry → loopflow（bio-reproducer 引擎）调用。

流程：
1. `validate_entry()` 先校验 bundle（评分前强校验）
2. 读 metadata（protocol_version 必须 2.0）
3. `_stage_input()` 只暂存**公开**输入（oracle 不进被测系统）
4. `_resolve_primary_paper()` 解析论文定位
5. 构造 loopflow 命令：
   - `--args`（language/consent/routing_budget/scope 等）
   - `--work-dir /output`（统一工作目录）
   - `--append-prompt <注入段>`（评测方注入，见 §4.2）
6. `build_submission_from_existing()`：run 结束后从 repro-data/ 反向组装 submission.json
   （`_artifact_candidates` 找证据文件、`_read_verdict_and_score` 读系统自评供对照）

**职责边界（2026-08-27 讨论定型）**：本适配器是"系统侧不感知评测设计"的保障——
任务说明（metadata.task）、问题清单注入、证据面声明全部由评测方在边界完成；
评分维度代码（旧 scored_scope）禁止进入被测系统（评估设计泄漏，ADR-0010 修订）。

### 3.4 `sandbox.py`（207 行）——容器边界

"Container boundary for benchmark systems under test." DockerSandbox：构建/挂载
/input /workspace /output，`--cap-drop ALL --user 1000:1000` 零特权，不挂宿主
socket（ADR-0009 一次性 VM 边界精神，开发/校准用容器模拟）。

### 3.5 `worker.py`（492 行）——一次性 VM 后端（正式发布用）

"QEMU/KVM disposable worker backend for formal benchmark execution." QemuWorker：
预检、启动、SSH 等待、guest 内执行、QMP 关停、sha256 完整性（`sha256_tree`）。
**与 harness 的分工**：正式发布结果必须走 disposable VM（ADR-0009 / BR-013），
harness 的 dind 容器仅供开发/校准——两者不可混同（run-entry.sh 注释明示）。

### 3.6 `bundle_validator.py`（386 行）——入口束信任校验

"Validate the trusted entry bundle before staging runtime input."
- `validate_entry()`：bundle schema、资源路径、依赖图无环、primary paper、level
  合规、metadata 键精确（`_require_exact_keys`）、时间戳、sha256
- **防信任问题**：评分前强制 bundle 完整（缺失 sha256/资源 → 拒绝），保证"被测系统
  拿到的输入是可信快照"
- `_is_audit_mode_entry`：兼容早期审计模式 entry（legacy）

### 3.7 `independent_evaluator.py`（405 行）——独立评估器

"Evaluate benchmark artifacts against a private oracle." **评分核心**：

- `evaluate_submission()`：入口——读 submission.json + rubric → 解析 artifacts →
  逐条执行 check
- `_evaluate_check()`：按 rubric 的 check 声明（artifact_role + 比较规则），把
  证据文件喂给 entry 自己的 `oracle/verify.py`（`_run_python_verifier` 动态导入）
- `_compare()`：数值比较（含容差）、CSV 行查找（`_read_csv`/`_find_row`）
- `_verdict()`：分数 → REPRODUCED/PARTIAL/FAILED/BLOCKED 映射
- **NO-EVIDENCE 语义**：`{"passed": False, "no_evidence": True}` 的 claim 从权重中
  剔除（不是判错）；全部 no-evidence → BLOCKED

### 3.8 其余

- `execution.py`：ExecutionRequest 数据契约（executor-neutral）
- `release_gate.py`：正式提交的发布检查
- `reporter.py`：生成 summary.json 报告
- `system_artifact.py`（369 行）：构建/校验 opaque 系统产物（被测系统的发布包）

---

## 4. 执行 harness：`benchmarks/harness/`

### 4.1 `run-entry.sh`（207 行）——校准/验证运行入口

取代仅存在于远端、未纳入版本管理的 bench-v3.sh（2026-08-27 删除）。

与旧版的关键差异（全部来自 35 个 run 的实测教训，BL-018/021）：
1. **不再挂载宿主 docker.sock**——沙箱不再等于宿主 root；dind sidecar 承担镜像
   拉取（privileged 只在 sidecar）
2. **sidecar 与沙箱挂载相同路径**——修复 Nextflow docker executor 挂载失败根因
   （19 个 run 因此被迫手工 docker run + docker cp）
3. **技能前置校验**（harness-probe.sh）：requires.bins / requires.env 启动前检查
4. **loop 定义只读挂载**到 ~/.loopflow/loops/（selftest 不跑 loop 的路径缺口）
5. **Claude Code backend env 注入**（--env-file，不挂整个 ~/.claude）
6. **registry-mirror 透传**（BL-008：远端 Docker Hub 直连被墙）
7. **运行时镜像默认** `bio-reproducer-runtime:system-idlefix-cc247`
   （claude 2.1.247 + stream watchdog，BL-013 修复产物）
8. **技能目录挂载**到 `/home/sandbox/.claude/skills`（BL-029：claude Skill 工具查找
   ~/.claude/skills，之前只注入 prompt 文本导致 "Unknown skill"）

### 4.2 `questions_inject.py`（61 行）——公开问题清单注入

**评测方职责**（系统侧不感知）：把 `input/questions.yaml` 翻译成任务注入段
（loopflow 原生 `--append-prompt`，≤64KiB，注入每个 agent 的 user prompt 末尾），
返回键列表供系统侧 lint 校验（args.question_keys）。无 questions.yaml → (None, [])，
系统退化为 T 编号路径（v1 风格不变）。

**为何这样设计（2026-08-27 讨论）**：系统侧不写任何文件名——问题清单的存在/位置
是评测方职责；避免系统"抄答案"（针对 bench-221 曾把评分维度误读进 scope 的教训）。

### 4.3 `verify-0026-run.sh`（103 行）——端到端契约检查

19 项检查：run 产物是否满足 ADR-0011 新契约（answers.csv 存在、target_id 对齐、
sha256sums、digests、routing.jsonl 等）。PASS=19 FAIL=0 于 run7。

### 4.4 辅助

- `verify-0026-run.sh`：19 项契约检查（**已固化为 pytest**：
  `tests/contract/test_verify_run_contract.py`，fixture 为 run7 真实产物快照）
- `harness-probe.sh`：harness 前置探针（网络 3/3、技能前置）——BL-019 教训：
  "任何网络不通/技能坏了的判断必须先跑它"
- `crosscheck-prototype.py` / `backfill_evidence_switch.py`：原型与一次性迁移
  （**已归档**至 `docs/plans/0026-file-centric-artifacts/archive/`，逻辑已分别
  内嵌 converter verify 模板与 35 entry 现状）
- `answers.csv` / `table2_q91_results.csv`：样例/夹具

---

## 5. Schema 与文档层

### 5.1 `benchmarks/schemas/`（JSON Schema）

| Schema | 校验对象 |
|--------|---------|
| `bundle.schema.json` | bundle.yaml 结构 |
| `claims.schema.json` | claims.yaml 结构 |
| `rubric.schema.json` | rubric.yaml 结构 |
| `submission.schema.json` | submission.json（被测系统交付物） |
| `result.schema.json` | 评估结果 |

产生方式：Interface 0002 定义的契约 → schema 硬化（bundle_validator 读入强校验）。

### 5.2 文档

- `README.md`：benchmark 目录索引
- `paper-entries.md`：待构建论文清单（Bottomly/Pickrell 等）
- `calibration-assets.md`：**校准资产索引**（P1/P2 批次、verdict 权威表、教训）
- `calibration-failure-taxonomy.md`：35 run 死因四分类（独立复核）
- `package-executability-probe.md`：交付包可执行性探针（0/6 通过教训）
- `claroai-results-report.md` / `claroai-divergence-analysis.md`：试点结果汇报与差异分析
- `baselines/README.md`：**基线纪律**——只有量具冻结 + 协议稳定 + 正式 VM 批次后
  才允许建基线；开发 run 属于观测，不是基准真值
- `VERSION`：2.1.0

---

## 6. 系统如何产生：演化时间线（关键节点）

| 阶段 | 产物 | 触发 |
|------|------|------|
| 0021（07-21） | converter 首批 35 entry（fe2aff0） | ClaroAI-Bench 接入（BL-011） |
| 0024/0025 | evaluate_run.py 入库、calibration-assets 索引 | 校准方法论确立（独立验证原则） |
| 08-18 | P1-1/P1-2：claims fidelity 修复 + 4 篇补全 | 转录缺口审计 |
| 08-19~22 | P2 批次（16/13/6）+ 看门狗 v2 + 死因分类学 | 35 篇批量跑 + BL-017 |
| 08-22 | ADR-0011 promote accepted；开执行容器 0026 | "REPRODUCED 不构成复现率"审计（BL-015） |
| 08-25~27 | run-entry.sh（dind sidecar）、证据面切换、注入通道 | 0026 单元 01-05，多轮首跑暴露缺口修复 |
| 08-27/28 | BL-013（claude watchdog）、BL-029（技能挂载）、S2（101 claims）、oracle v2.0.0 冻结 | 挂起根因 + 量具冻结 |
| 08-28+ | 结果汇报/差异分析 + 两轮对抗审查 + 追溯补登 | 试点汇报需求 |

**系统成熟度判断**（baselines/README 五条门槛）：入口束 ✓、oracle 冻结 ✓（v2.0.0）、
runner/评估协议稳定 ✓、但**正式 VM 批次未跑**（S5 未执行）→ **尚无发布基线**，
当前所有数字均为试点观测。

---

## 7. 一句话总结

本测评系统 = **转换器（生成考题）→ 入口束（考题+私有答案）→ 适配器+harness（隔离
执行）→ 独立评估器（只读产物评分）** 四段式；最核心的架构约束是 ADR-0011 的
"证据面收缩到标准格式真实产物"——系统自述不算数，只有落盘的 answers.csv/
sha256sums/digests 才算数；量具（oracle v2.0.0）已冻结，但正式结果尚需 S5 一次性
VM 批次才能发布。
