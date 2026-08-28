# Report 07 — run-entry.sh 端到端首跑（进行中）

> 2026-08-27。目的：验证单元 01-06 改动（dind 新基建、动态路由、新契约闭环）。
> 本报告记录首跑暴露的 harness 缺口与修复（已完成部分）；run 结果待完成后补全。

## 首跑暴露的三个缺口（全部已修复，commit 逐条记录）

selftest（单元 01）只覆盖边界自检，**不跑 loop**——完整 entry 首跑暴露三个
「selftest 覆盖不到」的缺口：

| # | 缺口 | 现象 | 修复 | commit |
|---|------|------|------|--------|
| 1 | sandbox 未挂载 loop 定义 | `loop run bio-reproducer` 在沙箱找不到 loop（~/.loopflow/loops/） | 挂载 `$REPO/loops/bio-reproducer` → `/home/sandbox/.loopflow/loops/bio-reproducer:ro`（loop 定义与 entry input 同源） | 8744861 |
| 2 | backend env 未进沙箱 | Claude Code 无 ANTHROPIC_* env（宿主配置在 ~/.claude/settings.json）→ Reader 无产物 fail-fast | 从宿主 settings.json 的 env 块生成 `--env-file` 注入（最小暴露：只传 env，不挂 .claude 目录） | 3e2fa22* |
| 3 | /home/sandbox 不可写 | 镜像内无 /home/sandbox（docker 自动创建 root 属主）→ claude 写 ~/.claude session 静默失败；迭代 2：skills 嵌套挂载使 docker 预建 .loopflow 仍 root 属主 | 整个 /home/sandbox 挂载 `$RUN/home`（777）+ **宿主预建 `.loopflow` 777**（防 docker root 预建） | 2 个 commit |

诊断方法（可复用）：宿主对照组（`claude -p` 在宿主 OK、沙箱静默 → 环境差异定位到
HOME 可写性）；container.log 的 fail-fast 时序（几秒内「前置产物缺失」= agent 调用
未产出，非正常快速完成）。

## 运行结果（2026-08-27 补全）

- entry: bench-220，run 目录 `/tmp/harness/run-bench-220-20260827-113053`，
  已归档 `/storeData/gs/claroai-calibration/runs/bench-220-0026-run1/`
- **终止于 Provision 收尾**：agent API 调用挂起（claude 会话 45+ 分钟无活动、
  无子进程、loop CPU 停滞——BL-013 已知「LLM 长会话无超时」缺陷的又一次实证，
  bench-229 曾挂 6.5h 同类）。后端健康（dashscope 200/1.35s）——挂起在 claude CLI
  侧连接，非我们的改动缺陷。已 kill + 清理，产物保留。

## BL-013 根因确认与修复（2026-08-27 续）

挂起后排查（非猜测，全部实测）：
1. **会话文件定位挂起点**：最后事件 = `assistant thinking`（12:44:22，
   「Now let me finalize the provision.md…」）——模型思考完毕**正要发 Edit tool_use
   时 SSE 流静默中断**，assistant 消息永远不完整，claude CLI 无超时等待。
2. **排除服务端**：curl 直连 dashscope（普通流 / thinking+工具 / 强制 tool_use /
   重放挂起会话 201 条历史）全部完整结束（message_stop 正常），4 次测试 0 挂起；
   claude CLI 多轮工具循环（3 步、15 步）也正常——**是偶发静默断流，非确定性路径**。
3. **确认 `API_TIMEOUT_MS` 对流式无效**：设 30000ms 实测 150s 仍未触发（该变量只
   作用于请求建立，不覆盖流式读取）；且宿主配置 3000000ms（50min）是放大器。
4. **定位上游根因**：Claude Code 官方 changelog——
   - v2.1.196（2026-06-29）：「streaming idle watchdog 现**对所有 provider 默认开启**，
     5 分钟无事件即 abort+retry」——我们镜像里的 **2.1.126 在此版本之前**，
     对非官方端点（dashscope 走 ANTHROPIC_BASE_URL）看门狗默认关闭。
   - v2.1.210（2026-07-14）：「新增 `CLAUDE_STREAM_IDLE_TIMEOUT_MS`（默认 90s）」。
   - 另有条目精确对应本症状：「Fixed a hang where the assistant could finish
     thinking but show no output after a run of empty turns」。

