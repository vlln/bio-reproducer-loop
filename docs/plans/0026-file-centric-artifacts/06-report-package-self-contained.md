# Report 06 — 交付包自包含（BL-025 / FC-008）

对应 [Plan 06](06-plan-package-self-contained.md)。证据 `benchmarks/package-executability-probe.md`
（0/6 干净容器通过，根因：交付包把 Java/Nextflow/Docker/R 当宿主既有环境）。

## 交付物

| 文件 | 改动 |
|------|------|
| `loops/bio-reproducer/agents/package.md` | **自包含纪律（BL-025）**：交付包只要求 Docker，Java/Nextflow/R 全在镜像内（镜像清单 = `03_provision/digests.txt`，单元 04 已落）；run.sh check 不再检查宿主 java/nextflow/R；run/validate 用 `docker run` 执行分析镜像；**FC-008 证据**：Package 必须执行 `bash run.sh check` 并落 `07_package/check.log`（含退出码 0），未执行/非 0 不得声明 completed；run.sh 模板更新（check= docker + 镜像 inspect；provision= 按清单 build） |
| `loops/bio-reproducer/artifact_checks.py` | `check_package_phase`：run.sh 存在 + `07_package/check.log` 存在且含退出码 0 记录（`exit/EXIT/status` + 可选分隔符 + 独立 0，`(?<!\d)(?!\d)` 防 `exit 10` 误报） |
| `loops/bio-reproducer/workflow.py` | Package 返回 complete 后 `_require_parsable(check_package_phase)`——无执行证明即 fail-fast（FC-008） |
| 测试 | `check_package_phase` 五态（缺 run.sh/缺 check.log/退出码 1/退出码 0/标准记录格式）；workflow 2 个 fail-fast 用例（无 check.log、EXIT=1）；package.md prompt 断言（自包含 markers + check 节无 nextflow/java） |

## 验收结果（对照 Plan 06）

| 项 | 判据 | 结果 |
|----|------|------|
| 自包含规则 | package.md 含「只要求 Docker / digests.txt 镜像清单 / check 不查宿主 java/nextflow/R」 | ✅ prompt 断言 + 模板语法 `bash -n` 通过 |
| FC-008 | Package 无 check.log 或退出码非 0 → fail-fast；退出码 0 → 通过 | ✅ `check_package_phase` 五态 + workflow 2 用例 |
| 回归 | 全套确定性测试全绿 | ✅ **203 passed / 4 skipped**（199 → 203） |

## 关键设计决策（留档）

1. **自包含边界 = 只要求 Docker**（等价于 Java 之于 Maven）：不要求「无 Docker 宿主
   也能跑」——那是过度设计。0/6 的缺 java/nextflow/R 由「分析环境在镜像内」消除；
   docker CLI+daemon 是唯一宿主前置（run-entry.sh 的 dind sidecar 已验证该路径）。
2. **check.log 是 FC-008 的执行证明**：Package 不重跑分析，但「执行 check」是打包动作
   的一部分（README 生成后的验证步骤），不是重跑分析——避免与「Phase 7 不重跑」规则
   冲突（package.md 规则节已显式澄清）。
3. **已归档 35 个 run 的 run.sh 是旧契约**（查宿主工具链）：不重写旧产物；新 run 的
   Package agent 按新规则打包。干净容器验证在 run-entry.sh 首次实跑时执行（harness
   侧，单元 01 的 dind 已具备验证条件）。

## 容器完成判据（对照 0026 README）

| 判据 | 状态 |
|------|------|
| 单元 01-04 验收项通过，且既有确定性测试保持全绿 | ✅ 203 passed（基线 141 → 203，+62 契约/回归用例） |
| ADR-0011 FC-001~FC-008 每条有对应检出手段 | ✅ FC-001 workflow 测试 / FC-002 artifact lint / FC-003 answers+routing 白名单 lint / FC-004 converter+validator / FC-005 evaluator 交叉核对 / FC-006 adapter+测试 / FC-007 `_derive_routing_budget`+workflow / FC-008 `check_package_phase`（本单元） |
| 一个 entry 端到端跑通新契约（产物标准格式、evaluator 不读 06_validate 判分） | ⏳ 集成测试已覆盖评分闭环（bench-220 answers 3 claims 全过 + NO-EVIDENCE 三态）；**真实 run-entry.sh 端到端首跑**仍待执行（需要算力 + 宿主 export MINERU_API_URL） |

## 未做 / 移交

- **run-entry.sh 完整 entry 首跑**（新契约端到端实跑 + Package 干净容器冒烟）：待
  量具冻结（S2）后或人类批准的一次实跑；宿主需 export `MINERU_API_URL`
- 远端 `bench-v3.sh` 删除：等 `run-entry.sh` 跑通完整 entry 后
- 已归档 35 run 的旧 run.sh 不重写（pilot 定性）
