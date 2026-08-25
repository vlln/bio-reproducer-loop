---
title: ADR-0011 — 文件为核心的产物契约与 Validate 内部化
description: 事实以标准格式文件持久化，禁止发明厚 schema；Validate 退为系统内部自反馈路由，不产出对外 verdict；外部评分证据面收缩到真实产物 + 极薄 answers 并强制交叉核对。
type: adr
status: proposed
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

### 3. Validate 内部化：自反馈路由，不产出对外 verdict

- **输入**：`01_plan` 的复现目标 + Run 的真实产物（结果文件 + answers）
- **输出**：内部路由决策——不达标目标应回到哪个 phase（数据不符 → Data；环境/版本不符
  → Provision；参数或步骤不符 → Run；论文理解错误 → Reader），以及追加式
  `06_validate/routing.jsonl`（字段：ts、target、判定、route_to、reason）
- **不产出对外 verdict**：对外 verdict 只能由外部独立 evaluator 给出
- **回环上限由调用方参数给定**（workflow 入参 / benchmark envelope 的 deadline 派生），
  **不在系统内写死数字**；耗尽即终止并如实记入 routing.jsonl
- Package 门控继续消费 validate 的单 key verdict（内部用途，不进证据面）

这同时补上系统当前完全缺失的动态路由能力（`workflow.py:120-189` 为纯线性 fail-fast）。

### 4. 证据面收缩：外部评分只读真实产物 + answers，并强制交叉核对

- 外部 evaluator 可读：Data / Provision / Run / Package 的标准格式产物（§2 表）+
  `05_run/answers.*`
- **`06_validate/` 整个目录不进证据面**；如需保留系统自评用于校准，只能作为
  `claimed_*` 观测单独记录，不参与任何 check 的打分
- `answers` 由**产生结果的阶段（Run）**落盘，不由 Validate 落盘
- **强制交叉核对**：answers 中每个值必须能在同一 run 的结果文件中定位到；定位失败则
  该 claim 不计分（不是判错，而是无证据）

选择让系统落 answers（而非 oracle 从 CSV 自行抽取）的理由见 trade-off 表。

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
| FC-003 | `answers` 与 `routing.jsonl` 不得含状态词、判断或理由字段 | schema lint（键名白名单） |
| FC-004 | `06_validate/` 不得作为任何 rubric check 的证据源（含 converter 生成路径） | bundle validator + converter 测试 |
| FC-005 | answers 中每个值必须可在结果文件中定位，否则该 claim 记为无证据、不计分 | evaluator 交叉核对实现 + 单元测试 |
| FC-006 | Validate 不得产出对外 verdict；对外 verdict 仅来自独立 evaluator | 代码审查 + adapter 测试（禁止把 metrics.json 作为评分来源） |
| FC-007 | 回环上限必须来自调用方参数，系统内不得写死；耗尽须记入 routing.jsonl | 代码审查 + workflow 测试 |
| FC-008 | Package 声明 completed 必须有 run.sh 执行日志且退出码 0，否则 partial | workflow 出口检查 + 契约测试 |

## 验证

> status=proposed。验证段回填后方可 promote 为 accepted（devloop DESIGN 门禁）。
> 全部验证项使用已归档 run 作 fixture，零新增算力。

| 验证项 | 复现步骤 | 预期结论 | 实际结论 |
|--------|---------|---------|---------|
| 现有产物能否支撑证据面切换 | 取 `runs/bench-220`（已知产出 table2_q91/tertile/ptrend、table3_paf CSV），尝试**只用 CSV** 复算 3 个 HR claims，不读 validate 报告 | 3 个 HR 可从 CSV 直接复算 → 证据面切换可行 | 待回填 |
| 反例：无结果文件时不得得分 | 取 `runs/bench-203`（Run 阻塞） | claims 记为无证据、不计分，且不因报告里的文字而得分 | 待回填 |
| `not_attempted` 与外部不可得可区分 | 取 `runs/bench-234`（同 run 已下 992MB，另 12 个数据集放弃）与 `runs/bench-217`（Crossref 真实 404） | 前者从 curl 日志判为未完成获取，后者判为外部不可得；**无需任何重试次数阈值** | 待回填 |
| 参数缩减可被检出并触发路由 | 取 `runs/bench-225`（禁用 255 组合穷举） | 实际命令与 plan 声明不一致可检出，routing 目标为 Run | 待回填 |
| Package 执行证明的真实基线 | 对若干已归档 Package 产物在干净容器执行 `bash run.sh check` | 得到真实退出码（预期多数非 0，印证 19/26 无执行证据） | 待回填 |
| answers 交叉核对能拦住无据自报 | 构造 answers 含结果文件中不存在的值 | 该 claim 记为无证据、不计分 | 待回填 |

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
