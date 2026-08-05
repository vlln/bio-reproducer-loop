---
title: Report 022 — ClaroAI SYSTEM_TEST
description: BL-011 系统级验证结论：136 确定性测试全绿、35-entry 审计评分冒烟全过、错判拦截验证；正式 VM 远端校准运行因 system artifact 缺口记录为遗留。
type: report
status: complete
created: 2026-08-04T00:00:00Z
---

# SYSTEM_TEST 结论

## 验证结果

| 层 | 结果 | 证据 |
|----|------|------|
| 集成/确定性测试 | **PASS** | `python3.12 -m pytest tests/` = **136 passed, 4 skipped**（125 基线 + 11 converter 新增） |
| Bundle gate（全量） | **PASS** | `make bench-validate` = **42 VALID**（既有 7 + 新增 bench-200~234 全部 L5） |
| 35-entry 评分冒烟 | **PASS** | ground-truth 一致 submission → **35/35 REPRODUCED(100)**（每 entry 的 verify.py/claims/rubric 均可加载执行） |
| 错判拦截 | **PASS** | bench-205 误判 NCT06119308 可下载 → PARTIAL 50，check 附原因 |
| 确定性重放 | **PASS** | converter 同快照两次转换字节一致（test_n2） |

## 远端校准运行

- 尝试在 `gs@172.16.209.237` 跑 `bench-run run --entry bench-200`：
  - formal VM backend：**WORKER_UNAVAILABLE**（worker/system 配置未装配——Plan 013 后 plan 专属大文件已清理，system artifact 需重建，属基建缺口，非本轮引入）
  - docker-validation backend：**INVALID_EXECUTION_ENVIRONMENT**（缺 sandbox 镜像，需构建含被测系统的镜像）
- 结论：**正式 VM 校准运行（disposable VM 全 7 阶段真实复现）列为遗留**，需重建 system artifact + runtime（Plan 013 级基建操作，数小时），见 backlog BL-012。
- 远端已同步至 `4ed12cb`（35 entry + converter 就绪），随时可跑。

## 遗留与建议

| 项 | 说明 | 建议 |
|----|------|------|
| BL-012（新） | 正式 VM 校准运行阻塞：system artifact/runtime/sandbox 镜像需重建 | backlog 排期，按 Plan 013 流程重建后跑 bench-200~205 抽样校准，对照 claroai-bench 作者 D1–D3 ground truth |
| claims.schema.json | 审计模式 claims（data/code_references/calibration）不被既有 schema 覆盖 | entry 发布前扩展 schema 或建审计模式专用 schema |
| lint 脚本 | `docs/backlog.md` frontmatter WARN（devloop 规定 backlog 无 frontmatter） | 修 lint 排除规则 |

## 校准意义

35 个 entry 的 `calibration` 段保留了作者 D1–D3 分数；正式 VM 运行产出 submission 后，
独立 evaluator 的 verdict/score 与作者分数对照即为"确定性独立评分 vs 多模型主观评分"
的校准观测（ADR-0010 正面后果之一），留给 BL-012 执行时完成。
