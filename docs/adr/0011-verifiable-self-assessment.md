---
title: ADR-0011 — 文件为核心的产物契约与 Validate 内部化
description: 事实以标准格式文件持久化，禁止发明厚 schema；Validate 退为系统内部自反馈路由，不产出对外 verdict；外部评分证据面收缩到真实产物 + 极薄 answers 并强制交叉核对。
type: adr
status: accepted
created: 2026-08-22T00:00:00Z
---

# ADR-0011: 文件为核心的产物契约与 Validate 内部化

> **本文为第二稿（2026-08-22）。** 第一稿（"可验证的自我判定/诚实核算"）已废弃，
> 废弃原因记录在本文「被废弃的第一稿」一节——它是补丁式设计：为观测到的三个具体失败
> 各定一条规则并写入拍脑袋阈值（`attempts ≥ 2`、终态码白名单），且把契约压在
> agent 返回值（易失层）与自定义厚 schema 上。保留该记录以免同类错误重犯。

## 背景

BL-017 失败分类学（`benchmarks/calibration-failure-taxonomy.md`）显示：8 个「系统能力」
失败中 7 个是**声称与事实脱节**（bench-234 已从 GEO 下载 992 MB 却称需更好网络、
bench-232 把公开可下载数据判为需申请、bench-225 私自削减分析规模仍出 verdict、
19 run 交付的 `run.sh` 从未被执行）。

诊断这些失败时暴露出更根本的三个结构问题：

1. **事实载体是自由散文。** phase 之间靠 Markdown 交接（plan.md / provision.md /
   data_manifest.md / run_results.md），`workflow.py:94-100` 的 `_require_files` 只检查
   文件存在、不检查内容。下游只能靠正则猜测上游语义——`oracle/verify.py` 为此写了
   301 行中英关键词匹配。
2. **契约压在易失层。** loopflow 的 agent 返回值是进程内控制信号，跑完即失；7 个 agent
   中只有 validate.md 声明了 output schema（其余 6 个为 0，故 loopflow 的
   `validate_json` + `coerce_json` + 重试机制在 6/7 phase 上从未启用）。但真正被下游、
   benchmark 与用户消费的是磁盘上的文件，不是返回值。
3. **证据面被自评污染。** 全部 entry 的 rubric 中 `artifact_role: validate_report`
   出现 **46 次**（最多的一类，对比 provision_report 35 / data_manifest 35），
   adapter 还从 `06_validate/metrics.json` 读 verdict/score 并在缺失时回退解析
   `report.md`（`adapters/loopflow.py:450-470`）。即**外部评分的主干在读系统自己写的
   Validate 报告**，与 Spec 001 BR-002（不信任系统自评）直接冲突。

同时 Validate 当前的职责是错位的：它对外充当评分者（被 benchmark 读取），对内却只用于
给 Package 开门（`workflow.py:180-188`），**没有任何回环能力**——任一 phase 非 complete
即 `return None` 终止。

## 决策内容

### 1. 事实以文件持久化；返回值只保留最小控制信号

只有文件跨进程、跨重启、跨评估者存在。因此：

- 所有需要被下游/评估者/用户消费的事实，必须以文件形式落在 `NN_phase/` 目录
- agent 返回值只保留**内部控制信号**：validate 的单 key `verdict`（用于内部路由与
  Package 门控），其余 agent 不新增 output schema
- 废弃"给 6 个 agent 补 output schema"的方案（第一稿 F1）：那是在校验易失层

### 2. 优先既有标准格式，禁止发明厚 schema

判据：**该事实是否已有标准文件格式？有则必须用它；没有才允许自定义，且自定义压到最小。**

厚 schema 的害处不只是随需求腐化，更在于**字段越多，模型越倾向把表填满而非如实记录**
（第一稿的 `{status, bytes_received, bytes_expected, attempts:[...]}` 即此类错误）。

| 事实 | 承载格式 |
|------|---------|
| 数据是否到手、内容是否一致 | 数据文件本体 + `sha256sum` 输出文件（任何人可重算） |
| 数据获取失败发生了什么 | curl/wget 的**实际输出日志**（含 HTTP 响应与字节数），不是「不可获取」这个词 |
| 环境是什么 | `docker images --digests` 输出文件 |
| 分析结果 | 结果 CSV/TSV 本体 + 命令日志 + 图 PNG |
| 交付物可执行 | `run.sh` + 一次真实执行日志（含退出码） |
| 复现值与复现目标的对应 | `answers`（见 §4），仅 `claim_id → value` |
| 系统内部返工过程 | `routing.jsonl`（见 §3），一行一事件 |

