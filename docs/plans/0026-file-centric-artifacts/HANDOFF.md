# 交接说明（0026 容器）

> 写给接手的 agent。**只凭文件即可恢复状态**，不要依赖任何对话历史。
> 最后更新：2026-08-27（单元 03 完成后）

## 先读这些（按序）

1. `docs/README.md` —— 当前阶段（`DESIGN`，设计缺陷退回）与退回定级依据
2. `docs/backlog.md` —— BL-014~BL-026 是本轮全部工程债；**文件末尾有防返工排序（S0-S5）与人类已作决策**
3. `docs/adr/0011-verifiable-self-assessment.md` —— accepted，本容器的唯一设计依据；
   **文末「被废弃的第一稿」记录了三类必须避免的思维惯性**
4. 本容器 `README.md`（单元表 + 状态）→ `01-report-harness-fixes.md`（单元 01）→
   `02-report-artifact-contract.md`（单元 02，Data 契约）→
   `03-report-validate-internalization.md`（单元 03，Validate 内部化 + 回环）
5. `benchmarks/calibration-failure-taxonomy.md`、`benchmarks/package-executability-probe.md` —— 35 run 的实测事实基础

## 立刻可以开始的下一步：单元 04

证据面切换（BL-023/BL-015，Plan 04 未写，先读 ADR-0011 §4/§4.1/§5 与 BL-023 再写 Plan）：

1. **46 个 rubric check 重挂证据源**：把 `artifact_role: validate_report`（46 次）重挂到
   `result_table` + `answers`；converter 生成 rubric 时禁用 validate_report（FC-004）
2. **adapter 停读 metrics.json**：`benchmarks/runner/adapters/loopflow.py:450-470` 的
   verdict/score 回退路径删除（FC-006）；`06_validate/` 整目录移出证据面
3. **answers 交叉核对实现（FC-005）**：以 `benchmarks/harness/crosscheck-prototype.py`
   为基础（容差由书写精度导出，无魔数），补「值真实但标错 source_file」反例
   （ADR-0011 验证 6 已标记未覆盖）
4. **`oracle/verify.py` 301 行散文解析退役标记**：随证据面切换自然退役
5. **benchmark adapter 透传 `routing_budget`**：从 envelope deadline 派生传入
   （单元 03 已就绪，只差调用方）
6. 系统侧已就绪的输入：`05_run/answers.csv`（表头白名单）、`05_run/results/`、
   `06_validate/routing.jsonl`（键名白名单）——新契约的 fixture 与 lint 在
   `tests/contract/`，直接复用

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

- `run-entry.sh` **只跑过 selftest，没跑过完整 entry**。首次实跑安排在单元 04 证据面
  切换之后（单元 02/03 已改产物契约，新 run 直接产出新契约产物）
- 远端 `bench-v3.sh` 暂留，等 `run-entry.sh` 跑通完整 entry 后再删
- `benchmarks/harness/crosscheck-prototype.py` 是 ADR-0011 验证 6 的原型（容差由书写精度导出，
  无魔数），单元 04 实现 evaluator 交叉核对时以它为基础；同目录 `answers.csv` +
  `table2_q91_results.csv` 是可直接复跑的样例：`python3 crosscheck-prototype.py answers.csv .`
  应得 3 PASS / 2 NO-EVIDENCE

## 待人类决策（不要自己拍）

1. **Spec 001 / Interface 0001+0002 / AC 的修订 promote**（单元 05）：不可委托门禁，改完给简报
2. qemu 安装：人类已认领，但**只影响可发布正式结果**（ADR-0009/BR-013），不阻塞本容器任何单元
3. `paperutils` CLI 与 MinerU 端点：已闭环（单元 02，移除声明）；若人类日后提供来源可重新引入
