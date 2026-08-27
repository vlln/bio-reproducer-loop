# Report 02 — phase 产物契约改标准格式文件（Data phase 实物）

对应 [Plan 02](02-plan-artifact-contract.md)。范围：**先只改 Data 一个 phase 做出实物**，
provision/run/validate/package 的契约推广留到单元 03/04（Plan 02 明示的执行策略）。

## 交付物

| 文件 | 改动 |
|------|------|
| `loops/bio-reproducer/artifact_checks.py` | **新增**。终态类别判定器 `classify_download_log`（completed/unavailable/not_attempted，ADR-0011 §2.1）+ `checksums_parseable` + `data_phase_evidence` + `check_data_phase`（04_data「存在 + 可被标准工具解析」） |
| `loops/bio-reproducer/workflow.py` | `_require_parsable` 新增；Data 阶段后插入 `check_data_phase` fail-fast（抓「幻觉 complete——返回 complete 但 04_data 无任何标准格式证据」）；`_require_files` 保留给其他 phase |
| `loops/bio-reproducer/agents/data.md` | 状态词表拆分 `completed / partial / unavailable / not_attempted`（按终态信号判定，明确「传输层失败 ≠ 外部不可得」「无日志不得标 unavailable」）；每资源获取日志 + `sha256sums.txt`；`curl -C -` 续传纪律（不装 wget/aria2c）；阻塞也落尝试日志；manifest 降级为从证据文件渲染 |
| `loops/bio-reproducer/agents/reader.md` + `_base.md` | **死技能声明移除**（BL-019 未闭项闭环）：`skills:` 删 `paperutils`/`mineru-api`；PDF 转换改为「环境有工具则用、无则直读文本」；标识符解析改直调 Crossref / EuropePMC（探针已证可达） |
| `benchmarks/runner/system_artifact/skills.lock.yaml` + `tests/unit/test_system_artifact.py` | lock 与声明集合同步收缩（7 → 5 技能）；`build_system_artifact` 的「lock 必须精确等于声明技能」校验要求两者一致 |
| `loops/bio-reproducer/.skills/paperutils`、`.skills/mineru-api` | **删除**（死代码：不再被任何 agent 声明，loopflow 只注入声明的技能，`runner.py:256`） |
| `tests/contract/test_data_phase_contract.py` | **新增**（18 个契约用例） |
| `tests/fixtures/contract/` | bench-234 两个真实日志 + bench-217 manifest + README（来源/裁剪说明） |
| `tests/unit/test_loop_workflow.py` | happy path 等 6 个用例补 `04_data` 标准格式证据 |

## 验收结果（对照 Plan 02）

| 项 | 判据 | 结果 |
|----|------|------|
| 阻塞也留证据 | 无正常产物但有获取日志 → 可判定；两者皆无 → 无证据 | ✅ bench-217（仅散文 manifest + 空 raw_data/reference，零日志）→ `check_data_phase` False；bench-234 → True |
| 终态类别区分 | `curl: (35)` 判未完成；HTTP 404/403 判外部不可得；`Download complete` + 文件存在判已获取 | ✅ 真实日志：`p4_gse136831.log` → not_attempted；`p4_gse289881.log`（中途 `curl: (56)` 但终态 `Download complete` ×2 + `ls -l`）→ completed；合成 4xx/451/访问墙 → unavailable |
| 无阈值 | 代码中不出现任何重试次数/比例常量 | ✅ `artifact_checks.py` 无 `attempts`/`retries`/`>= 2` 等；契约测试 `test_no_magic_thresholds_in_artifact_checks` 守护 |
| answers 交叉核对 | 值可在 `source_file` 定位，容差由书写精度导出 | ⏸ 单元 04（原型 `benchmarks/harness/crosscheck-prototype.py` 已验证 3 PASS / 2 NO-EVIDENCE，本单元未动） |
| 散文不被消费 | 无新增正则解析；`oracle/verify.py` 标记 legacy | ⏸ 单元 04（本单元未新增任何 Markdown 解析；`verify.py` 退役随证据面切换） |
| 回归 | 141 个确定性测试全绿 | ✅ **166 passed, 4 skipped**（141 存量 + 新增 25：contract 18 + system_artifact 相关调整后全绿） |

## 关键设计决策（留档）

1. **`check_data_phase` 判据是「至少一个标准格式证据」而非三件套全齐**。三件套
   （数据本体 + sha256sum + 每资源日志）是 prompt 契约（`agents/data.md`）；workflow 的
   fail-fast 只抓「声称完成但零证据」。理由：抓幻觉不需要校验完整性，校验完整性会误杀
   合法边界（如只读预下载数据、无需下载的场景），且完整校验是评分策略、不该进系统。