允许的自定义格式**只有两类**：`answers` 与 `routing.jsonl`。二者都只记标识符与数值/事件，
**不含状态词、判断、理由**；理由写进散文报告，而散文报告不被任何程序消费。

#### 2.1 阶段整体阻塞时仍必须落尝试日志（验证 3 暴露后追加）

验证 3 发现：bench-217（论文 DOI 在 Crossref 真实 404）**没有 `04_data/` 目录**，其
「外部不可得」的唯一证据存在于 `container.log`——那是 harness 侧运行观测，不属交付
产物，外部评估者不应依赖它。因此：

- 即使某 phase 整体 blocked、无任何正常产物，**也必须在该 phase 目录落下尝试日志**
  （请求了什么、返回了什么）；否则该阻塞在证据面上等同「未尝试」
- 区分「未完成获取」与「外部不可得」依据**终态类别**而非尝试次数：传输层失败
  （`curl: (35) Recv failure`、超时、连接重置）属未完成；HTTP 404/403/451 与注册墙/
  DUA 属外部不可得；`Download complete` + 文件存在属已获取
- 系统内不得写死任何重试次数阈值（验证 3 证明按终态类别即可判定）

### 3. Validate 内部化：自反馈路由，不产出对外 verdict

- **输入**：`01_plan` 的复现目标 + Run 的真实产物（结果文件 + answers + 实际执行的代码）
- **触发条件用通用信号，不做论文特定判断**（验证 4 修正）：实际执行的代码/参数与声明
  不一致即触发，证据为**作者原始代码与实际执行代码的 diff**（bench-225 的
  `DiscRisk_1_train_patched.py` 即此类）。不试图自动判断「某参数是否属于缩减」——那需
  论文语义、无法通用化；只要求「改了必须声明，未声明即路由回 Run」
- **输出**：内部路由决策——不达标目标应回到哪个 phase（数据不符 → Data；环境/版本不符
  → Provision；参数或步骤不符 → Run；论文理解错误 → Reader），经 Validate 结果
  `payload.route_to` 返回（ADR-0058：workflow 用框架 `run_rerun_loop` 读 payload 做
  回环，不再读文件）
- **不产出对外 verdict**：对外 verdict 只能由外部独立 evaluator 给出
- **回环上限由调用方参数给定**（workflow 入参 / benchmark envelope 的 deadline 派生，
  `routing_budget`），**不在系统内写死数字**；耗尽即终止（ADR-0058：框架
  run_rerun_loop 返回 exhausted 如实记录）
- **routing.jsonl（可选交付记录，已不参与回环）**：如需对外交付路由轨迹可追加写入
  `06_validate/routing.jsonl`（FC-003 键名白名单：ts/target/decision/route_to/reason），
  但回环决策**仅来自 payload.route_to**——routing.jsonl 不再是机制依赖（ADR-0058
  迁移，2026-08-31）
- Package 门控继续消费 validate 的单 key verdict（内部用途，不进证据面）

这同时补上系统当前完全缺失的动态路由能力（`workflow.py:120-189` 为纯线性 fail-fast；
2026-08-31 迁移后由框架 `run_rerun_loop` 提供，见 ADR-0058）。

### 4. 证据面收缩：外部评分只读真实产物 + answers，并强制交叉核对

- 外部 evaluator 可读：Data / Provision / Run / Package 的标准格式产物（§2 表）+
  `05_run/answers.*`
- **`06_validate/` 整个目录不进证据面**；如需保留系统自评用于校准，只能作为
  `claimed_*` 观测单独记录，不参与任何 check 的打分
- `answers` 由**产生结果的阶段（Run）**落盘，不由 Validate 落盘
- **强制交叉核对**：answers 中每个值必须能在同一 run 的结果文件中定位到；定位失败则
  该 claim 不计分（不是判错，而是无证据）
- **系统产物中出现的"论文期望值"一律忽略**：验证中发现 bench-220 的
  `figures/figure_hr_comparison_data.csv` 含 `expected` 列（1.63/3.32/2.42，系统自己从
  论文读来的值）。oracle 只用自身 ground truth，不得消费产物里的任何期望值字段

#### 4.1 问题清单公开、期望值私有（验证 1 暴露后追加）

验证 1 发现原设计的漏洞：**claim id（C1/C2/C3）是 oracle 私有的，系统不可能知道**，
因此"系统落 `claim_id → value`"写不通；若改由 oracle 去结果文件里猜哪一行对应哪个 claim，
等于把 301 行正则换个位置重写。裁决：

