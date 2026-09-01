# ClaroAI 校准资产索引（BL-013）

> 防遗忘与无法复用：远端/本地产出必须落在固定位置并登记索引。
> 远端持久资产区：`/storeData/gs/claroai-calibration/`（runs/{bench-NNN}/、scripts/、system/）。
> 临时运行区：`/tmp/bl012/`（重启即失，完成后必须移出）。

## Plan 0025：第一批其余 5 篇 claims 模式重跑（2026-08-17/18，bench-229 待补）

> 新自然语言 task 下正式重跑（bench-220 已先行，REPRODUCED 100）。旧 run 均存
> `runs/bench-NNN-legacy-*`。verdict 为独立 evaluator 结果（claims oracle 自动解析）。
> bench-229 首次重跑两次幽灵进程挂起（Run 阶段 6.5h、Package 阶段 10.5h 无响应），
> 评分工件完成后手动评估归档；LLM 长会话无超时为系统级遗留缺陷。

| entry | 耗时 | 系统自评 | **独立 verdict** | 作者 D5 | 关键失败/发现 |
|-------|------|----------|-----------------|---------|--------------|
| bench-200 | ~1h15m | PARTIAL | **FAILED 0** | 2 | Fig4A DEG 复现 163/23 vs 论文 599/1390（**未检测 GEO 标签互换**——作者 agent 曾修正；真实复现缺陷）；A1 因作者 D2=0 低估冲突 |
| bench-203 | ~2h38m | BLOCKED | **PARTIAL 30** | 2 | LME p 值 claim 未复现（run 阻塞，MRI 数据环境问题） |
| bench-221 | ~1h35m | REPRODUCED | **REPRODUCED 76.25** | 2 | 8 个 HR claims 复现 7 个；hei.2015 cancer HR 0.88 vs 0.83 超容差；A2 NCHS 链接无判断 |
| bench-222 | ~2h25m | REPRODUCED | **REPRODUCED 100** | 2 | 无数值 claims（scores.json 无 D5 evidence），仅 D1–D3 证据可评 |
| bench-223 | ~9h | REPRODUCED | **REPRODUCED 85** | 2 | AUROC≥0.95 复现通过（0.992 vs 作者 0.992）；A1 数据引用判断失败；scMKL 计算重（9h） |
| bench-229 | 05:02→08:54（评分工件） | REPRODUCED 87.6 | **PARTIAL 32.5** | 1 | multi 计数 57491 精确复现 ✓；ATAC/RNA/spatial 因 KPMP 注册限制未复现；A1 对 KPMP UUID/Zenodo 无判断；Package 阶段幽灵进程挂起 |

**Provision 越界观察**（对照审计时代）：全部合理——bench-200 复用 deseq2-analysis:bench001
增量 7 包、bench-221 复用 nhanes-fi-ca-mortality:r4.3.3（论文同名镜像，零构建）、bench-223
全复用 scmkl-provision:0.1.6、bench-203 仅建 MRtrix3+Python 聚焦环境、bench-229 复用
p4rkerw/sctools。**无现成镜像场景（203）亦未越界装全套**；审计时代的"provision 建全量
分析环境"问题未复现。

**校准发现**（claims 维度）：bench-200 系统复现 DEG 数 163/23 vs 论文 599/1390——独立
验证显示作者 agent 修正了 GEO 标签互换而本系统未检测，属真实复现缺陷（D5 层面）；
bench-221 的 8 项 HR 中 7 项精确复现。作者 D5=2 的评分在 bench-200/203 与系统实际表现
不一致（作者高估或系统缺陷，双向可能，符合校准双向发现原则）。

## 批量校准脚本（远端）

- ~~`bench-v3.sh`~~：**已删除（2026-08-27）**，被 `harness/run-entry.sh` 取代
  （dind sidecar 隔离 + 不挂宿主 socket + registry-mirror 透传，见下文资产表）。
  原实现：docker 模拟 VM 边界跑 loopflow 全链路（时间戳目录，`bash bench-v3.sh <entry>`），
  挂载 `/var/run/docker.sock` 违反 ADR-0009，废弃；备份在
  `/storeData/gs/claroai-calibration/scripts/archive-bench-v3-20260827/`
- ~~`watch.sh` / `run-with-watchdog.sh`~~：**已删除（2026-08-27）**，bench-v3.sh 体系的
  完成检测/看门狗，随之上移除；备份同上
