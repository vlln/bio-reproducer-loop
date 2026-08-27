# Report 05 — 下游文档同步（待人类 promote）

对应 HANDOFF 单元 05。**不可委托门禁**：修订完成，需人类 review 并 promote 后
Spec/Interface/AC 才回到 active。

## 修订内容（ADR-0011 §2/§4/§4.1/§5 + 单元 02-04 落地的契约）

| 文档 | 修订 |
|------|------|
| `docs/interface/0001-benchmark-protocol.md` | InputBundle 结构加 `questions.yaml`（公开问题清单）；BundleResource 表 role 加 `questions`、authority 加 `benchmark`；**新增「被测系统标准格式产物」节**（03_provision digests / 04_data sha256sums+日志 / 05_run results+answers+commands.log / 07_package；answers 与 routing.jsonl 键名白名单；`06_validate/` 不在证据面 FC-006）；NO-EVIDENCE 语义（FC-005） |
| `docs/interface/0002-claroai-converter.md` | 修订注（单元 04 证据面切换）；claims.yaml 加 `target_id`；**新增 §2.1 公开问题清单**（questions.yaml 结构 + 无期望值 + 交叉核对 + limitation 声明）；§3 rubric 证据角色 → answers/data_evidence/environment；**§4 submission 证据约定重写**（只读标准产物，NO-EVIDENCE 三态，全无证据→BLOCKED） |
| `docs/spec/0001-benchmark.md` | claims 模式节：公开问题清单、oracle 真值证据改为标准格式产物、评分语义（交叉核对 + NO-EVIDENCE）、散文报告不被消费（BR-002 落地） |
| `docs/ac/0002-benchmark-runner.md` | AC-0005-N-4（artifacts 新角色，06_validate 不在）、N-5（routing_budget 由 deadline 派生，FC-007） |
| `docs/ac/0005-claroai-converter.md` | N-6（questions/target_id）、N-7（交叉核对四态 + NO-EVIDENCE）、B-5（无 answers 不得从散文兜底，FC-006）、F-5（validate_report 残留拒绝，FC-004） |
| `docs/adr/0011-verifiable-self-assessment.md` | **FC-003 措辞修订**：routing.jsonl 的 reason 字段与旧字面「不得含理由」冲突——§3 明示含 reason，落实为键名白名单（answers 4 列 / routing 5 键，检出手段指向 `artifact_checks.py` 的 lint） |

状态：以上 Spec/Interface/AC 均**退回 proposed**（发布就绪审计要求），promote 后回 active。

## 待人类决策清单

1. **promote Spec 001 / Interface 0001+0002 / AC-0002+0005 回 active**（或指出需再修订处）
2. **docs/README.md 的「设计评估」行**在 promote 后更新（当前仍记 active）
3. 其余（qemu、技能）不阻塞本容器

## 未做（下一单元 06）

- Package 交付包自包含（run.sh 干净容器 check 退出码 0，FC-008）——单元 06
- run-entry.sh 完整 entry 首跑（新契约端到端实跑）