### BL-013 修复（已落地）

| 层 | 动作 | 状态 |
|----|------|------|
| 主防：claude 版本 | runtime 镜像内 claude 2.1.126 → **2.1.247**（npm 全局包），commit 为 `bio-reproducer-runtime:system-idlefix-cc247` | ✅ |
| 主防：watchdog 配置 | 宿主+远端 `~/.claude/settings.json` env 块加 `CLAUDE_ENABLE_STREAM_WATCHDOG=1` + `CLAUDE_STREAM_IDLE_TIMEOUT_MS=300000`（5min，官方 clamp 10s~30min 内） | ✅ |
| 主防：harness | run-entry.sh 默认镜像改 `system-idlefix-cc247`（`HARNESS_RUNTIME_IMAGE` 可覆盖）；backend.env 自动透传新变量（settings.json env 块直出） | ✅ |
| 兜底：loopflow | `CliTransport` 空闲看门狗完善为**子进程感知**：idle 超时但子进程存活（mip/docker pull 长命令）继续等，无子进程才 kill；默认 43200s→7200s；新增 7 测试；提交 loopflow develop `4b9bdf7` | ✅ |
| 验证 | 新镜像 claude 2.1.247 真实 dashscope 冒烟 EXIT=0；loopflow 全量 446 passed；harness selftest 6/6（含 Nextflow docker executor，ubuntu:22.04 经 mirror pull） | ✅ |

注意：升级镜像内 claude 2.1.247 后，模型名验证更严格（mock 端点
`unrecognized_model` 会被拒）；真实 dashscope 链路不受影响（冒烟已证）。

### 已验证（首跑目的部分达成）

| 验证项 | 结果 |
|--------|------|
| dind 新基建（无 docker.sock、registry-mirror 透传、任务容器挂载） | ✅ 镜像经 dind 拉取成功（rocker/r-ver 1.21GB + r-base 1.17GB） |
| loop 定义挂载（run-entry.sh 修复 1） | ✅ `loop run bio-reproducer` 正常加载 workflow/agents |
| backend env 注入（修复 2） | ✅ Reader 正常调用 claude（dashscope deepseek-v4-pro） |
| HOME 可写（修复 3） | ✅ claude 会话写入正常 |
| 技能补齐（单元 02）：paperutils + mineru-api | ✅ Reader 真实使用（paperutils 元数据 + mineru-api PDF 转换，WebFetch blocked 后 curl 兜底） |
| goal 从 plan.md 派生（单元 03） | ⏳ 未直接观察（container.log 无 goal 日志；plan.md 已产出待核对） |
| provision 契约 digests.txt（单元 04） | ✅ `03_provision/digests.txt` 落盘（docker images --digests 原始输出） |
| provision 纪律（镜像复用/技能/mip） | ✅ mip pull 走 image-mirror-skill + 交互验证后固化 Dockerfile；SAS 正确标 out-of-scope |
| 动态路由 / answers / routing.jsonl / check.log | ⏳ 未到阶段（Data/Run/Validate/Package 未执行） |

### 未验证（需重跑）

Data（curl -C - 续传）、Run（answers.csv）、Validate（routing.jsonl 回环）、
Package（check.log）。**重跑前置已解决**：BL-013 根因确认（claude 2.1.126 对第三方
端点 SSE 看门狗默认关闭）+ 官方修复（升级 2.1.247 + `CLAUDE_STREAM_IDLE_TIMEOUT_MS`）
+ loopflow 兜底（子进程感知看门狗）——见上文 BL-013 修复表，可直接重跑。

## 重跑完成（run2，2026-08-27 续）——端到端全通 + 发现并修复 target_id 契约缺口

