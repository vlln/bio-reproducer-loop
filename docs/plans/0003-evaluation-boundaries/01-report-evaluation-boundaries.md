---
title: Report 003 — 独立评估与测试分域实施进展
description: 协议 v2、独立 evaluator、确定性测试、内部 eval 迁移与既有 benchmark 结果重评的阶段性结果。
type: report
status: complete
created: 2026-07-19T00:00:00Z
---

> 本报告中的 `bench-003` 是重编号前、使用旧 DESeq2 oracle 的历史运行标识。
> 当前真实论文 entry 为 `bench-100`，这些结果不构成 bench-100 的 baseline。

# 已完成

| 项目 | 结果 |
|------|------|
| 设计冻结 | Spec v2、Interface 0001、ADR-0005/0006 已 active/accepted |
| Entry 迁移 | 当时编号 bench-001 至 bench-006 的六个 entry 均已拆为 `input/` 与 `oracle/`；eval fixture 独立维护 |
| Submission 协议 | loopflow adapter 对 v2 entry 生成 artifact manifest，不生成权威 score/verdict |
| 独立评分 | evaluator 直接检查 CSV、环境记录和图像文件，不读取 Validate metrics |
| 路径边界 | 拒绝绝对路径、`..` 越界和不存在的 artifact |
| 比较器 | 支持文件、PNG、CSV 行/计数/集合、正则和受信任 Python verifier |
| 测试分域 | 真实 LLM Phase 用例已从 `tests/` 移到 `evals/component/` |
| 假绿修正 | 非零退出、缺失产物和 Package skip 均明确失败 |
| Eval sampling | 12 个 component case、2 个 handoff case；smoke/regression/release 分别运行 1/3/5 次 |
| Eval coverage | 按 capability/failure mode 覆盖，代表输入来自 bench-001/004/006，不按全部 entry 展开 |
| Real-LLM smoke | deepseek-v4-pro 完成 12 个 component case 与 2 个 handoff case，各运行 1 次 |
| Smoke 修复 | 修复 YAML 标量检查、blocked 文本误判和 Package phase-only 恢复门禁；3 个受影响 case 针对性重跑通过 |
| CI 门禁 | 默认 pytest 只收集 `tests/`；GitHub Actions 增加确定性测试 |
| 历史结果导入 | `bench-run submit` 可从既有 `repro-data` 补建 submission，不重新调用 LLM |
| Legacy 保存 | 系统自评迁移为 `legacy-result.json`，evaluator 独占 `result.json` |
| Golden 清理 | 六个 entry 仅保留 `input/`、`oracle/`、`metadata.yaml`；claims 不再包含评分规则 |
| Baseline 生命周期 | 删除开发期 tracked baseline；迁移分数仅保留为本报告中的 observation |
| bench-003 首跑 | 远端完成 5 次 protocol v2 运行与独立评分，5 次均为 REPRODUCED/100 |
| 实现提交 | `7ffa45a refactor(evaluation): separate benchmark and llm eval domains`；`c456147 fix(evals): make smoke harness executable` |

# 验证结果

| 命令 | 结果 |
|------|------|
| `python3 -m pytest tests/ -q` | 57 passed |
| `python3 -m pytest evals/component/ --collect-only -q --eval-profile smoke` | 12 collected |
| `python3 -m pytest evals/component/ --collect-only -q --eval-profile regression` | 36 collected |
| `python3 -m pytest evals/handoff/ --collect-only -q --eval-profile smoke` | 2 collected |
| `python3 -m pytest evals/handoff/ --collect-only -q --eval-profile release` | 10 collected |
| Component real-LLM smoke | 有效结果 12/12 passed；首次 10/12，修复 harness 后 2/2 针对性重跑通过 |
| Handoff real-LLM smoke | 有效结果 2/2 passed；首次 1/2，修复负向断言后针对性重跑通过 |
| 修复影响 case 重跑 | 3 passed in 371.89s |
| `make lint` | PASS |
| Tracked Python compile check | PASS |
| `git diff --check` | PASS |

