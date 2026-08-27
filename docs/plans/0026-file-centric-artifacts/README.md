# 0026 — 文件为核心的产物契约落地

> **接手请先读 [HANDOFF.md](HANDOFF.md)**（下一步、远端部署方式、已付代价的纪律、待人类决策项）。

依据：[ADR-0011](../../adr/0011-verifiable-self-assessment.md)（accepted，六项验证全部回填）
分支：`refactor/0026-file-centric-artifacts`（待创建）
定级：DESIGN 设计缺陷退回后的实现容器

## 背景一句话

35 篇批量跑完后的发布就绪审计发现：**量具与被测物同时在动**，且外部评分主干（46 个
check）在读系统自评。ADR-0011 决定事实以标准格式文件持久化、Validate 退回内部做自反馈
路由、外部评分只读真实产物。本容器落地该决策，并先修使数据不可信的基建缺陷。

## 执行顺序与依据

先修基建（否则任何验证跑出来的数据都不可信），再改产物契约（量具的输入），最后动
benchmark 侧证据面。系统行为改动一律成对跑（同子集 before/after）以直接产出 ablation 证据。

| 单元 | 内容 | 关联 backlog | 状态 |
|------|------|-------------|------|
| 01 | harness 修复：dind sidecar 架构（去 docker.sock）、Nextflow executor 修复、`curl -C -` 续传、前置探针 | BL-018 BL-019 BL-021 BL-024 | **done**，见 [Report 01](01-report-harness-fixes.md) |
| 02 | phase 产物契约改标准格式文件；`_require_files` 升级为「存在 + 可被标准工具解析」；阻塞时也落尝试日志 | BL-014 BL-021 | **done（Data phase 实物）**，见 [Report 02](02-report-artifact-contract.md)；死技能声明已清（BL-019 未闭项闭环） |
| 03 | Validate 内部化 + `routing.jsonl` + goal 从 plan.md 派生（删 RNA-seq 硬编码） | BL-016 BL-022 | **done**，见 [Report 03](03-report-validate-internalization.md)；回环预算 `routing_budget` 来自调用方参数（FC-007）；Run 结果契约（results/ + answers.csv）已推广 |
| 04 | 证据面切换：46 个 check 重挂 `result_table`+`answers`、converter 禁用 validate_report、adapter 停读 metrics.json、交叉核对实现 | BL-023 BL-015 | **done**，见 [Report 04](04-report-evidence-switch.md)；评分只读真实产物（answers/sha256sums/digests），NO-EVIDENCE 三态，42 entry bundle gate 全过；provision 契约（digests.txt）随 A2 推广 |
| 05 | 下游文档同步：Spec 001、Interface 0001/0002、AC 补场景（需人类再次 promote） | — | **done（待 promote）**，见 [Report 05](05-report-doc-sync.md)；Spec/Interface/AC 已退回 proposed，FC-003 措辞已修订 |
| 06 | 交付包自包含：Package 出口以干净容器 `run.sh check` 通过为准 | BL-025 | pending |

## 不做什么

- 不做 harness 侧命令审计 / 出口代理抓包（防伪造属独立议题，ADR-0011 明确不纳入）
- 不重跑 35 篇正式批次（量具冻结前跑批即返工；该批已定性为 pilot 数据）
- 不新增 claims 策展（属 benchmark 侧独立工作，等证据面切换完成后再排）

## 完成判据

1. 单元 01-04 各自的验收项通过，且 141 个既有确定性测试保持全绿
2. ADR-0011 的 FC-001~FC-008 每条都有对应检出手段落地（非口头承诺）
3. 一个 entry 端到端跑通新契约：产物为标准格式、evaluator 不读 `06_validate/` 即可判分