**run2**：`run-entry.sh bench-220`，目录 `/tmp/harness/run-bench-220-20260827-161422`，
归档 `/storeData/gs/claroai-calibration/runs/bench-220-0026-run2/`（69M）。BL-013 修复后
**一次跑通全部 7 阶段**（Reader→Bootstrap→Provision→Data→Run→Validate→Package），
全程无挂起（claude 2.1.247 看门狗未触发，说明无静默断流；监控按进程树确认正常）。

| 验证项 | 结果 |
|--------|------|
| Data 契约：sha256sums.txt + 每资源日志 | ✅ 5 个关键资源 sha256 落盘 + 11 个 fetch.log（per-resource 纪律）；含 curl 206/Range 续传证据 |
| Data 纪律 | ✅ raw.githubusercontent 卡住自动切 git clone；NHANES-III .dat + 预测模型 RData + 分析代码全获取 |
| Run 契约：answers.csv + commands.log | ✅ 表头 4 列精确；3 行（T1/T2/T3）；`reports/commands.log` 落盘 |
| Run 实际计算 | ✅ `results/table2_cvd_hr_results.csv`（svycoxph 实际算得：血铅 1.63/胫骨 3.32/髌骨 2.42，与论文一致） |
| Validate 契约：routing.jsonl | ✅ 6 行，5 键白名单（ts/target/decision/route_to/reason），全部 reproduced、route_to=null 无需回环 |
| Package 契约：check.log | ✅ 前置检查（docker CLI/daemon/镜像）全 OK，EXIT=0；README + run.sh 自包含入口 |
| 独立评估器 evaluate_run.py | ⚠️ 见下方缺口——verdict REPRODUCED 但 C1-C3 NO-EVIDENCE |

### 验收发现并修复：answers target_id 与公开问题清单脱节（ADR-0011 §4.1 执行缺口）

- **现象**：evaluate_run.py 输出 `evaluator_verdict: REPRODUCED (100)` 但 C1/C2/C3 全部
  NO-EVIDENCE——answers.csv 用 plan.md 内部 T 编号（T1/T2/T3），而公开问题清单
  `input/questions.yaml` 与 oracle claims 的键是 metric slug（`blood-lead-cvd-hr` 等）。
- **根因**：`agents/run.md` 写成「target_id 用 plan.md 的复现目标 ID」，偏离
  ADR-0011 §4.1 / Interface 0002 §2.1「系统按公开问题清单键填 answers」。
- **修复**（本地 commit 待做）：(a) `run.md`：target_id 必须用 `input/questions.yaml`
  的键，无问题清单时才用 T 编号；(b) `reader.md`：Reproduction Target 表每行标注
  questions target_id（如 `id: T1 (blood-lead-cvd-hr)`）；(c) `artifact_checks.py`
  `check_run_phase` 增加键对齐检查——有 questions.yaml 时 answers target_id ⊆ 问题
  清单键，否则 Run 完成门 fail-fast（实测 T1/T2 → 拦截，slug → 通过）；(d) 契约测试
  +3（对齐/拦截/无清单兼容），全量 **206 passed / 4 skipped**。
- **影响**：本次 run2 的 answers 用了 T 编号，外部评分拿不到 C1-C3 证据；数值本身
  正确（与论文一致）且交叉核对可通过。修复后重跑一次即可让外部评分闭环。

## run3（2026-08-27）——补强验证：Reader 门 fail-fast 实证 + Questions Mapping 强制

run3（`/tmp/harness/run-bench-220-20260827-175437`，归档 `bench-220-0026-run3/` 68M）
在 run2 修复（run.md/reader.md 软指引）后重跑，**暴露软指引不够**：
- Reader 产出的 plan.md **没有** Questions Mapping（reader.md 的「若存在则标注」
  未被执行）→ Run agent 自造 `t2_cvd_bpb` 等 ID 且把 answers.csv 放进
  `05_run/results/`（位置也错）→ `check_run_phase` fail-fast 在 Run 完成后拦截
  （`前置产物不可用: answers.csv 缺失或表头不合规`），浪费了 Provision/Data 算力。