- `evaluate_run.py`（本文件所在仓库）：评估已完成 run

## 已完成校准（第一批，D2=2&D3=2 六篇）

| entry | 论文 | 系统 verdict | evaluator | 作者 cal | 完整产物 | 备注 |
|-------|------|-------------|-----------|----------|----------|------|
| bench-220 | SciTotalEnv epi | REPRODUCED 100（重跑确认） | REPRODUCED 100 | D1=2/D2=2/D3=2 | 已归档 ✓ | ✅ 一致 |
| bench-222 | TorchXRayVision | PARTIAL（重跑，图像网络限制） | REPRODUCED 100 | D1=2/D2=2/D3=2 | 已归档 ✓（重跑补回） | 元数据审计与作者一致；系统因图像数据网络限制自评 PARTIAL |
| bench-200 | HDM 多组学 | REPRODUCED（重跑；首次 BLOCKED 因参考基因组下载中断） | FAILED 0 | D1=2/D2=0/D3=1 | 已归档 ✓（重跑补回） | **校准发现**：重跑系统成功下载数据 → 与作者 D2=0 分歧（作者工具限制判不可下载，数据实际可获取——作者 D2 低估）；代码不完整判断与 D3=1 一致 |
| bench-203 | MRI diffusion | REPRODUCED 100 | REPRODUCED 100 | D1=2/D2=2/D3=2 | 已归档 ✓ | |
| bench-221 | Cancer Control | REPRODUCED 100 | REPRODUCED 100 | D1=2/D2=2/D3=2 | 已归档 ✓ | 首次 run 失败后重启 |
| bench-223 | Comm Biol | BLOCKED | — | D1=2/D2=2/D3=2 | 已归档 ✓ | scMKL alpha=1.0 代码 bug（作者 D3=2 高评 vs 实际 bug） |
| bench-229 | Genome Biol | BLOCKED | PARTIAL 50 | D1=2/D2=2/D3=2 | 已归档 ✓ | **修正**：GSE220289"无处理矩阵"为 **agent 误报**（GEO 独立验证有 19 个处理矩阵文件，45.6GB）；KPMP 下载需注册待验证；GEO SSL 为系统网络限制 |

**第一批全部闭环（7 run 全归档）**。结论：作者 D1-D3 元数据评分大体可靠（元数据判断多数与作者一致）；
系统 verdict 差异根因逐篇为：系统网络/参数路径（bench-200/223）+ 论文真实限制（bench-229/223-SLL）；
bench-223 重跑暴露复现偏差（scMKL 未超基线，属 D5 层面）；bench-200 显示作者 D2 可能低估。

**校准双向发现**：bench-200 重跑显示作者 D2=0 低估（数据实际可下载，作者工具链限制导致判不可下载）；bench-223 显示系统 alpha 参数路径问题（非论文 bug）——作者评分与确定性评分的差异**双向都有**，不能单向归因"作者高估"。

## Plan 0025：claims 模式离线重评（修正审计模式高估）

> 2026-08-12：converter v0.2.0 起 ClaroAI entry 为 claims 模式（D5 数值声明 + 容差
> 评分，D1–D3 为辅助证据）；`scored_scope`/审计模式已删除。以下对同一批归档 run
> （证据文件：data_manifest/provision/06_validate report，未重跑）用 claims oracle
> 离线重评的结果，**取代**上表旧 verdict 作为校准观测（bench-220/221 的 claims
> evidence 从 validate 报告逐条手工映射，见 Report 025）：

| entry | claims 模式 verdict | 旧（审计模式）verdict | 作者 D5 | 解读 |
|-------|---------------------|----------------------|---------|------|
| bench-220 | REPRODUCED 100 | REPRODUCED 100 | 2 | 3 个 HR claims 全部匹配 ✓ |
| bench-221 | REPRODUCED 65 | REPRODUCED 100 | 2 | 8 个 claims 复现 4 个（fs_enet/pc2 × 全因/癌症）；旧评分高估 |
| bench-222 | REPRODUCED 100（无数值 claims） | REPRODUCED 100 | 2 | paper_23 scores.json 无 D5 evidence；仅 D1–D3 证据可评 |
| bench-203 | PARTIAL 30 | REPRODUCED 100 | 2 | LME p 值 claim 未复现 |
| bench-200 | FAILED 0 | REPRODUCED 90 | 2 | Fig4A DEG claims 未复现；作者 D2=0 低估仍致 A1 失败 |
| bench-223 | FAILED 15 | BLOCKED | 2 | AUROC claim 未复现（scMKL 阻塞） |
| bench-229 | FAILED 15 | BLOCKED | 1 | barcode count claims 未复现 |

