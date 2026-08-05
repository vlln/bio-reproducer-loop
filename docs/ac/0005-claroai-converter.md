---
title: AC 009 — ClaroAI Converter
description: 验收 ClaroAI-Bench 任务到标准 entry（L5，DOI/PMID locator，不附带论文全文）的确定性转换、oracle 转录与审计评分闭环（BL-011 / ADR-0010）。
type: ac
status: proposed
created: 2026-08-04T00:00:00Z
---

# AC-0009: ClaroAI Converter

验证 `benchmarks/converters/claroai/` 将 claroai-bench `papers/paper_XX/` 确定性转换为
标准 entry（metadata.yaml/bundle.yaml/input/oracle），且审计模式评分闭环可用。

## 正常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0009-N-1 | claroai-bench 快照含 35 篇 paper_XX（含 2 篇湿实验） | 运行 converter 生成全部 entry（bench-200 起） | 35 个 entry 生成，`bench-run validate-entry` 全部通过（L5，primary paper 为 external DOI/PMID locator，无 bundled 论文文件） | 自动化 |
| AC-0009-N-2 | 同一快照 | 连续两次转换同一论文 | 两次输出字节一致（metadata/bundle/claims/rubric），确定性可重放 | 自动化 |
| AC-0009-N-3 | 生成的审计模式 entry（primary paper 为 DOI locator） | 被测系统（或等价探针）经 DOI/PMID 解析获取论文全文 | 系统可获得 original 全文（如 EuropePMC JATS XML），记录解析来源与结果；获取失败按 external blocked 处理（见 B-1） | 自动化 + 人工审查 |
| AC-0009-N-4 | 生成的审计模式 entry | 构造符合 ground truth 的 mock submission 运行 evaluator | rubric checks 按 `python_verify` 判定通过/失败，verdict/score 正确 | 自动化 |
| AC-0009-N-5 | converter 转录 claims | 对照 paper_XX/scores.json 的 evidence 逐项核查 | 无漂移（ground truth 状态与 evidence 一致） | 自动化 |

## 边界场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0009-B-1 | 论文全文在运行时不可获取（非开放获取/网络失败） | 被测系统尝试经 DOI/PMID 获取全文 | 系统记录 `external` blocked（BR-004），该 run 不计入系统失败；entry 本身有效（L5 primary paper 为 locator，不依赖 bundled 文件） | 自动化 |
| AC-0009-B-2 | 湿实验论文（is_computational=false） | 生成 entry | 正常生成，scored_scope 同为 `d1_d3_audit`，claims 不含 D4/D5 虚构值 | 自动化 |
| AC-0009-B-3 | scores.json 某维度 evidence 缺失 | 转录 claims | 该引用状态标记 `unknown`，不编造 ground truth，rubric 对应 check 为 NA | 自动化 |
| AC-0009-B-4 | 同一论文未来生成 D5 复现 entry | 分配 entry ID | 新 ID 不与既有 bench-200+ 冲突，两个 entry 独立 bundle/oracle | 自动化 |

## 异常场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0009-E-1 | 快照文件缺失或 JSON 格式损坏 | 运行 converter | 报错并列出受影响论文清单，不静默跳过、不产出半成品 entry | 自动化 |
| AC-0009-E-2 | `locator.md` 与 bundle primary paper 的 DOI/PMID 不一致 | 运行 converter/bundle 校验 | 报错并阻止生成/校验通过，明确提示标识符冲突 | 自动化 |
| AC-0009-E-3 | converter 输出缺 provenance（快照版本） | 校验输出目录 | provenance 检查失败，明确提示快照 hash | 自动化 |

## 失败场景

| 编号 | 前置条件 | 操作步骤 | 预期结果 | 验证方式 |
|------|---------|---------|---------|---------|
| AC-0009-F-1 | rubric 含作者真值派生键（如顶层 `calibration`、`author_score`），或 bundle 含 FORBIDDEN_KEYS 字段 | 执行 bundle validator（扩展：校验 bundle 的同时按 CC-003 精确名单扫描 `oracle/rubric.yaml`） | 返回 INVALID_BUNDLE（BR-018 / CC-003；作者分数仅允许存于 claims.yaml calibration 段，协议合法键 `expected_verdict`/`verdict_*`/`checks` 不受影响） | 自动化 |
| AC-0009-F-2 | entry 声明 L5 但 primary paper 非稳定 locator（如附带论文全文文件或 source 缺失） | 执行 fidelity gate | 拒绝进入 L5（CC-004），不建立 baseline | 自动化 + 人工审查 |
| AC-0009-F-3 | 同一快照两次转换输出漂移 | 运行 golden 对比测试 | 测试失败，converter 不得发布 | 自动化 |
| AC-0009-F-4 | 审计模式 entry 的 metadata scored_scope 缺失或非 `d1_d3_audit` | 执行 bundle validator | 返回 INVALID_BUNDLE（CC-002） | 自动化 |