Smoke provenance：

| 字段 | 值 |
|------|-----|
| Model | `deepseek-v4-pro` |
| Prompt/agent version | `e89ff5031219dc7b73b78bb3d3540677766d0714-agents-match-installed` |
| Tool environment | `loopflow-cad13f678348b70beac9a45112b5c5695cc7a5ac-darwin-arm64` |
| Profile | `smoke`（每个 case 1 次） |
| Raw observations | gitignored `evals/results/plan003-smoke/` |

负向测试已经证明：

- claimed verdict/score 与实际产物冲突时，以实际产物为准
- 错误结果即使 claimed score 为 100，独立 evaluator 仍判定 FAILED
- submission 不能通过相对路径读取工作目录外文件
- staged InputBundle 不包含 `oracle/`

## 迁移期评估观测

使用 2026-07-19 为每个 entry 同步的五个运行目录离线生成 submission 并评分；没有重新调用 LLM。

| Entry | 独立 verdict 分布 | 分数范围/均值 | 结论 |
|-------|-------------------|---------------|------|
| bench-001 | 3 REPRODUCED, 2 PARTIAL | 80–90 / 86 | run_01/04 缺少部分支持 artifacts |
| bench-002 | 3 REPRODUCED, 1 PARTIAL, 1 FAILED | 5–95 / 73 | run_01 无结果表；run_05 缺 GO/KEGG 证据 |
| bench-003 | 5 REPRODUCED | 100–100 / 100 | protocol v2 远端首跑；全部科学与环境检查通过 |
| bench-004 | 4 REPRODUCED, 1 PARTIAL | 70–100 / 94 | run_04 未提交 Striatum 与 Hippocampus 对比表 |
| bench-005 | 5 REPRODUCED | 100–100 / 100 | 4 次 legacy PARTIAL 属于系统自评低估 |
| bench-006 | 4 REPRODUCED, 1 FAILED | 20–100 / 84 | run_05 无差异表达结果表，legacy REPRODUCED 属于 false positive |

bench-004 的旧 oracle 将 Drd2、Prox1 错放在 Cortex-vs-Thalamus 对比。新 rubric 按
Striatum-vs-Cortex、Hippocampus-vs-Cortex 分别验证，并允许方向相反的等价 contrast 或带
contrast 列的合并结果表。该修正依据输入计数与科学语义，不以提升 baseline 分数为目标。

bench-003 在 Linux x86_64 远端完成五次 protocol v2 首跑。run_04 曾因 Claude Code
未消费已完成后台任务的通知而停滞，终止原进程后从 Provision 恢复；恢复后的全部科学
产物仍由独立 evaluator 从 submission artifacts 重新评分。五次最终得分均为 100，
结果保存在 gitignored results 和本报告中，不作为冻结 benchmark baseline。

# 后续风险

1. 当前隔离保证 runner 只 stage `input/`，但不构成恶意被测程序的 OS 级沙箱；该项由 Plan 005 实现，不阻塞本 Plan 的评估分域验收。
2. PNG comparator 只验证格式与尺寸，不等价于科学图像内容比较；复杂图像仍需 entry-specific verifier。
3. 本轮仅完成 smoke 的单次采样；Prompt 或模型发布前仍需运行 regression/release profile，形成 3/5 次分布报告。
4. bench-001/002/004/005/006 来自既有产物离线重评；只有重编号前的 bench-003 在本轮重新执行了被测系统。

# 阶段结论

独立评分链路已经证明 golden 可以拆除且评分不依赖系统自评；tests/evals/benchmarks
三域边界、capability-oriented eval 和 release-gated baseline 均已落地。Plan 004 已完成
InputBundle fidelity 审查，本轮真实 LLM smoke 的 14 个 case 均取得有效通过结果。
Plan 003 标记 done；强隔离和发布级重复采样分别留给 Plan 005 与 release gate。
