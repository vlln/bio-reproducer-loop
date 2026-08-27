# Report 04 — 证据面切换：评分只读真实产物（BL-023/BL-015）

对应 [Plan 04](04-plan-evidence-switch.md)。依据 ADR-0011 §4/§4.1/§5
（FC-003/FC-004/FC-005/FC-006），BL-023 / BL-015。

## 交付物

| 文件 | 改动 |
|------|------|
| `benchmarks/converters/claroai/converter.py` | `_slugify`（metric → 公开 target_id）；claim 加 `target_id`；`_build_questions`（input/questions.yaml，无期望值）；`_build_rubric` 证据面切换（validate_report→answers、data_manifest→data_evidence、provision_report→environment）；`_build_bundle` 声明 questions 资源；`VERIFY_TEMPLATE` 重写（178 行，退役全部散文解析） |
| `benchmarks/converters/claroai/backfill_evidence_switch.py` | **新增**：42 entry 幂等迁移（claims 加 target_id、生成 questions.yaml、rubric 重挂、bundle 声明 questions、替换 verify.py）；保护：非 claroai claims 结构（bench-001~006/100）跳过 |
| `benchmarks/runner/independent_evaluator.py` | **NO-EVIDENCE 三态**（FC-005）：verify 返回 `no_evidence` → check 从权重排除（不计分不扣分）；全部 check 无证据 → BLOCKED（score 不构成复现率） |
| `benchmarks/runner/adapters/loopflow.py` | `_read_verdict_and_score` 删除 report.md 正则回退（散文解析退役），metrics.json 仅作 claimed_verdict 观测（FC-006）；`_artifact_candidates` 加 answers/data_evidence 角色；`_derive_routing_budget`（FC-007：从执行器 deadline 派生，5h→4、1h→0） |
| `benchmarks/runner/bundle_validator.py` | RESOURCE_ROLES 加 `questions`、AUTHORITIES 加 `benchmark`（benchmark 自产资源不要求 derived_from） |
| `benchmarks/converters/claroai/evaluate_run.py` | 新证据流：只读 answers.csv + sha256sums + digests；旧协议 run 不可重评（明确报错）；`--claims-evidence` 移除 |
| `loops/bio-reproducer/agents/provision.md` + `artifact_checks.py` + `workflow.py` | **provision 契约推广**：`03_provision/digests.txt`（docker images --digests 原始输出）+ `check_provision_phase` + Provision 后 fail-fast |
| `tests/contract/test_evidence_switch.py` | **新增** 8 例：交叉核对命中/标错 source_file/缺 target/超容差判错、A1 日志终态推导、A2 digests 推导、evaluator 三态、check_provision_phase |
| 42 个 entry | claims.yaml 加 target_id（46 条）、input/questions.yaml（42 份）、rubric 证据重挂（35 个 claroai entry）、bundle 声明 questions、verify.py 换新模板 |

## 验收结果（对照 Plan 04）

| 项 | 判据 | 结果 |
|----|------|------|
| FC-004 | converter 生成的 rubric 无 validate_report 证据 | ✅ 全仓 grep 无残留（仅 backfill 映射表）；`test_questions_and_rubric_evidence_switch` 断言 |
| FC-005 | answers 值可定位否则 NO-EVIDENCE（含标错 source_file 反例） | ✅ `check_claim` 交叉核对 + evaluator 三态；标错 source_file → no_evidence（不判错） |
| FC-006 | adapter 不把 metrics.json 作为评分来源；06_validate 不在 evaluator artifacts | ✅ report.md 正则回退删除；`_artifact_candidates` 无 06_validate 产物 |
| A1/A2 | 从 04_data/03_provision 标准格式推导，无散文解析 | ✅ 日志终态 + digests 推导；verify.py 模板无 `_parse_data_manifest` 等 |
| 回归 | 全套确定性测试全绿 + bundle gate 全过 | ✅ **199 passed / 4 skipped**；42 entry bundle gate 全过 |
| 端到端 | 一个 entry 新契约跑通（产物标准格式、evaluator 不读 06_validate 判分） | ✅ 集成测试：bench-220 answers 样例（1.6339/3.3246/2.4230）经 evaluator 3 claims 全过（ADR-0011 验证 1 的真实 HR 值） |

## 关键设计决策（留档）

1. **NO-EVIDENCE 三态**：verify 返回 `{"passed": False, "no_evidence": True}` →
   evaluator 将该 check 从总权重排除（不计分不扣分）；**全部 check 无证据 → BLOCKED**
   （score=0 不构成复现率，避免「无证据却得高分」的测量漏洞）。这与 ADR §4「定位
   失败不计分（不是判错）」一致。
2. **target_id 公开映射**（ADR §4.1 落地）：claims.yaml 每个 claim 加
   `target_id`（metric 的 slug，如 `blood-lead-cvd-hr`）；`input/questions.yaml`
   是公开问题清单（target_id+question+unit，无期望值）；系统 answers.csv 用
   target_id 填值；oracle 判分 = 比对私有期望值 + 交叉核对 source_file。
3. **evaluate_run 旧 run 不可重评**：旧协议 run（无 answers/digests）直接报错——
   不拿旧散文产物硬套新口径（该批已定性 pilot，ADR-0011 负面后果明示）。
4. **backfill 保护**：只迁移 claroai claims 结构（`claims` 为数值列表）；
   bench-001~006/100 的手写 entry（experimental_design/methods 结构）跳过。
   实测教训：初次迁移误改了 7 个手写 entry 的 verify.py + 生成空 questions.yaml，
   已 git 恢复并加保护（测试先行暴露）。
5. **provision 契约随 A2 一并推广**：`digests.txt` 是 `docker images --digests`
   原始输出（标准格式，任何人可重算）；A2 从「digests 非空 = 环境构建有产出」推导。
6. **evaluator `total_weight<=0` 改为 BLOCKED 而非报错**：oracle 无错、submission
   无证据不是 INVALID_ORACLE。

## 未做 / 移交

- **FC-003 措辞修订**（routing.jsonl 键名白名单化，§3 的 reason 字段冲突）→ 单元 05
- **`input/questions` 契约写入 Interface/Spec/AC**（公开问题清单的角色、target_id
  生成规则、系统 answers 对应关系）→ 单元 05（人类 promote 门禁）
- **run-entry.sh 完整 entry 首跑**（新契约产物端到端实跑）→ 待单元 05 文档同步后
- **成对跑 ablation（before/after）** → 量具冻结（S2）后，与 BL-016 一并排期
- **benchmark 侧 evaluate_run 对已归档 35 run 的批量重评** → 不适用（旧协议不可重评，
  新 run 从 run-entry.sh 起即新契约）
