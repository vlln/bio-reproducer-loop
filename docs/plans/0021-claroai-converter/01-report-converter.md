---
title: Report 021 — ClaroAI Converter 实现
description: converter 实现完成：35 个 L5 审计模式 entry 生成并全部通过 bundle gate；validator 扩展 CC-002/003/004；测试 136 passed。
type: report
status: complete
created: 2026-08-04T00:00:00Z
---

# 实现结论

## 交付物

| 交付物 | 位置 | 状态 |
|--------|------|------|
| Converter 核心 | `benchmarks/converters/claroai/converter.py` | 完成 |
| CLI | `benchmarks/converters/claroai/cli.py`（claroai2bench，Interface 0002 契约） | 完成 |
| verify.py 模板 | `converter.py` 内 `VERIFY_TEMPLATE`，每 entry 生成 `oracle/verify.py` | 完成 |
| Validator 扩展 | `bundle_validator.py` `_validate_audit_mode`（CC-002 scored_scope / CC-003 rubric 作者真值键 / CC-004 primary external） | 完成 |
| 测试 | `tests/unit/test_claroai_converter.py`（11 用例，AC-0009 N-1/N-2/N-3/N-5、B-2/B-3、E-1/E-2、F-1/F-4） | 完成 |
| Entry 产物 | `benchmarks/entries/bench-200..234`（35 个 L5 entry）+ provenance | 完成 |

## 验证结果（Checkpoint 逐项）

| Checkpoint | 结果 | 证据 |
|------------|------|------|
| pytest 全绿 | **PASS** | `python3.12 -m pytest tests/` = **136 passed, 4 skipped**（125 基线 + 11 converter 新增） |
| bench-validate 全过 | **PASS** | `make bench-validate`：既有 bench-001~100 + 新增 bench-200~234 全部 VALID（L5） |
| AC-0009 场景测试 | **PASS** | N-1（生成+gate）、N-2（确定性字节一致）、N-3（locator↔DOI）、N-5（转录）、B-2（湿实验）、B-3（evidence 缺失→unknown）、E-1（快照损坏）、E-2（ID 冲突阻止）、F-1（rubric 作者真值键→INVALID_BUNDLE）、F-4（缺 scored_scope→INVALID_BUNDLE） |
| 确定性 | **PASS** | test_n2_deterministic_output：同快照两次转换字节一致 |
| 审计评分闭环（集成） | **PASS** | 真实 bench-200 + 生成 verify.py：正确判断 → REPRODUCED 100；误判 GSE308855 → PARTIAL 50（check 附原因） |

## 实现决策记录

1. **标识 locator**：DOI 优先，arXiv 次之（paper_23 无 DOI/PMID，arXiv 2111.00595），PMID 兜底；Interface 0001 L5 本就允许 arXiv locator。paper_33 无 PMID 但走 DOI。
2. **主代码仓库判定**（spike 精度发现）：只按作者 justification/evidence 文本匹配 URL；无匹配 → 全部 `unknown`（不猜，AC-0009-B-3）。paper_01 主仓库 hollow、4 个工具仓库 unknown。
3. **无 URL 代码引用**：不生成 bundle 资源（无法定位 source），claims 保留 `unknown` 条目（"available on request" 类引用）。
4. **validator 扩展范围**：以 entry_id ≥ 200 识别审计模式区间（与 ADR-0010 §4 "bench-200 起"一致），对既有 entry（bench-001~100）零影响（回归测试确认）。
5. **结构测试契约对齐**：`test_protocol_v2_entry_layout_is_minimal` 的 oracle 目录断言过严（只允许 claims+rubric），而 Interface 0001 OracleBundle 明确允许可选 verify.py；已修正为 superset 检查并遍历全部 entry（含 bench-200+）。

## 遗留发现（后续迭代）

- `claims.schema.json` 只覆盖"科学事实"型 claims（实验设计/方法/定量结果），审计模式 claims（data_references/code_references/calibration）结构不同，未被 schema 覆盖。entry 发布前需为审计模式 claims 扩展 schema 或建独立 schema（当前 tests 不检查 bench-200+ 的 claims schema，不阻塞）。
- `make lint` 对 `docs/backlog.md` 报 frontmatter WARN（devloop 规定 backlog 无 frontmatter，lint 脚本未排除）——既有缺陷，非本轮引入。
- BL-010（README entries 表滞后）在 35 个 entry 落地后更突出，建议后续 backlog 排期。
