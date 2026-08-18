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

- `bench-v3.sh`：docker 模拟 VM 边界跑 loopflow 全链路（时间戳目录，`bash bench-v3.sh <entry>`）
  （Plan 0025：不再硬编码 `scope=d1_d3_audit`，改读 entry `metadata.task` 自然语言任务作为
  loop scope 参数——评分维度代码不再进入被测系统）
- `watch.sh`：run 完成检测（写 run-done.txt）
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

**验证**：bench-229 在 system-idlefix 镜像 + 看门狗下重跑——全程连续推进 6h 无停摆
（Reader 20:49→Provision 01:42→Data 01:57→Run 02:21→Validate 02:26），空闲超时未触发
（无需干预）。**看门狗设计缺陷记录**：以 metrics.json 出现为完成判定过早（Package 阶段
仍在进行，report.md 未写完），导致误判完成 + 评估缺 validate_report artifact——应改为
等 loop `Done:` 或容器退出。

## 教训与规范

1. **完成即归档**：run 完成立即 `mv` 到持久区 + 登记本索引，勿事后批量移动（bench-200/220/222 产物因批量移动误操作丢失）
2. 丢失的 3 篇评估结果已保留（Report 023/024），如需完整产物需重跑
3. verify 模板（converter.py）已适配：Markdown 表格/属性-值表/URL 行、规范化模糊匹配、out-of-scope NA、状态词
4. 校准执行方法论（独立验证原则、完成即归档等）属本地流程，见 AGENTS.local.md「校准运行工作目录与资产规范」
