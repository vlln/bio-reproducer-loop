# 交接说明（0026 容器）

> 写给接手的 agent。**只凭文件即可恢复状态**，不要依赖任何对话历史。
> 最后更新：2026-08-27（单元 01 完成后）

## 先读这些（按序）

1. `docs/README.md` —— 当前阶段（`DESIGN`，设计缺陷退回）与退回定级依据
2. `docs/backlog.md` —— BL-014~BL-026 是本轮全部工程债；**文件末尾有防返工排序（S0-S5）与人类已作决策**
3. `docs/adr/0011-verifiable-self-assessment.md` —— accepted，本容器的唯一设计依据；
   **文末「被废弃的第一稿」记录了三类必须避免的思维惯性**
4. 本容器 `README.md`（单元表 + 状态）→ `01-report-harness-fixes.md`（已完成的实测结论）
5. `benchmarks/calibration-failure-taxonomy.md`、`benchmarks/package-executability-probe.md` —— 35 run 的实测事实基础

## 立刻可以开始的下一步：单元 02

**先只改 Data 一个 phase，做出实物再推广**（Plan 02 已写明范围与验收）：

1. `agents/data.md`：状态词表拆 `completed / partial / unavailable / not_attempted`；
   要求落 `sha256sum` 输出 + **每资源一份获取日志**；阻塞时也必须落日志（ADR-0011 §2.1）
2. 下载纪律写进 prompt：统一 `curl -C -` 续传（已实测 NCBI 返回 206；`wget`/`aria2c` 镜像内没有，
   **不要去装 wget**）
3. `workflow.py`：`_require_files` → 「存在 + 可被标准工具解析」
4. `tests/contract/` 补用例，正反例用已归档 run：
   - `runs/bench-234/repro-data/04_data/p4_gse136831.log`（两行：`curl: (35)` + `wget: command not found`）→ 应判 `not_attempted`
   - 同 run `p4_gse289881.log`（`Download complete … (248.6 MB)`）→ 应判 `completed`
   - `runs/bench-217`（无 `04_data` 目录）→ 应判「无证据」，不得判外部不可得
5. **顺手清掉死技能声明**（单元 01 遗留的唯一未闭项，人类未提供来源，按 Plan 01 纪律执行）：
   从 `agents/reader.md` 的 `skills:` 移除 `paperutils` 与 `mineru-api`，改为要求 Reader 直调
   Crossref / EuropePMC（探针已证可达）。理由：两者声明的前置在任何机器上都不存在，
   保留声明等于每次 run 先撞墙再兜底，并把基建缺失伪装成能力缺失

## 远端与脚本部署（必读，否则会白跑）

- 远端：`ssh gs@172.16.209.237`（免密）。**不要用 rex 脚本**（`extra_opts[@]` unbound 变量 bug）
- 仓库内的 harness 脚本**不会自动出现在远端**，用前先 `scp`：
  ```bash
  scp benchmarks/harness/run-entry.sh benchmarks/harness-probe.sh gs@172.16.209.237:/tmp/
  ssh gs@172.16.209.237 'bash /tmp/run-entry.sh selftest'      # 六项边界自检，应 6/6
  ssh gs@172.16.209.237 'bash /tmp/harness-probe.sh'           # 前置探针，当前应报未满足 2 项
  ```
- **新 run 一律用 `run-entry.sh`，不要再用远端 `bench-v3.sh`**（后者挂 docker.sock，违反 ADR-0009，
  且是 Nextflow 挂载失败的根因）
- 归档 run 在 `/storeData/gs/claroai-calibration/runs/bench-2NN/repro-data/`；`*-legacy-*` 忽略

## 纪律（违反过，代价已付）

1. **任何「网络坏了 / 技能坏了 / 数据拿不到」的判断，必须先跑 `harness-probe.sh` 实测**。
   BL-019 因为跳过实测被误诊两次（先怪技能注入，再怪出口网络），两次都是拿单行日志当根因
2. **不要拍阈值**（重试几次、偏差多少算复现）：阈值属评分策略，归 oracle，系统内一个魔数都不留
3. **不要发明厚 schema**：已有标准格式的事实必须用标准格式；自定义只允许 `answers` 与
   `routing.jsonl`，且不含状态词/判断/理由
4. **不要在量具冻结前跑批**：35 run 已因此返工一次（跑完 oracle 还在改 → 离线重评、claim 被覆盖丢失）
5. **不要 push**（人类明确要求）；commit 照常
6. 系统改动要成对跑（同子集 before/after），使改动自动成为 ablation 证据

## 已完成但未部署 / 未验证的部分

- `run-entry.sh` **只跑过 selftest，没跑过完整 entry**。首次实跑安排在单元 02 契约改造之后
  （否则用旧契约跑一遍还要再跑一遍）
- 远端 `bench-v3.sh` 暂留，等 `run-entry.sh` 跑通完整 entry 后再删
- `benchmarks/harness/crosscheck-prototype.py` 是 ADR-0011 验证 6 的原型（容差由书写精度导出，
  无魔数），单元 04 实现 evaluator 交叉核对时以它为基础；同目录 `answers.csv` +
  `table2_q91_results.csv` 是可直接复跑的样例：`python3 crosscheck-prototype.py answers.csv .`
  应得 3 PASS / 2 NO-EVIDENCE

## 待人类决策（不要自己拍）

1. **Spec 001 / Interface 0001+0002 / AC 的修订 promote**（单元 05）：不可委托门禁，改完给简报
2. qemu 安装：人类已认领，但**只影响可发布正式结果**（ADR-0009/BR-013），不阻塞本容器任何单元
3. `paperutils` CLI 与 MinerU 端点是否存在：已按纪律默认「不存在 → 移除声明」，若人类提供来源则改为补齐