结论：审计模式的 verdict 系统性高估可复现性；claims 模式把"未复现论文定量声明"如实
记为 FAILED/PARTIAL。作者 D5 与系统 claims 复现的差异（bench-200/203/223 作者 D5=2
而系统未复现）属校准双向发现，与 bench-200 D2 低估同类。

## Plan 0025：bench-220 claims 模式正式重跑（端到端验证，2026-08-17）

**目的**：验证"新任务说明（metadata.task 自然语言）→ 系统执行 → claims 复现 → 自动
解析评分"完整链路（此前离线重评只验证了旧产物 vs 新评分体系）。

| 项 | 值 |
|----|-----|
| run | `/storeData/gs/claroai-calibration/runs/bench-220`（旧 run 存 `bench-220-legacy-2026-08-07-20-17-39`） |
| 总耗时 | **~1 小时**（Reader 18m + Provision 7m + Data 12m + Run 20m + Validate 3m + Package）vs 上次 8h23m（**8 倍提速**：provision 复用已有镜像，不再越界建全量环境） |
| 任务解读 | plan.md Reproduction Target = T1–T3 三个 HR claims（1.63/3.32/2.42）+ T4–T10 数据/代码核查，out-of-scope 声明明确——`d1_d3_audit` 误读不再发生 |
| 系统执行 | Run 产出 Table 2/3 真实结果（table2_q91/tertile/ptrend、table3_paf csv） |
| claims 复现 | validate 报告 R1–R6 六项 HR 精确匹配（血铅 1.633903784 vs 1.63，6 位小数一致），PAF 三项偏差 ≤0.9pp |
| **claims oracle 评估** | **REPRODUCED 100**（5/5 checks：A1/A2 + C1–C3 全部 PASS，自动解析 validate 报告，无手工映射） |
| 作者校准对照 | 作者 D5=2 → 系统 REPRODUCED 100，**完全一致** ✓ |

验证结论：claims 模式端到端链路成立——自然语言任务被正确解读、系统真实复现论文定量
声明、独立评估自动评分。耗时从 8h23m 降至 ~1h，证明 scope 语义修复同时消除了越界重活。

**过程教训**（本地流程）：容器以 uid 1000 运行，run 目录子目录（01_plan/.git 等）为
1000 属主 755 权限，gs 无法清理/移动其内文件——本次归档后 tmp 残留重复副本无法删除
（/tmp 重启即失，无碍）。**后续基准：run 完成归档前先 `chmod -R a+rX`（或容器内收尾）**，
否则 mv 跨设备会部分失败。

## P1-1：claims fidelity review（2026-08-18）

对 35 篇 claims.yaml 与 claroai scores.json D5 evidence 的交叉审计：
- 审计发现 16 篇有转录缺口；修复 converter 3 类格式缺失（pub 值带 % 后缀、
  "vs published" 格式、 "verified=" 格式）+ 噪声行过滤（outputs=/exit_code=）
- claims 总数 22 → 29；bench-231 手工补 2 条阈值 claims（论文声称精度 >90%，
  复现 KNN-5 98.3% / 线性探针 96.7%）
- 剩余 6 篇发现均为误报或非数值声明：bench-213/220/221 样本量注记（非关键声明）、
  bench-223 AUROC 作者复现值（claim 已存在，审计误报）、bench-229 GMM 定性行
- 验证：141 passed，42 entry 全过 bundle gate（commit 1f45613）

## P1-2：4 篇无 D5 evidence 论文 claims 补全（2026-08-18）

