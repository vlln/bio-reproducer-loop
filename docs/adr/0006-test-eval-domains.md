---
title: ADR-0006 — 测试、内部评测与公开基准分域
description: 将确定性软件测试、真实 LLM 行为评测和公开黑盒 benchmark 拆为三套生命周期与门禁。
type: adr
status: accepted
created: 2026-07-19T00:00:00Z
---

# ADR-0006: 测试、内部评测与公开基准分域

## 背景

当前 L1 被命名为 unit test，却调用真实 LLM、loopflow 和系统工具；L2 同时承担
协议集成与 Agent 语义传递评测。单一 L1-L5 轴混合了测试范围、执行真实性和发布
对象，导致速度、确定性和门禁含义不清。

本 ADR supersede ADR-0003、ADR-0004，以及 ADR-0001 中关于 L1/L2 测试框架的部分。

## 决策内容

项目拆分为三个域：

| 域 | 目录 | 真实 LLM/工具 | 主要用途 | 默认 PR 门禁 |
|----|------|---------------|----------|--------------|
| 软件测试 | `tests/` | 禁止 | 确定性代码与契约验证 | 是 |
| 内部行为评测 | `evals/` | 允许 | Prompt、Phase 和 handoff 质量回归 | 否，按策略触发 |
| 公开 benchmark | `benchmarks/` | 允许 | 系统级、引擎无关能力比较 | 否，独立发布 |

`tests/unit/` 使用 fake executor 测试 evaluator、adapter、runner、解析和状态机。
`tests/contract/` 使用录制或人工构造的 fixture 测试 Phase 输入输出协议、状态传播和
错误处理。任何依赖真实 LLM、网络、容器安装或论文分析的用例都不属于 unit test。

`evals/component/` 评测单 Phase 的业务行为；`evals/handoff/` 评测多个 Phase 之间
的语义传递。评测需要重复运行并报告分布，不以一次 `pytest PASS` 表达能力。

内部 eval 的覆盖单位是能力分支和失败模式，而不是 benchmark entry。每项能力至少由一个
代表 case 覆盖；只有 entry 引入新能力或暴露真实回归时才抽取新 case。采样次数由 smoke、
regression、release profile 决定，不在 case 实现中硬编码。

实现语言继续使用 Python；确定性测试继续使用 pytest。该技术选择不意味着真实 LLM
行为评测属于 pytest unit test。

## Fixture 分类

| 名称 | 含义 | 是否唯一正确答案 | 是否参与公开评分 |
|------|------|------------------|------------------|
| oracle | 独立科学真值与评分规则 | 是 | 是 |
| fixture | 构造的确定性输入或上游状态 | 否 | 否 |
| exemplar | 一个经过人工确认的合法输出示例 | 否 | 否 |
| baseline | 特定系统、模型、Prompt 和环境的历史观测 | 否 | 仅用于回归比较 |

禁止使用 `golden` 同时表达上述多个概念，也禁止通过 symlink 让内部 eval 直接复用
公开 benchmark 的完整参考产物。

内部 eval 的上游 Phase 文件统一视为 fixture。Exemplar 不得作为完整输出匹配目标，也不得
同时充当下游输入；没有人工校准或展示用途的 exemplar 不进入仓库。

## Phase 评测原则

| Phase | 独立评测证据 |
|-------|--------------|
| Reader | claims 召回率、精确率、参数归属和幻觉数 |
| Bootstrap | Agent 报告与独立环境探针的差异 |
| Provision | 需求覆盖、版本约束和替代方案有效性 |
| Data | 数据身份、checksum、维度和错误来源处理 |
| Run | 实际结果表、统计方向、容差和图表产物 |
| Validate | 与独立 evaluator 的一致性和自评校准误差 |
| Package | 在干净环境中的 `run.sh` smoke test |

## 后果

### 正面

- `pytest` 重新代表快速、确定性的工程反馈。
- LLM 非确定性通过分布和 baseline 表达，不再伪装成 unit test。
- 内部 eval 与公开 benchmark 可以独立演进。

### 负面

- 当前 `tests/unit/` 需要迁移或重写。
- 需要维护 fake executor 和 eval reporter。
- Prompt 回归不再由普通 CI 自动覆盖，需要单独执行策略。

## 约束规则

| 规则编号 | 规则 | 检出方式 |
|----------|------|----------|
| AR-001 | `tests/` 不调用真实 LLM、网络或容器部署 | pytest marker 与静态检查 |
| AR-002 | `evals/` 每个用例记录模型、Prompt、工具和环境版本 | eval result schema |
| AR-003 | 非确定性 eval 使用重复运行和分布统计 | reporter 检查 |
| AR-004 | 缺失产物、进程失败和 Phase 被跳过不得视为成功 | negative tests |
| AR-005 | baseline 与 oracle 分开版本化 | 目录结构检查 |
| AR-006 | eval 按 capability/failure mode 覆盖，不按 entry × Phase 展开 | coverage matrix 检查 |
| AR-007 | eval 重复次数只来自 execution profile | runner 单元测试与静态检查 |

## 验证

| 验证项 | 复现步骤 | 预期结论 |
|--------|----------|----------|
| 确定性门禁 | 断网运行 `pytest tests/` 两次 | 两次结果一致 |
| 行为评测 | 同配置运行 component eval 五次 | 报告成功率、均值和方差 |
| 假绿拦截 | fake executor 返回非零或不生成产物 | 测试明确失败 |
