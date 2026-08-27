# Report 03 — Validate 内部化 + 动态路由 + goal 派生

对应 [Plan 03](03-plan-validate-internalization.md)。依据 ADR-0011 §3/§4（FC-003/FC-006/
FC-007）、BL-016/BL-022。

## 交付物

| 文件 | 改动 |
|------|------|
| `loops/bio-reproducer/workflow.py` | `_section_text`/`derive_goal`（Data/Run goal 从 plan.md 派生，删 RNA-seq 硬编码）；`_execute_sequence`（顺序执行 + 前置检查 + goal 覆盖 + Data/Run 契约检查）；Validate 后回环循环（`_read_routing`/`_routing_route`，路由链 `ROUTE_CHAINS`）；预算 `routing_budget` 只来自调用方参数 |
| `loops/bio-reproducer/agents/validate.md` | 职责从「对外评分者」→「内部自反馈路由」：不产出对外 verdict（内部自评仅供 Package 门控与路由参考）；新增 `06_validate/routing.jsonl` 契约（追加式，键名白名单 ts/target/decision/route_to/reason）；触发条件用通用信号（实际执行与声明不一致且未声明 → 路由，如 `*_patched.py`）；report.md/metrics.json 保留生成但标注内部草稿 |
| `loops/bio-reproducer/agents/run.md` | 结果契约：`results/` CSV/TSV + `answers.csv`（target_id,value,unit,source_file，FC-003）+ `reports/commands.log`（命令+退出码）；修改作者代码必须声明（防 BL-022 类未声明缩减） |
| `loops/bio-reproducer/artifact_checks.py` | `answers_parseable`（表头精确白名单）+ `run_phase_evidence`/`check_run_phase`（05_run「存在+可解析」）+ `routing_events_ok`（FC-003 键名白名单 lint） |
| `loops/bio-reproducer/loop.md` | 新增 arg `routing_budget`（默认 0 = 线性不回环；上限由调用方给定） |
| `tests/unit/test_loop_workflow.py` | +9 用例：goal 派生（有段落/无段落/注册表无硬编码）、回环（Run/Data/Reader 链、预算耗尽、未知路由、budget=0 线性）、prompt 契约断言 |
| `tests/contract/test_run_phase_contract.py` | 新增 12 用例：answers 表头白名单、check_run_phase 四态、routing 键名 lint |

## 验收结果（对照 Plan 03）

| 项 | 判据 | 结果 |
|----|------|------|
| goal 派生 | 有 plan.md 段落时 goal 含该论文内容；无则回退默认；注册表无 RNA-seq 硬编码 | ✅ `PLAN_WITH_TARGETS`（NHANES 血铅 HR）→ Data goal 含 NHANES、Run goal 含 血铅/T1；无段落回退注册表默认；注册表 goal 无 RNA-Seq/FASTQ |
| routing.jsonl 契约 | 键名白名单，无额外字段 | ✅ `routing_events_ok`：合法 5 键通过；额外键/缺键/非 dict 拒绝（FC-003 lint 测试） |
| 回环 | route_to=Run 重跑 Run+Validate；预算递减；耗尽退出；未知路由终止；默认线性 | ✅ 6 个回环用例全过（含 Reader 全链重跑且不重触发 confirm 门） |
| 预算来源 | 只来自调用方参数；系统内无硬编码回环次数 | ✅ `routing_budget` 来自 args；workflow.py 无回环次数常量 |
| Run 契约 | run.md 含 results/answers/命令日志规则；check_run_phase 抓幻觉完成 | ✅ 12 个 contract 用例；prompt 内容断言 |
| 回归 | 全套确定性测试全绿 | ✅ **190 passed / 4 skipped**（166 → 190，+24 用例） |

## 关键设计决策（留档）

1. **`_routing_route` 取「最后一个事件」而非「最后一个非空 route_to」**。routing.jsonl
   是追加式，回环后旧事件仍在；取最后一个非空会读到上一轮的旧路由导致无限回环。
   最近一次 Validate 的 route_to 才是当前决策（null 即终止）。实测抓出：初版实现
   （取最后非空）在 Data 回环测试中死循环，测试先行暴露。
2. **routing.jsonl 的 `reason` 字段与 FC-003 字面「不得含理由字段」冲突**：ADR §3
   明示字段含 reason（触发路由的事实证据），以 §3 为准；FC-003 落实为**键名白名单**
   （只允许 5 键、不得加评分/状态字段）。FC-003 措辞修订留单元 05 文档同步。
3. **answers 表头精确白名单**（`set(cols) == set(ANSWERS_COLUMNS)`）：FC-003 的
   「不得含状态词/判断/理由」落实为含额外列即违规，而非仅「缺列违规」。
4. **分层边界（防返工）**：单元 03 保留 report.md/metrics.json 生成（标注内部草稿），
   不破坏 evals 量具（`validate-complete-result` 断言 metrics.json 字段）；「外部不读
   validate」的 adapter/converter 改动严格留单元 04。
5. **goal 派生只搬运、不判断**：`_section_text` 只按标题摘段落，`derive_goal` 把段落
   塞进通用模板；解析失败回退注册表默认 goal（不 fail）。摘取长度护栏 500 字符
   （非评分阈值，工程护栏）。
6. **回环重跑覆盖旧产物**：显式日志（`Validate 路由回 X（回环预算剩余 N）`）；不依赖
   loopflow 的 replay 作废（BL-003 留 loopflow 方向）。

## 未做 / 移交

- **真实 LLM 成对跑（before/after ablation）**：按纪律须在量具冻结（S2）之后执行，
  与 BL-016 的 ablation 一并排期；本单元用确定性测试（fake agent + prompt 内容断言）
  覆盖行为契约，真实 run 行为对比不属本单元（量具未冻结，跑即返工）
- **`06_validate/` 移出证据面**（adapter 停读 metrics.json、converter 禁用
  validate_report、46 个 check 重挂 result_table+answers）→ 单元 04
- **answers 值定位交叉核对（FC-005）**→ 单元 04（crosscheck-prototype.py 为基础）
- **FC-003 措辞修订**（routing.jsonl 键名白名单化）→ 单元 05 文档同步
- **benchmark adapter 透传 `routing_budget`**（从 envelope deadline 派生）→ 单元 04