bench-208/209/222/225 的 scores.json 无 D5 evidence，从论文作者复现产物提取数值声明：
- bench-208（VDAC isoforms）3 条：VDAC1/2/3 比例（论文 Fig1A 50%/30%/18% vs 作者复现 57.6/30.9/11.5）
- bench-209（EpiFlow）4 条：Mann-Whitney U、p=1.83e-9、H3K9ac/H3K27ac Pearson r（0.41/0.42）
- bench-222（TorchXRayVision）5 条：DenseNet121/ResNet50 参数量 + 3 个 AUROC（0.88/0.91/0.94）
- bench-225（NN ensembles）2 条：集成 AUROC 75.1%、BMI-only 64.2%
全部 entry 通过 bundle gate（141 tests passed），claims 与作者复现校准一致（commit f84ab7d）。
至此 35 篇全部有可评分的 claims（其余 31 篇来自 converter 转录 + bench-223/231 手工补）。

## P2 批次 v1 故障与看门狗 v2（2026-08-19/20）

35 篇批量首日暴露**看门狗误杀**：以 container.log 静默 2.5h 为挂起信号，但重计算 entry
（bench-231 特征提取、bench-214 大图下载等）在长工具调用期间 container.log 本来就静默
（loopflow 只在 agent 消息时写日志）——13 次误杀（bench-214/201 各被杀 3 次），健康 run
反复被终止，24h 仅 2 篇完成且为截断结果。**container.log 静默 ≠ 挂起**。

**看门狗 v2 修复**：
- liveness 改为 **run 目录文件活动**：30 分钟无任何文件写入才判挂起（模型调用 <30min，
  工具调用必写文件——区分可靠）
- **定向 kill**：只杀 /output 挂载匹配本 run 的容器（v1 误杀所有 shard 容器）
- loopflow 空闲超时提高到 **12h 兜底**（bench-v3.sh env LOOPFLOW_AGENT_IDLE_TIMEOUT=43200，
  防长静默工具调用被 transport 误杀）
- 批次已按 v2 重启（28 篇，干净数据）；v2 运行中再发现：30min 无文件活动规则对
  长 Docker 拉取/构建（bench-214 provision 网络重置卡 30min+）仍误杀 → 窗口放宽到
  **90min**（长拉取可容忍，数小时真挂起仍必被捕获）；已生效于后续 entry

## P2：35 篇 claims 模式最终结果（2026-08-22，当前 oracle 权威重评）

> 批次完成后用**当前 claims 完整 oracle** 对全部归档 run 重评（修正批次时部分 entry
> 尚未补 claims 的差异 + 恢复 bench-223 AUROC claim）。**16 REPRODUCED / 13 PARTIAL /
> 6 FAILED**（REPRODUCED 率 46%，作者 D5 ~60% 同量级）。

| entry | verdict | score |
|-------|---------|-------|
| bench-200 | FAILED | 0.0 |
| bench-201 | PARTIAL | 46.67 |
| bench-202 | PARTIAL | 50.0 |
| bench-203 | PARTIAL | 30.0 |
| bench-204 | PARTIAL | 50.0 |
| bench-205 | PARTIAL | 50.0 |
| bench-206 | PARTIAL | 30.0 |
| bench-207 | REPRODUCED | 100.0 |
| bench-208 | REPRODUCED | 85.0 |
| bench-209 | FAILED | 17.5 |
| bench-210 | REPRODUCED | 65.0 |
| bench-211 | REPRODUCED | 100.0 |
| bench-212 | REPRODUCED | 100.0 |
| bench-213 | REPRODUCED | 100.0 |
| bench-214 | REPRODUCED | 85.0 |
| bench-215 | REPRODUCED | 100.0 |
| bench-216 | REPRODUCED | 100.0 |
| bench-217 | REPRODUCED | 100.0 |
| bench-218 | REPRODUCED | 100.0 |
| bench-219 | PARTIAL | 50.0 |
| bench-220 | REPRODUCED | 100.0 |
| bench-221 | REPRODUCED | 76.25 |
| bench-222 | PARTIAL | 30.0 |
| bench-223 | REPRODUCED | 85.0 |
| bench-224 | REPRODUCED | 100.0 |
| bench-225 | FAILED | 15.0 |
| bench-226 | FAILED | 0.0 |
| bench-227 | PARTIAL | 50.0 |
| bench-228 | PARTIAL | 50.0 |
| bench-229 | FAILED | 15.0 |
| bench-230 | REPRODUCED | 100.0 |
| bench-231 | FAILED | 15.0 |
| bench-232 | PARTIAL | 50.0 |
| bench-233 | PARTIAL | 50.0 |
| bench-234 | PARTIAL | 50.0 |

