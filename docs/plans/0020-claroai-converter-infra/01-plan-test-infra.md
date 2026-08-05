---
title: Plan 020 — ClaroAI Converter 测试基建增量
description: BL-011 TEST_INFRA 增量检查：核对既有基建覆盖 converter 测试需求，搭建 tests/fixtures/claroai/ 测试数据，确认 CI/门禁基线。
type: plan
status: pending
created: 2026-08-04T00:00:00Z
---

# 增量检查（非首次迭代，对照 phase-test-infra.md「增量检查」表）

## 检查项与结论

| 检查项 | 方法 | 结论 |
|--------|------|------|
| 既有测试基建 ADR 覆盖本轮需求 | 对照本轮新增模块（benchmarks/converters/claroai）与测试层需求，逐 ADR 核对 | **覆盖**：converter 为纯本地 Python 模块（无网络调用，PDF 抓取已删除），pytest + tests/unit 即可覆盖；无新框架/Mock 需求 → 不新增测试基建 ADR |
| 测试框架/Mock 支持新增模块 | 检查测试层入口与 fixture 需求 | **部分**：pytest 入口存在（tests/unit），缺 converter 测试数据 → 增量搭建 `tests/fixtures/claroai/`（见下） |
| 架构规则文件与最新契约一致 `[适用]` | 对照 Spec 模块划分表 | **N/A**：项目无架构规则工具（无 dependency-cruiser 等），无规则文件可更新 |
| CI/门禁仍正常 | 本地跑等价检查：`pytest tests/`（Python 3.12） | **通过**：125 passed, 4 skipped；CI 配置（.github/workflows/ci.yml，Python 3.10）无漂移；frontmatter/YAML 检查覆盖新增文档与后续 converter 输出（benchmarks/entries） |

## 增量搭建：测试数据工厂

- 目标：`tests/fixtures/claroai/`，converter 单元测试输入（AC-0009-N-5 转录正确性、golden 对比、bundle gate）
- 样本：paper_01（计算论文，D1=2/D2=0/D3=1，4 数据引用 + 5 代码引用）与 paper_10（湿实验，is_computational=false），仅 metadata/extraction/scores JSON
- 来源：claroai-bench HF 快照（CC-BY-4.0），README 注明来源与 license；测试不联网、不依赖 `~/Project/claroai-bench`

## 自证（增量门禁）

| 门禁项 | 自证方法 | 预期 |
|--------|---------|------|
| fixture 数据可用 | 脚本解析两样本的 metadata/extraction/scores，核对字段 | 全部可解析，字段齐全 |
| 测试基线 | `python3.12 -m pytest tests/` | 125 passed（与 docs/README 记录一致） |

## 约束

- 不编写具体测试用例（DEVELOP 的 Plan 021 编写）
- 不修改 Spec/业务 ADR；测试基建 ADR 无新增
- 本地默认 python3 为 3.9（不满足项目 ≥3.10 要求），测试用 `/opt/homebrew/bin/python3.12`