- `input/questions.*`（**公开**）：`target_id` + 一句话问题 + 单位。这是任务的一部分
- `05_run/answers.*`（系统产出）：`target_id, value, unit, source_file`
- `oracle/claims.yaml`（**私有**）：论文期望值 + 容差 + 来源
- oracle 判分 = 比对 answers 的 value 与私有期望值，并核对该值存在于 answers 自述的
  `source_file` 中

代价（必须在论文 limitation 中声明）：公开问题清单**把"自行判断该报告哪些数值"从测量中
移除了**。换来的是评分无歧义与引擎中立——裸 agent 与开源 agent 用同一份问题清单，
各自的文件名/列名差异不影响评分。反之若坚持问题私有、由 oracle 用私有 locator 取值，
locator 会绑死被测系统的文件名与列名，baseline 一换即失效，benchmark 不再引擎无关。

### 5. 检查方式随之变薄

`_require_files` 升级为「存在 + 可被标准工具解析」，而**不是**校验自定义字段表：

```
04_data/        → sha256sum -c 通过
03_provision/   → digest 行可被 docker 解析
05_run/results/ → CSV 可被标准 csv 解析且非空
05_run/answers  → 每个值可在结果文件中定位
07_package/     → run.sh 执行日志存在且退出码为 0
```

系统内不留任何评分阈值。「重试几次算尽力」「偏差多少算复现」全部属于消费方
（oracle / 用户），可随 oracle 版本扫描并做敏感性分析。

## 候选方案与 trade-off

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 标准格式文件 + 两类极薄自定义 | 无需发明字段表；可被标准工具核验；正则解析自然消失 | 需重构 7 个 agent 的产物契约与 46 个 check 的证据源 | **采纳** |
| 自定义 state.json 厚 schema（第一稿） | 字段齐全、解析简单 | 随需求腐化；诱导模型填满而非如实记录；仍是系统自报 | 拒绝 |
| 给 6 个 agent 补 output schema（第一稿 F1） | 复用 loopflow 已有校验与重试 | 校验的是不持久化的返回值，下游消费不到 | 拒绝 |
| **answers 由系统落盘 + oracle 交叉核对**（采纳） | oracle 无需为 35 篇各写抽取代码；值可被结果文件反查 | 仍是系统自报数值，需依赖交叉核对约束 | **采纳** |
| 问题清单公开 + 期望值私有（采纳，见 §4.1） | 评分无歧义；引擎中立，baseline 可比；oracle 无需 per-entry locator | 把「自行判断该报告什么」从测量中移除，须在 limitation 声明 | **采纳** |
| oracle 侧从结果 CSV 自行抽取 | 证据面最纯粹，系统零自报 | 每 entry 一段私有抽取规则（35 篇 = 35 段）；且需规定 CSV 列名，等于换一种方式约束系统 | 拒绝（工作量差一个数量级） |
| 仅在 benchmark 侧扣分，不动系统 | 不动系统 | 只惩罚不修复；真实用户仍收到未经验证的交付物 | 拒绝 |

## 后果

### 正面

- 外部评分不再读系统自评，BR-002 从口号变为可检查的约束
- `oracle/verify.py` 的 301 行散文解析随证据面切换自然退役
- 系统获得动态路由能力，且返工过程持久化为文件证据
- Package 交付物首次具备可执行证明（落实 Spec 001 长期未实现的 run.sh smoke）
- FCR/UDR 一类指标可从文件直接计算，且对任意被测系统（含 baseline agent）同样适用

### 负面

- **46 个 check 需重挂证据源**，converter 需同步改造（生成 rubric 时禁用 validate_report）
- **已归档 35 个 run 大部分无 answers 与执行日志** → 不能用新口径重评，该批数据确定为
  pilot（与 BL-019 修正后的降级配置结论一致）
- 需要一个最小路径约定（如 `05_run/results/`、`05_run/answers.*`），这本身是对被测系统的
  约束，必须写入 Interface 并对所有被测系统一致适用
- 路由回环会放大耗时，与 deadline 冲突；回环预算必须显式声明并计入 envelope
- 标准格式只解决可核验，**不防伪造**（agent 可写假 CSV 与假日志）。防伪造需 harness 侧
  自动采集（命令审计 / 出口代理），属独立议题，本 ADR 不纳入、也不声称具备该能力

### 中立

