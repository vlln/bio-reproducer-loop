# Plan 04 — 证据面切换：评分只读真实产物（BL-023/BL-015）

依据：ADR-0011 §4/§4.1/§5（FC-003/FC-004/FC-005/FC-006）、BL-023 / BL-015；
前置：单元 02（04_data 契约）/ 03（05_run 契约 + answers + routing）。

## 目标

外部评分主干从「读系统自评」切到「只读真实产物 + 极薄 answers」：
- `06_validate/` 整目录移出证据面（FC-006）
- 数值 claim 的证据从 validate_report 切到 `05_run/answers.csv` + **强制交叉核对**（FC-005）
- converter 生成 rubric 时不再产出 validate_report 证据（FC-004）
- 元数据审计 check（A1/A2）重挂标准格式产物（04_data sha256sums/日志、03_provision digests）
- `oracle/verify.py` 的散文解析退役，只留数值比对 + answers 读取

## 分步（按依赖序）

### 1. 公开问题清单 + 私有映射（ADR §4.1）
- `claims.yaml` 每个 claim 加 `target_id`（公开 slug，如 `blood-lead-cvd-hr`）——私有 oracle
  内声明「该 claim 对应公开问题清单的哪个 target_id」
- converter 生成 `input/questions.yaml`：`target_id + question + unit`（**无期望值**）
- 系统侧：`run.md` 的 answers target_id 用 questions 的 target_id（单元 03 已落 answers
  表头；target_id 来源写明确）

### 2. converter 禁用 validate_report（FC-004）
- `_build_rubric`：claim check 的 `evidence.artifact_role: validate_report` →
  `answers`（新 role，指向 `05_run/answers.csv`）
- `VERIFY_TEMPLATE` 重构 `check_claim`：读 answers.csv（按 target_id 匹配行）→
  **交叉核对**（value 能在 source_file 中定位，容差由书写精度导出，复用
  `benchmarks/harness/crosscheck-prototype.py` 的 locate 逻辑，无魔数）→ 与
  paper_value 比对；交叉核对失败 → NO-EVIDENCE（不计分，非判错）
- 退役：`_parse_claims_evidence`（validate 报告散文解析）删除

### 3. 元数据审计 check 重挂（A1/A2）
- A1 `check_data_references`：证据 data_manifest → `04_data` 标准格式
  （sha256sums.txt 存在 + 获取日志终态推导「系统判断可获取」，无日志=未尝试）
- A2 `check_code_references`：证据 provision_report → `03_provision` digests
  （`docker images --digests` 输出；**顺带推广 provision 契约**：provision.md 要求落
  digest 文件 + `artifact_checks.check_provision_phase` + workflow 检查）

### 4. adapter（FC-006）+ 透传
- `_read_verdict_and_score`：删除 report.md 正则回退（散文解析退役）；metrics.json 仅作
  `claimed_verdict` 观测（ADR §4 允许），不参与任何 check 打分
- 透传 `routing_budget`：adapter 从 envelope `deadline_seconds` 派生（如
  `max(0, deadline//3600 - 1)`，具体公式留实现——预算属调用方，系统不写死）

### 5. evaluate_run.py 新证据流
- 校准评估改读 `05_run/answers.csv` + `04_data` 标准格式 + `03_provision` digests
  （旧散文路径保留为 legacy 标记或删除）

### 6. entry 批量增量更新（不重生成，防覆盖手工策展）
- 42 个 entry：claims.yaml 加 target_id + 生成 input/questions.yaml + 替换 verify.py
  （新模板）；**不动 claims 期望值、不动手工补丁**
- 若 entry 有手工补的 claim（如 bench-223 AUROC），target_id 由脚本按 metric slug 生成

## 验收

| 项 | 判据 |
|----|------|
| FC-004 | converter 生成的 rubric 无 `validate_report` 证据（grep 审查 + converter 测试） |
| FC-005 | answers 值可在 source_file 定位否则 NO-EVIDENCE（含「值真实但标错 source_file」反例） |
| FC-006 | adapter 不把 metrics.json 作为评分来源；06_validate 不在 evaluator artifacts |
| A1/A2 | 从 04_data/03_provision 标准格式推导判断，无散文解析 |
| 回归 | 全套确定性测试全绿；converter golden 对比更新；bundle gate 全过 |

## 风险与边界

- 已归档 35 个 run 无 answers/digests → 新口径下大量 NO-EVIDENCE（符合 ADR「该批定为
  pilot」）；evaluate_run 重评用于校准对比，不发布
- verify.py 是 per-entry 模板生成：改 VERIFY_TEMPLATE + 增量替换，不触碰手工策展
- A2 依赖 provision 契约推广（新 run 才有 digests）；旧 run 该 check 无证据不计分
- 交叉核对的「推导系统判断」只做薄映射（事实 → 判断），不做论文语义判断