**重评发现与修正**：
- bench-222：REPRODUCED 100 → **PARTIAL 30**（P1-2 补 5 条 claims 后如实显示 0/5 复现）
- bench-206：PARTIAL 50 → 30（3 条 PR claims 0 通过）
- **bench-223 AUROC claim 曾被 P1-1 converter 换入覆盖丢失**（重评暴露）→ 已恢复
  （REPRODUCED 85，AUROC 0.996 ≥ 0.95）
- 教训：converter 重生成换入会覆盖手工补的 claims——手工补后需回归检查

**评估产物追溯补登（2026-08-31）**：
- **bench-222 最终评估 JSON 已固化**：`/storeData/gs/claroai-calibration/scripts/
  eval-bench-222-final.json`（P2 时点代码重跑，PARTIAL 30.0、C1–C5 全部
  "no reproduced value"、0/5）。此前该结果仅存在于 reval35.txt 汇总行，`/tmp/bl012`
  只有 0-claims 时点的过期 eval-bench-222-new.json（REPRODUCED 100）——追溯缺口已闭合。
- **reval35.txt 的 bench-223 行为过期快照**（PARTIAL 50.0、0/0）：是 AUROC claim 恢复前
  的中间评估；权威值为 REPRODUCED 85（见上）。引用 reval35.txt 时须注意，勿误引 223 行。

## P0：幽灵进程根因与修复（2026-08-18，loopflow idle timeout）

**根因**：loopflow `CliTransport`（cli.py）docstring 声称"Default 300s"超时但从未实现——
`self._timeout = None`，`join(timeout=None)` 无限阻塞；`claude -p` 子进程在模型 API 挂起时
可无限等待（bench-229 实测 Run 阶段 6.5h、Package 阶段 10.5h 无响应）。

**修复**（已应用 local + 远端 /storeData/gs/loopflow 源码 + 运行时镜像新 tag
`bio-reproducer-runtime:system-idlefix`）：
- CliTransport 新增**空闲超时**：子进程连续无输出（stdout/stderr）超过阈值即 kill + TimeoutError；
  任何输出行重置计时。默认 2h（`LOOPFLOW_AGENT_IDLE_TIMEOUT` 可配）——长构建/下载静默
  30-60min 不受影响，实测挂起 6.5-10.5h 必然被捕获；10s 轮询粒度，本地单测通过。
- 校准层看门狗 `run-with-watchdog.sh`：容器日志 2.5h 无更新 → kill + 自动重启（默认最多
  2 次）；metrics.json 出现即视为完成。修复了启动竞态（等容器出现再判 idle）。

**验证（2026-08-19 完成）**：bench-229 在 system-idlefix 镜像 + 看门狗下**端到端跑通
7 阶段**（Reader 20:49→Provision 01:42→Data 01:57→Run 02:21→Validate 02:26→Package 完成，
loop `Done:` 输出 verdict REPRODUCED）——**全程无停摆、空闲超时未触发、无需任何干预**，
对比修复前两次挂起（Run 6.5h / Package 10.5h 停摆）——**P0 修复验证通过**。
最终独立评估：**FAILED 15**（A1 KPMP UUID 无判断；4 条 barcode claims 未复现——run 自述
multi_barcodes.csv 缺 LOY 列无法验证；与作者 D5=1 基本一致）。归档 runs/bench-229
（旧 run 存 legacy-2026-08-18-05-02-03）。
**看门狗设计缺陷记录**：以 metrics.json 出现为完成判定过早（Package 阶段仍在进行）——
应改为等 loop `Done:` 或容器退出（已在 run-with-watchdog.sh 修复）。

## 教训与规范

1. **完成即归档**：run 完成立即 `mv` 到持久区 + 登记本索引，勿事后批量移动（bench-200/220/222 产物因批量移动误操作丢失）
2. 丢失的 3 篇评估结果已保留（Report 023/024），如需完整产物需重跑
3. verify 模板（converter.py）已适配：Markdown 表格/属性-值表/URL 行、规范化模糊匹配、out-of-scope NA、状态词
4. 校准执行方法论（独立验证原则、完成即归档等）属本地流程，见 AGENTS.local.md「校准运行工作目录与资产规范」

## ADR-0011 验证资产（2026-08-22）

