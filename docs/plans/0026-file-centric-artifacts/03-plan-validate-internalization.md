# Plan 03 — Validate 内部化 + 动态路由 + goal 派生

依据：ADR-0011 §3/§4（FC-003/FC-006/FC-007）、BL-016 / BL-022；backlog 排序 S3。
前置：单元 01（harness）/ 02（Data 契约）done。

## 目标

把 Validate 从「对外评分者」改为**内部自反馈路由**，并让系统首次具备动态回环
能力；同时删掉 Data/Run goal 的 RNA-seq 硬编码（BL-016），把 Run 的结果契约推广
（Plan 02「做实物再推广」）。

## 分层边界（防返工）

- **本单元只改被测系统行为**：validate.md / run.md / workflow.py / loop.md /
  artifact_checks.py（Run 侧）
- **对外证据面切换（adapter 停读 metrics.json、converter 禁用 validate_report、
  46 个 check 重挂）属单元 04**——FC-006 的 adapter 测试部分在单元 04 落地。
  因此本单元**保留** report.md/metrics.json 生成（降级为内部记录），避免量具
  （evals component case）在证据面切换前断裂
- Validate 返回值 verdict 保留（内部 Package 门控，FC-006 允许内部用途），
  prompt 明确「不对外」

## 改动点

### 1. goal 从 plan.md 派生（BL-016）

- `workflow.py` 新增 `_section_text(plan_text, heading)` + `derive_goal(phase, plan_text)`：
  Data/Run 的 goal 从 plan.md 的 `Reproduction Target` / `Data Requirements` /
  `Analysis Steps` 段落搬运生成；**只搬运已有内容，不做论文语义判断**
  （通用信号原则）；解析失败回退注册表默认 goal
- `_phase(agent, name, common, goal=None)`：goal 可覆盖；`run()` 在 Reader 完成后
  读 plan.md，为 Data/Run 传派生 goal
- PHASES 注册表默认 goal 保留（单 agent eval 与解析失败时使用），把硬编码的
  RNA-seq 措辞改为「完整下载复现所需数据」「运行分析流水线复现论文目标」这类
  通用表述

### 2. Validate 内部化（ADR-0011 §3）

- `validate.md` 重构：
  - 职责改为「对比复现结果与论文声称 → 判定不达标目标应回到哪个 phase」，
    不再自称对外评分
  - **新增输出 `06_validate/routing.jsonl`**（追加式，一行一事件），键名白名单
    （FC-003 落实）：`ts / target / decision / route_to / reason`
  - 触发条件用通用信号（ADR §3 验证 4 修正）：实际执行代码/参数与 plan 声明
    不一致（如作者原始代码被 patch 且未声明）→ route_to=Run；数据不符→Data；
    环境/版本不符→Provision；论文理解错误→Reader
  - report.md / metrics.json 保留生成但标注**内部草稿**（不对外）
  - 返回值 verdict 保留（内部 Package 门控）

### 3. 回环机制 + 预算（FC-007）

- `loop.md` 新增 arg `routing_budget`（默认 0 = 线性不回环，保持现行为）；
  上限由调用方给定（benchmark envelope 按 deadline 派生），**系统内不写死**
- `workflow.py`：Validate 后读 routing.jsonl 取最后非空 route_to；非空且
  budget>0 时重跑该 phase 及其下游（Data→Run→Validate / Provision→Data→Run→
  Validate / Run→Validate / Reader→全链且跳过 confirm 门），每轮 budget-1，
  全部事件追加记录；耗尽或 route_to 为空即退出循环

### 4. Run 结果契约推广（Plan 02 策略）

- `run.md`：结果落 `05_run/results/`（CSV/TSV）+ `05_run/answers.csv`
  （`target_id,value,unit,source_file`，FC-003 无状态词/判断/理由）+ 命令执行日志
  （含退出码）
- `artifact_checks.py` 新增 `answers_parseable` / `run_phase_evidence` /
  `check_run_phase`；workflow 在 Run 后 `_require_parsable`
- answers 的**值定位交叉核对（FC-005）留单元 04**（crosscheck-prototype 为基础）

## 验收

| 项 | 判据 |
|----|------|
| goal 派生 | 有 plan.md（含 Data Requirements/Target 表）时 Data/Run goal 含该论文的资源/目标词；无 plan.md 回退默认 goal；注册表 goal 无 RNA-seq 措辞 |
| routing.jsonl 契约 | 键名白名单 `ts/target/decision/route_to/reason`；不含额外字段（lint 测试） |
| 回环 | fake agent 模拟 route_to=Run → 重跑 Run+Validate、预算递减、耗尽退出；route_to 空 → 不重跑；默认 budget=0 → 线性 |
| 预算来源 | `routing_budget` 只来自调用方参数；workflow.py 无硬编码回环次数 |
| Run 契约 | run.md 含 results/answers/命令日志规则；check_run_phase 抓「声称完成但无结果 CSV/answers」 |
| 回归 | 全套确定性测试全绿（166 + 新增）；evals component case 不因本单元断裂（量具冻结） |

## 风险

- Validate 语义变化可能影响 evals `validate-complete-result`（断言 report 含评分）：
  本单元保留 report/metrics 生成，故不破坏；若断言仍挂，属单元 04 证据面切换时
  更新量具的范畴，本单元不越权
- 回环重跑覆盖旧产物：显式日志记录；不依赖 loopflow 的 replay 作废（BL-003
  留 loopflow 方向）
- routing.jsonl 的 `reason` 字段与 FC-003 字面「不得含理由字段」冲突：ADR §3 明示
  字段含 reason，以 §3 为准；FC-003 落实为键名白名单，措辞修订留单元 05 文档同步