- 与 BL-003（resume_from 阶段级重跑）合流：路由的落地形态取决于 loopflow 的 phase 重做
  机制，属实现细节

## 约束规则

| 规则编号 | 规则 | 检出方式 |
|----------|------|---------|
| FC-001 | 需被下游/评估者消费的事实必须落文件；agent 返回值仅允许 validate 的单 key verdict | 代码审查 + workflow 契约测试 |
| FC-002 | 已有标准格式的事实必须用标准格式；自定义格式仅限 `answers` 与 `routing.jsonl` | 代码审查 + entry/产物 lint |
| FC-003 | `answers` 与 `routing.jsonl` 使用键名白名单，不得含额外字段：answers 4 列 `target_id,value,unit,source_file`；routing.jsonl 5 键 `ts,target,decision,route_to,reason`（ADR-0058 修订：routing.jsonl 降级为可选交付记录，不参与回环；写了仍须合规） | schema lint（`artifact_checks.py: answers_parseable / routing_events_ok`）+ 契约测试 |
| FC-004 | `06_validate/` 不得作为任何 rubric check 的证据源（含 converter 生成路径） | bundle validator + converter 测试 |
| FC-005 | answers 中每个值必须可在结果文件中定位，否则该 claim 记为无证据、不计分；`value` 必须为**有限纯数值**（禁止单位/CI/括号——`1.63 (1.25–2.14)` 无法被数值交叉核对解析，2026-08-27 迁移 run 实证：CI 格式使 C1-C3 全部 NO-EVIDENCE；单位写 unit 列，CI 上下界放结果源表） | evaluator 交叉核对实现 + `artifact_checks.py: answers_parseable`（value 纯数值逐行校验）+ 单元测试 |
| FC-006 | Validate 不得产出对外 verdict；对外 verdict 仅来自独立 evaluator | 代码审查 + adapter 测试（禁止把 metrics.json 作为评分来源） |
| FC-007 | 回环上限必须来自调用方参数，系统内不得写死；耗尽须如实记录（ADR-0058：框架 run_rerun_loop 返回 exhausted，不掩盖） | 代码审查 + workflow 测试 |
| FC-008 | Package 声明 completed 必须有 run.sh 执行日志且退出码 0，否则 partial | workflow 出口检查 + 契约测试 |

## 验证

> **验证段已全部回填，2026-08-22 经人类确认 promote 为 accepted。**
> 全部验证项使用已归档 run 作 fixture，零新增算力。