零算力验证，全部以已归档 run 作 fixture，产物入库：

| 资产 | 内容 |
|------|------|
| `calibration-failure-taxonomy.md` | 35 run 死因四分类 + 独立复核（BL-017） |
| `package-executability-probe.md` | 26/35 有 run.sh；6 个抽样在干净容器 `run.sh check` **0/6 通过**，全因缺宿主 java/nextflow/R/docker（BL-025） |
| `harness/run-entry.sh` | 取代远端未版本管理的 `bench-v3.sh`：dind sidecar（privileged 只在 sidecar）+ 不挂宿主 socket + registry-mirror 透传 + `selftest` 六项边界自检（全过）。**新 run 一律用它，勿再用 bench-v3.sh** |
| `harness-probe.sh` | harness 前置探针（可复现）：出口网络 3/3 `code=200`、`wget`/`aria2c` 缺失、技能前置未满足 2 项（paperutils bin / mineru-api env）。**用途：任何「网络不通/技能坏了」的判断必须先跑它**，BL-019 已因跳过实测误诊两次 |

验证结论已回填 `docs/adr/0011-verifiable-self-assessment.md` 验证段：证据面可从
validate 报告切换到结果 CSV（bench-220 三个 HR 零正则复算通过）；「未完成获取」与
「外部不可得」按终态类别可区分、无需重试阈值（bench-234 vs bench-217）；参数缩减的
通用检出信号是作者原码与实际执行码的 diff（bench-225）；answers 交叉核对容差由书写
精度导出、无魔数。


## ADR-0058 迁移验证（2026-09-01，bench-220-0026-migrate）

> bio-reproducer workflow 从手写路由循环迁移到框架层 run_rerun_loop 后的首个
> 完整端到端 run（远端 run-entry.sh）。

| 项 | 值 |
|----|-----|
| run | `/storeData/gs/claroai-calibration/runs/bench-220-0026-migrate` |
| 结果 | **REPRODUCED（validate 自评 100/100，无偏差 deviations:[]）**；独立评估 REPRODUCED 100（3/3 HR claims 交叉核对通过，值 1.63/3.32/2.42 与论文一致） |
| 迁移验证点 | ① workflow 含 run_rerun_loop 正常加载执行（无 import 错误）；② `rerun: stage=X (stages_run=N)` 框架编排日志走通 7 阶段；③ validate 经 payload.route_to=null 返回（无回环，run_rerun_loop 正常终止）；④ Package check.log 通过；⑤ run-entry.sh exit=0 |
| Provision | paper-r-env:4.2.0 镜像构建成功（3 次尝试：survminer 缺失、Deriv 编译失败后成功）——agent 失败重试正常 |
| 发现 | **answers.csv value 带 CI 格式**（`1.63 (1.25–2.14)`）导致评估器 _locate 交叉核对 NO-EVIDENCE（value 非数值）；修正为纯数值后 3/3 通过——属 agent 书写格式问题（非迁移缺陷），run7 无此问题，建议 validate.md 明确 answers value 只写数值 |

## ADR-0058 迁移成对 ablation（2026-09-01）

> 迁移前后同 entry（bench-220）对比：旧 workflow（手写路由循环）vs 新 workflow
> （框架 run_rerun_loop）。同论文、同 oracle、同 harness。

| 维度 | 迁移前（run7） | 迁移后（0026-migrate） | 结论 |
|------|--------------|----------------------|------|
| workflow 路由实现 | 手写 while routing_budget + routing.jsonl | 框架 run_rerun_loop + payload.route_to | 迁移等价 |
| verdict | REPRODUCED 100 | REPRODUCED 100 | **无回归** |
| 独立评估 | REPRODUCED 100（3/3 claims 交叉核对） | REPRODUCED 100（3/3 claims，修正 answers 格式后） | 等价 |
| 7 阶段走通 | ✓ | ✓ | 等价 |
| 路由触发 | unit 26 用例覆盖 | unit 26 用例覆盖（test_routing_*） | 等价 |
| 编排日志 | 无框架日志 | `rerun: stage=X (stages_run=N)` 框架编排日志 | 迁移生效证据 |

**结论**：迁移无行为回归；路由机制从 loop 层（自造文件+自检）移到框架层
（run_rerun_loop + payload），验证了 ADR-0058 的设计目标。