- **补强（commit 2f5d0e2）**：(a) reader.md 升级为**强制**——必读
  `input/questions.yaml`、逐字转录、plan.md 必须含 `Questions Mapping` 表；
  (b) run.md 显式禁止自造 target_id + answers.csv 位置钉死 `05_run/` 根目录；
  (c) artifact_checks 新增 `check_reader_phase`（plan 覆盖问题清单键，**Reader
  完成门早期拦截**，省算力）+ `questions_target_ids` 复用；(d) workflow.py Reader
  门接入；契约测试 +5（211 passed/4 skipped）。
- 价值：run3 是**失败即信息**——它实证了「软指引不可靠、必须硬门禁」。

## run4（2026-08-27）——BL-028 完整闭环：外部评分 C1-C3 真正计分 ✅

run4（`/tmp/harness/run-bench-220-20260827-192104`，归档 `bench-220-0026-run4/`
454M）带完整修复（Reader 门 + 强制 Questions Mapping）重跑：
- **验证点 A（Reader 门）**：plan.md 含 `Questions Mapping` 表，3 个问题清单键
  （blood-lead-cvd-hr/tibia-lead-cvd-hr/patella-lead-cvd-hr）逐字映射 T1-T3 → 通过。
- **验证点 B（Run 门）**：`05_run/answers.csv` 根目录 + target_id 逐字用清单键 +
  数值实算（svycoxph：1.6339/3.3246/2.4230，与论文一致）→ 通过。
- **外部评估闭环**：evaluate_run.py 首次 C1/C2/C3 **passed=True**——
  `paper=1.63 system=1.6339 within tol=0.05 OK（交叉核对通过）`，verdict
  REPRODUCED 100。对比 run2 的「REPRODUCED 但 C1-C3 全 NO-EVIDENCE」彻底修复。
- **副产品修复（commit f7043fd）**：evaluate_run.py 打包缺口——只拷
  answers/sha256sums/digests 没拷 answers 引用的 `05_run/results/`，导致交叉
  核对 `source_file 不存在`（run4 首次评估暴露）；已加 `results/` copytree
  + 端到端测试（212 passed/4 skipped）。
- **验收**：verify-0026-run.sh 19/19、契约测试 212 passed、归档路径评估通过。

### 监控方法教训（run2 补充）

- 阶段推进以 `container.log` 的 `[loopflow] Agent responded` / `[agent]` 行 + 产物目录
  出现为准；dind 镜像列表看拉取/构建进度；R 包编译期 dind CPU 500%+ 属正常。
- 验证脚本 `benchmarks/harness/verify-0026-run.sh`（run 根目录 + `repro-data/` 路径假设
  已修正）19 项契约检查可一键复验归档 run。

### 监控方法教训

container.log 无新行 ≠ 挂起：需用 `docker top` 看 claude 子进程树区分
「等待长命令」（bash/mip/docker pull 存活 = 正常）与「API 挂起」
（无子进程 + 会话文件停滞 + loop CPU 不增长 = 挂起）。两次误判：
mip pull 慢曾误判为挂起（有子进程实为正常）；此后用进程树判断才准确。


## run5（2026-08-28）——注入通道验证 ✅（端到端未完成，监控误判教训）

run5（`/tmp/harness/run-bench-220-20260828-103855`，归档 `bench-220-0026-run5/` 45M）
验证**问题清单注入通道**（commit 2808ab4 分层重构）：
- **注入段进入 agent prompt** ✅：claude 进程命令行含 `<run-append-prompt>` 段 +
  「任务公开问题清单」（288 字符，含 blood-lead-cvd-hr 等 3 键）——注入通道真实生效
- **plan.md Questions Mapping** ✅：含映射表 + 3 个清单键（注入驱动，非 reader.md 硬编码）
- **端到端未完成**：Provision 阶段 R 包构建反复失败重试（v1→v4，2.5h：p3m.dev
  网络抖动致 `withr`/`bit` 下载失败 + agent 生成的 R tryCatch 脚本语法 bug），
  未进入 Data 阶段

