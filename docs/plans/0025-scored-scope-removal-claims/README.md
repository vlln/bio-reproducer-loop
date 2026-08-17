## 执行容器 0025 — scored_scope 删除与 ClaroAI claims 模式（FIX）

| 文件 | 类型 | 状态 |
|------|------|------|
| [01-plan-scored-scope-removal-claims.md](01-plan-scored-scope-removal-claims.md) | Plan | done |
| [01-report-scored-scope-removal-claims.md](01-report-scored-scope-removal-claims.md) | Report | done |

状态：DONE（2026-08-12）。

## 概述

完整修复路径：删除 `scored_scope` 机制（评分维度代码泄漏 + 任务降级载体），ClaroAI
entry 恢复 claims 模式（D5 数值声明 + 容差 comparator，D1–D3 为辅助证据），6 篇校准
run 离线重评并与作者 D5 校准对照。

## 变更摘要

- converter v0.2.0：`reproduction_target` + 自然语言 `task`；D5 claims 转录（4 种
  evidence 格式）；`check_claim` 容差/阈值比较；无 `d1_d3_audit` 发射。
- 35 个 bench-200+ entry 重生成（数据零漂移）+ bench-100 迁移 + bench-223 AUROC 阈值
  claim 手工补。
- adapter 改读 `metadata.task`；validator CC-002 rev.（禁 scored_scope，必填
  reproduction_target/task）；evaluate_run.py 支持 claims evidence。
- 测试 141 passed / 4 skipped；42 entry 全过 bundle gate。
- 6 篇离线重评：bench-220 REPRODUCED 100、bench-221 65、bench-203 PARTIAL 30、
  bench-200/223/229 FAILED（修正审计模式高估）。

## 后续 backlog（不在本 Plan 范围）

1. 无 D5 evidence 的 4 篇论文 claims 人工补全（bench-208/209/222/225）。
2. 全 35 篇 claims 逐篇 fidelity review。
3. 系统侧执行层优化：audit/claims 任务的 provision 最小化（避免越界建全量环境、
   整批省 ~10h）——属 loop 执行纪律，需独立 Plan。
