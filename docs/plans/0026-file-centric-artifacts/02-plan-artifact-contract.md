# Plan 02 — phase 产物契约改标准格式文件

依据：ADR-0011 §1/§2/§2.1/§5，FC-001~FC-004、FC-008；backlog BL-014 / BL-021

## 目标

把 phase 之间的事实载体从自由散文 Markdown 换成**标准格式文件**，使下游（下一 phase、
外部 evaluator、用户）读字段而不是猜措辞；散文报告保留但降级为不被程序消费的派生物。

## 契约（逐 phase）

| phase | 必须落下的标准格式文件 | 说明 |
|-------|---------------------|------|
| 04_data | 数据文件本体 + `sha256sum` 输出文件 + 每资源一份获取日志（curl/wget 原始输出） | 阻塞时**也要落获取日志**（§2.1，bench-217 教训） |
| 03_provision | `docker images --digests` 输出文件 | digest 可核对 |
| 05_run | 结果 CSV/TSV + 命令日志 + 图 PNG + `answers`（`target_id,value,unit,source_file`） | answers 只记标识符与数值，无判断 |
| 06_validate | `routing.jsonl`（Plan 03 落地） | 不进外部证据面 |
| 07_package | `run.sh` + 干净环境执行日志（含退出码） | Plan 06 落地 |

**禁止**：发明新的厚 schema；`answers` 与 `routing.jsonl` 之外不得新增自定义格式；
两者均不得含状态词、判断、理由（FC-003）。

## 改动点

1. `agents/data.md`：状态词表拆分 `completed / partial / unavailable / not_attempted`
   （`unavailable` 与 `not_attempted` 的区分依据终态类别，见 ADR §2.1）；要求落 sha256sum
   与每资源获取日志；散文表格改为从这些文件渲染
2. `agents/provision.md`：要求落 digest 文件
3. `agents/run.md`：要求落结果文件到固定路径 + `answers`
4. `workflow.py`：`_require_files` → `_require_parsable`，检查「存在 + 可被标准工具解析」
   （sha256sum -c / docker 可解析 digest 行 / csv 可读且非空 / answers 每值可定位）
5. `tests/contract/`：新增用例覆盖每条检查，负例用已归档 run 的真实产物构造

## 验收

| 项 | 判据 | fixture |
|----|------|---------|
| 阻塞也留证据 | 无 `04_data` 正常产物但有获取日志时，判定为「外部不可得」；两者皆无判「未尝试」 | bench-217（当前无 04_data）、bench-234（有逐资源日志） |
| 终态类别区分 | `curl: (35)` 判未完成；HTTP 404/403 判外部不可得；`Download complete` + 文件存在判已获取 | bench-234 的 `p4_gse136831.log` vs `p4_gse289881.log` |
| 无阈值 | 代码中不出现任何重试次数/比例常量 | grep 审查 |
| answers 交叉核对 | 值必须可在 `source_file` 中定位；容差由书写精度导出（`0.5×10^-decimals`），非魔数 | bench-220 的 `table2_q91_results.csv`（原型已验证 5 例） |
| 散文不被消费 | 全代码路径不再解析 Markdown 表格 | grep：无新增正则解析；`oracle/verify.py` 标记 legacy |
| 回归 | 141 个确定性测试全绿 | — |

## 风险

- 7 个 agent 的 prompt 同时改动，可能引入行为回归 → 用 `evals/` 的 component case 做
  前后对照；改动前先在一个 phase（Data）做实物，验证后再推广
- 标准格式只解决可核验、**不防伪造**（agent 可写假 CSV/假日志）——ADR-0011 已明确不纳入
  该目标，不得在本单元隐含地声称已解决