### 监控误判教训（重要——第三次）

本次把**正常工作的 Provision agent 误判为挂起并 kill**：
- 现象：container.log 2.5h 无新行 + claude 子进程只有 `sleep 120`
- 真相：agent 走 background-task 异步构建（R 包编译），主循环用 `sleep 120`
  轮询等待——`sleep 120` 是**轮询间隔**不是挂起；claude 会话文件持续写入
  （最后事件 05:17:45 UTC = 13:17:45 北京时间，我们 kill 前一刻仍在 thinking→Bash）
- 教训：**判断挂起的权威信号是 claude 会话文件停滞 + 无子进程 + CPU 平坦三合一**，
  不能只看 container.log 静默或子进程形态。`sleep N` 子进程在 background-task 轮询
  下是**正常**的（与 mip pull 的 bash 子进程同类）。Provision 阶段 R 环境构建
  可长达数小时（含失败重试），属正常挣扎，应容忍。

## run7（2026-08-28）——注入通道 + BL-029 修复后完整端到端 ✅ REPRODUCED 100

run7（`/tmp/harness/run-bench-220-20260828-144258`，归档 `bench-220-0026-run7/` 28M）
带全部修复（注入通道 2808ab4 + BL-029 技能挂载 8f233ab + 修正监控纪律）重跑，
**首个完整端到端成功的 run**（run5/6 分别卡在技能误报/直连被墙）：
- **注入通道**：plan.md Questions Mapping（3 清单键）+ answers.csv 用清单键
  （blood-lead-cvd-hr 等，非自造）——系统侧零文件名依赖全程成立
- **BL-029 修复验证**：`Skills are unavailable` 计数 0；Provision 用技能正常拉取
  rocker/r-ver:4.2.0 + 增量构建 lead-cvd-r-env:4.2.0（Hmisc 等全装上）
- **7 阶段全通**：01_plan→07_package + README/run.sh，verdict REPRODUCED
- **外部评估闭环**：evaluate_run.py C1/C2/C3 **passed=True**
  （paper=1.63 system=1.63 within tol=0.05 OK），score 100
- **契约 19/19**（verify-0026-run.sh）；routing.jsonl 6 行 reproduced/route_to=null
- **耗时**：~3.5h（Provision R 包增量构建为主，v1/v2 全量构建失败后 agent 正确转
  增量策略——交互安装+commit，纪律正确）

### 本轮三个环境修复串联（run5→run7）

| 修复 | 阻断 | 效果 |
|------|------|------|
| 注入通道（2808ab4） | reader/run.md 写死文件名 | 系统侧零文件名，清单走 --append-prompt |
| BL-029 技能挂载（8f233ab） | Skill 工具 Unknown skill → 直连被墙 | 技能可用，镜像经 mip 拉取 |
| 修正监控纪律（run5 教训） | 误判 background-task 轮询为挂起 | 三合一判断（session+子进程+CPU） |

## S2/BL-015：claim 策展完成 + oracle v2.0.0 冻结（2026-08-28）

用户指示「bench-220 run 正常则推进 S2」——run7 确认正常后执行：
- **17 个零 claims entry 数值 claims 落盘**（101 条，subagent 并行读 PMC/EuropePMC
  全文提取，每篇 3-6 条含出处/容差）；bench-207 剔除无效 C5（定性无数值）；
  bench-218/232 摘要级（paper_found=false），bench-232 付费墙跳过待人工
- **A1/A2 转诊断**（10/10）+ C1-Cn 平分 80；questions.yaml 同步公开清单键
- **oracle 全部升 v2.0.0** 并打 tag `oracle-v2.0.0` 冻结（S2 完成）
- 42/42 bundle 通过、218 tests 无回归、claims-rubric-questions 一致
- 工具：`benchmarks/converters/claroai/s2_apply_claims.py`（幂等落盘脚本）
- 冻结后跑批的 verdict 方构成可发布的复现率（S5 前置达成）