| 验证项 | 复现步骤 | 预期结论 | 实际结论 |
|--------|---------|---------|---------|
| 现有产物能否支撑证据面切换 | 取 `runs/bench-220`（已知产出 table2_q91/tertile/ptrend、table3_paf CSV），尝试**只用 CSV** 复算 3 个 HR claims，不读 validate 报告 | 3 个 HR 可从 CSV 直接复算 → 证据面切换可行 | **通过（2026-08-22）**：`results/table2_q91_results.csv` 为规整结构化表（`group,outcome,exposure,hr,lower_ci,upper_ci,p_value`）。C1 血铅 CVD HR 论文 1.63 vs 实测 1.63390378426855（偏差 0.24%）、C2 胫骨铅 3.32 vs 3.32464221876738（0.14%）、C3 髌骨铅 2.42 vs 2.42303481511462（0.13%），均在 5% 相对容差内。**全程零正则、未读 validate 报告**。副产品发现两点：(a) claim id 私有导致 answers 无法以 claim_id 为键 → 追加 §4.1 裁决；(b) `figures/figure_hr_comparison_data.csv` 含系统自写的 `expected` 列，oracle 必须忽略 |
| 反例：无结果文件时不得得分 | 取 `runs/bench-203`（Run 阻塞） | claims 记为无证据、不计分，且不因报告里的文字而得分 | **通过（2026-08-22）**：`05_run/` 下仅 `run_results.md` 与 `main.nf`，**零结果文件**。散文里写着 `Status: BLOCKED` 与 9 个目标全 blocked，但新证据面不消费散文 → 其 1 条 LME p 值 claim 记为无证据、不计分 |
| `not_attempted` 与外部不可得可区分 | 取 `runs/bench-234`（同 run 已下 992MB，另 12 个数据集放弃）与 `runs/bench-217`（Crossref 真实 404） | 前者从 curl 日志判为未完成获取，后者判为外部不可得；**无需任何重试次数阈值** | **通过，但暴露新契约要求（2026-08-22）**：bench-234 的 `04_data/` 下**每个数据集一份下载日志**（`p4_gse*.log`）。成功者含逐字节进度 + `Download complete: … (248.6 MB)` + `ls -l`；放弃的 GSE136831 全文仅两行：`curl: (35) Recv failure: Connection reset by peer` 与 `bash: line 1: wget: command not found` → **传输层失败 + 回退工具不存在**，与 HTTP 403/404 权限墙属不同终态类别，**按终态类别即可区分，不需要重试次数**。另发现被计入「12 个放弃」的 GSE135893 实际已下载完成 4 个文件——散文 manifest 夸大了放弃范围。**bench-217 反例暴露缺口**：该 run 无 `04_data/` 目录，DOI 404 证据只存在于 `container.log`（harness 侧），phase 产物内为零 → 追加要求见 §2.1 |
| 参数缩减可被检出并触发路由 | 取 `runs/bench-225`（禁用 255 组合穷举） | 实际命令与 plan 声明不一致可检出，routing 目标为 Run | **通过，并修正触发条件（2026-08-22）**：证据在文件而非散文——实际执行脚本名为 `DiscRisk_1_train_patched.py`（系统 patch 过作者代码），其 `:674` 为 `evaluate_exhaustive(do_arch_search=False, …)`，而 `01_plan/plan.md:211` 记载「论文说明进行了穷举搜索」。但判定「`do_arch_search=False` 属缩减」需论文语义、不可通用自动化 → 触发条件改为通用信号：作者原始代码与实际执行代码存在 diff 而 plan 未声明（`_patched` 即此类），见 §3 |
| Package 执行证明的真实基线 | 对若干已归档 Package 产物在干净容器执行 `bash run.sh check` | 得到真实退出码（预期多数非 0，印证 19/26 无执行证据） | **通过，结果比预期更差（2026-08-22）**：35 个 run 中**仅 26 个存在 run.sh**（缺失 9 个：bench-202/203/204/205/206/213/217/218/232）。按体积分层抽 6 个（bench-200/201/215/216/219/230）在干净 `ubuntu:22.04` 容器实测 `run.sh check`（只读挂载 + 拷贝后执行，归档未被改动）：**退出码全为 1，0/6 通过**。首个失败原因全部是缺宿主依赖——java ×4、nextflow ×1、R ×1，其中 2 例显式报 docker/singularity 缺失。路径硬编码 0 例、脚本错误 0 例（check 分支写得正确，是主动 exit 1）。结论：交付包把整套运行时（Java/Nextflow/Docker/R）当作宿主既有环境，既不携带也不安装 → **README + run.sh 不构成自包含的一键重跑制品**。详见 `benchmarks/package-executability-probe.md`。局限：未测 `all` 分支，不能推断全流程可执行性；覆盖 6/26 为分层抽样非随机 |
| answers 交叉核对能拦住无据自报 | 构造 answers 含结果文件中不存在的值 | 该 claim 记为无证据、不计分 | **通过（2026-08-22）**：原型实测 5 例，核对规则**不含魔数**——容差由 value 自身书写精度导出（`0.5 × 10^-decimals`）：全精度 `1.63390378426855` 命中（容差 5e-15）、四舍五入 `3.325` 命中 3.32464…（容差 5e-4）、两位 `2.42` 命中 2.42303…（容差 5e-3）；伪造值 `2.99` 判 NO-EVIDENCE；source_file 不存在判 NO-EVIDENCE。**未覆盖**「值真实但标错来源文件」一例（本地只取了 table2 一个 CSV），实现时补 |

## 被废弃的第一稿

第一稿标题为「可验证的自我判定（诚实核算）」，决策为三条规则：R1 不可获取声称须带
evidence json 且 `attempts ≥ 2`、终态码限定白名单；R2 参数缩减打 not_comparable；
R3 Package 须有 smoke.json。废弃理由：

1. **补丁式**：三条规则一一对应当时恰好观测到的三个 case（bench-210/232/234、
   bench-225、19 run），第四类失败出现时无一条适用
2. **阈值拍脑袋**：`attempts ≥ 2` 与终态码白名单无任何依据，且阈值属评分策略，
   不应写入被测系统
3. **层次错误**：把契约压在 agent 返回值与自定义厚 schema 上，而持久化载体是文件
4. **未触及真问题**：当时未发现 46 个 check 读 validate_report——证据面被自评污染
   才是评分体系的主缺陷

保留本节的目的：这三类错误（点名 case 立规则、把评分阈值塞进系统、在易失层立契约）
是同一种思维惯性，后续设计需自查。