2. **终态判定优先级：completed > unavailable > not_attempted**。`p4_gse289881.log`
   同时含 `curl: (56)` 与 `Download complete`——续传克服中间失败后终态是完成，判
   completed（ADR 验证 3 的 bench-234 结论一致）。
3. **`bench-217` 实际有 `04_data/` 目录**（与 ADR-0011 验证 3「无 04_data 目录」的字面
   表述不同——归档 Aug 20 重建过）：目录仅含散文 `data_manifest.md`（BLOCKED）+ 空
   `raw_data/`/`reference/`，**无任何 .log 与校验文件**。语义不变：有目录但无标准格式
   证据 → 判「无证据」，不得因散文自称「DOI 不可解析」而判外部不可得。fixture 与
   README 已按实测记录。
4. **workflow.py 以 `sys.path.insert(__file__ 同目录)` 导入 `artifact_checks`**：workflow
   可能以任意 CWD 被加载（loopflow runtime / pytest importlib），相对导入不可靠。

## 未做 / 移交

- **provision/run/validate/package 的契约推广**（`docker images --digests`、结果 CSV、
  answers、run.sh 执行日志）→ 单元 03/04，按 Plan 02「先做实物再推广」
- **`oracle/verify.py` 301 行散文解析退役标记** → 单元 04 证据面切换时一并处理
- **`evals/fixtures/phase-states/valid/bench-001/01_plan/plan.md` 中 `paperutils` 字样**为
  历史产物快照（fixture 数据），保留
- **`docs/interface/0001-benchmark-protocol.md:81 tool: mineru`** 属单元 05 文档同步
  （人类 promote 门禁）范围，未动
- **`.skills/bio-reproducer/`** 死代码目录仍留（BL-002 candidate，本单元不越权）
- **`run-entry.sh` 完整 entry 首跑**：仍待单元 03 契约改造后执行（HANDOFF 既定顺序）

## 实测记录

- fixture 源：远端 `/storeData/gs/claroai-calibration/runs/bench-234/repro-data/04_data/`、
  `bench-217/repro-data/04_data/`（ssh gs@172.16.209.237）
- `p4_gse289881.log` 原始 229,833 字符（34 分钟 curl 进度），裁剪为 440 字符 7 行，
  仅滤进度条、保留全部终态信号（`curl: (56)`、`Download complete` ×2、
  `Resuming from byte 447599`、`ls -l`）——裁剪细节见 `tests/fixtures/contract/README.md`
- 远端 35 个 run 的 04_data 日志中**无 HTTP 4xx 正例**（全部是传输层错误
  `curl: (18)/(92)` 等），故 unavailable 判定用合成日志覆盖（终态信号即 4xx 文本，
  判定逻辑与真实日志一致）

## 修订（2026-08-27）：死技能声明**恢复**（人类提供来源）

本单元原按纪律「默认不存在 → 移除声明」清掉 `paperutils`/`mineru-api`（BL-019 处置 (a)）。
人类随后提供真实来源，按 HANDOFF 待决策项 3 的约定「若人类提供来源则改为补齐」执行反转：

| 技能 | 来源 | 前置满足方式（全部实测） |
|------|------|------|
| paperutils | GitHub `vlln/paperutils`（skills/paperutils，commit `b88e5b7c`）或本机 `~/Project/skill_project/paperutils/` | 工具内嵌 `scripts/paperutils`（`python3` 调用，零依赖）；**已安装版 SKILL.md 的 `requires.bins` 是过时声明**（源仓库版本无此声明）——两端 `~/.agents/skills/paperutils/` 已同步为源版本；实测 `paperutils get 10.1136/bmjebm-2023-112303` 成功 |
| mineru-api | 端点 `http://172.16.218.40:8001/`（`/health` 200，v3.1.10） | `requires.env MINERU_API_URL`：宿主 export 后由 `run-entry.sh:78` 透传沙箱；`harness-probe.sh` 同步补透传；实测 `/health` healthy |

连带恢复：`agents/reader.md` 的 `skills:` 声明（技能优先 + 直调 API 兜底，
BL-019 处置 (c) 保留）、`skills.lock.yaml` 两条目（commit 与源仓库 HEAD 一致）、
`tests/unit/test_system_artifact.py`（7 技能）。
**教训留档**：BL-019 的「bin paperutils 不存在」诊断针对的是**旧版 SKILL.md 的过时声明**；
移除声明解决了撞墙表象，但真正根因是技能安装区版本滞后于源仓库——补齐时应先对比
安装区与源仓库的 SKILL.md 差异（本修订即由此发现）。
