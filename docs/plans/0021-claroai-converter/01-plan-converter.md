---
title: Plan 021 — ClaroAI Converter 实现
description: 实现 claroai2bench converter（L5 locator entry 生成）、bundle validator 扩展（CC-002/003/004）、AC-0009 四场景测试；生成 35 个 entry 并 validate 全过。
type: plan
status: pending
created: 2026-08-04T00:00:00Z
---

# ClaroAI Converter 实现

## Context

BL-011 DESIGN 已冻结：Spec 0001 v5（审计模式小节）、ADR-0010（converter 转标准 entry、
L5 DOI/PMID locator、不附带论文全文）、AC-0009（四场景）、Interface 0002（claroai2bench
CLI 与审计评分协议）。TEST_INFRA 已提供 fixture（`tests/fixtures/claroai/`，paper_01 +
paper_10）。spike 验证（spike/0010-claroai-converter）确认转换链路与 L5 locator 版
bundle gate 可行。

## Request

1. `benchmarks/converters/claroai/`：`converter.py`（核心转换）+ `cli.py`（claroai2bench
   CLI，契约见 Interface 0002）+ `verify_template.py`（每 entry 生成 `oracle/verify.py`
   的模板）
2. bundle validator 扩展（`benchmarks/runner/bundle_validator.py`）：
   - CC-002：bench-200+ entry 的 `metadata.scored_scope` 必须为 `d1_d3_audit`，否则 INVALID_BUNDLE
   - CC-003：bench-200+ entry 的 `oracle/rubric.yaml` 不得含作者真值派生键（精确名单：
     顶层 `author_score`/`author_scores`/`calibration`/`ground_truth`/`d1`/`d2`/`d3`），否则 INVALID_BUNDLE
   - CC-004：bench-200+ entry 的 primary paper 必须 external locator（拒绝 bundled paper），否则 INVALID_BUNDLE
3. 测试 `tests/unit/test_claroai_converter.py`（TDD，用 fixture，不联网）覆盖 AC-0009
   N-1/N-2/N-3/N-5、B-2/B-3、E-1/E-2、F-1/F-4
4. 生成 35 个 entry（bench-200~234，`--no-fetch` 语义即本版：无全文抓取）到
   `benchmarks/entries/`，`bench-run validate-entry` 全部通过
5. provenance：`benchmarks/entries/claroai-converter-provenance.json`（快照 ref、版本、ID 映射）

## Output Format

- converter 模块（含 CLI）；validator 扩展（含单测）；`oracle/verify.py` 模板
- `benchmarks/entries/bench-200..234/`：metadata.yaml + bundle.yaml + input/paper/locator.md +
  oracle/{claims.yaml,rubric.yaml,verify.py}
- `benchmarks/entries/claroai-converter-provenance.json`

## Constraints

- 不附带论文全文文件（版权决策，ADR-0010 §5）；primary paper 一律 external DOI/PMID locator
- 测试不联网、不依赖 `~/Project/claroai-bench`（只用 `tests/fixtures/claroai/`）
- 不修改 accepted 文档（Spec/ADR/AC/Interface）；validator 扩展不改变既有 entry（bench-001~100）行为
- 转录必须确定性可重放（同快照 → 字节一致，AC-0009-N-2）
- per-reference ground truth 从 evidence 文本解析主代码仓库（spike 发现的精度问题）；
  无法判定的引用标 `unknown`，不编造（AC-0009-B-3）

## Checkpoint

- `python3.12 -m pytest tests/` 全绿（含新增 converter/validator 测试）
- `make bench-validate` 对既有 + 新增 entry 全部通过（35 个 bench-200+ + 既有）
- AC-0009 各场景有对应测试断言
- converter 对 fixture 快照两次转换字节一致

## Steps

1. TDD：写 `test_claroai_converter.py` + validator 扩展测试（红）
2. 实现 converter（metadata/bundle/claims/rubric/verify 生成）与 CLI（绿）
3. 实现 validator 扩展（CC-002/003/004），跑通 F-1/F-4（绿）
4. 用本地 `~/Project/claroai-bench` 快照生成 35 个 entry 到 benchmarks/entries/
5. `bench-run validate-entry` 全过 + provenance 生成
6. Report + 合并回 develop
