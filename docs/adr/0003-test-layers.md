---
title: ADR-0003 — 五层测试体系
description: 将测试体系分为两个域五个层次：L1-L2 内部测试（耦合于 bio-reproducer），L3-L5 黑盒基准（引擎无关）。
type: adr
status: accepted
created: 2026-07-15T00:00:00Z
---

# ADR-0003: 五层测试体系

---

## 背景

测试体系需要覆盖从单个 Agent 可靠性到真实环境端到端复现的全范围。单一层级的测试无法同时满足"快速反馈"和"真实能力测评"的需求。

---

## 决策内容

测试体系分为两个域、五个层次：

- **L1-L2（内部测试）**：耦合于 bio-reproducer 实现，服务于开发迭代
  - L1：单 Phase Agent 可靠性
  - L2：跨 Phase 信息流自洽性
- **L3-L5（黑盒基准）**：引擎无关，可成为公开标准
  - L3：构造论文，已知答案，最小外部依赖
  - L4：真实论文，冻结环境
  - L5：真实论文，真实环境

L1/L2 测 Agent 的业务逻辑正确性，通过真实 LLM 调用运行。Schema 合规（字段类型、枚举值、JSON 格式）是 loopflow workflow 运行时的基础设施保证，不属于 benchmark 测试范围。

---

## 备选方案

### 方案 A: 五层体系 (采用)

- 优点：覆盖全范围，内部/黑盒分离清晰，L3-L5 可独立发布
- 缺点：需要维护两层测试框架

### 方案 B: 仅 L3-L5 黑盒基准

- 优点：简单，直接测最终结果
- 缺点：无法快速定位问题（Phase 层面），开发迭代反馈慢

### 方案 C: 仅 L1-L2 内部测试

- 优点：快速反馈
- 缺点：无法衡量系统整体能力，不能作为公开基准

---

## 选择理由

- 内部测试和黑盒基准回答不同的问题，不可互相替代
- L1/L2 测"每个零件是否正常工作"，L3-L5 测"整车能不能跑"
- 两层分离后，L3-L5 可独立版本化、独立发布

---

## 验证

| 验证项 | 复现步骤 | 结论 | 经验 | 验证 Branch |
|--------|---------|------|------|------------|
| 五层体系可行性 | 实现 L3 bench-001 + L1 Reader 测试，验证两套体系能协同工作 | 待验证 | — | — |

---

## 后果

### 正面

- 开发时有快速反馈（L1/L2），发布时有标准化测评（L3-L5）
- L3-L5 可成为公开基准，吸引社区参与

### 负面

- 需要维护两套测试基础设施
- L3 的 golden fixtures 需要同时服务于 L1/L2 和 evaluator

---

## 约束范围

- 全部测试代码（`tests/`）
- 全部基准定义（`benchmarks/entries/`）
- 全部 runner 代码（`benchmarks/runner/`）

---

## 约束规则

| 规则编号 | 规则 | 适用范围 | 违反时如何检出 |
|----------|------|---------|--------------|
| AR-001 | L1/L2 测业务逻辑正确性，不测 schema 合规（schema 合规是 loopflow 的保证） | `tests/` | code review |
| AR-002 | L3-L5 不依赖 bio-reproducer 内部实现 | `benchmarks/` | 静态检查 expected.yaml/result.json 字段 |
| AR-003 | L3 每篇论文跑 N≥5 次，报告 verdict 分布；L4 跑 N≥1 次（推荐 2-3） | `benchmarks/runner/` | CI 配置检查 |
| AR-004 | Baseline 先行，关注变化方向而非绝对值 | 全部测评流程 | 报告格式检查 |
| AR-005 | Golden fixtures 保持粗粒度：L1 只比较关键结构化字段（status、schema 合规），不比较全文 | `tests/` + `benchmarks/entries/*/golden/` | code review |
| AR-006 | L3 构造论文的 golden/ 目录是单一来源，tests/fixtures/ 通过 symlink 引用，禁止复制 | `tests/fixtures/` | 目录结构检查 |
| AR-007 | L3 与 L4 之间通过 Tier 1 真实论文过渡（如 airway 数据集），先跑工程复杂度最低的真实论文 | `benchmarks/entries/` | — |

### 设计原则详解

**AR-005: Golden fixtures 粗粒度** — golden fixtures 与 prompt 和 output schema 紧耦合。每次修改 prompt 或 schema，golden fixtures 需同步更新。为避免维护成本失控：L1 不比较 plan.md 全文，只比较关键的结构化字段（status 是否正确、tool list 是否非空、schema 是否合规）。Golden fixtures 是"骨架"不是"全文"。

**AR-003: 非确定性度量** — LLM agent 的非确定性是根本性的。同一篇论文跑 5 次可能得到 3 种不同的 verdict。分布本身就是重要的系统行为指标——高方差说明 prompt 或流程不够稳定。

**AR-007: L3-L4 过渡** — L3（构造论文，数据 10MB，工具 1 个）和 L4（真实论文，数据可能 50GB，工具 5 个）之间存在巨大的工程复杂度鸿沟。选择 Tier 1 真实论文（工程复杂度极低）作为过渡，先跑这些确认工程链路通畅，再上真正的 L4。

**AR-004: Baseline 先行** — 第一轮跑完后，结果即为 baseline。之后每次改动，关注的是相对 baseline 的变化方向，而非分数的绝对值。分数本身不重要，变化方向重要。