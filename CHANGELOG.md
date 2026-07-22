# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- 将确定性软件测试、真实 LLM 内部评测和公开 benchmark 拆分为三个域
- Benchmark 改为 input、submission、private oracle 三方协议，最终评分由独立 evaluator 生成
- 废弃多用途 golden fixture，改用 oracle、fixture、exemplar 和 baseline 四类资产
- 支持从既有 `repro-data` 补建 submission，并保留 legacy 自评用于校准
- 修正 bench-004 的跨脑区对比 oracle；使用独立 evaluator 重评 bench-004 至 bench-006
- 内部 eval 改为 capability case + execution profile，移除多用途 exemplar 和硬编码重复次数
- 清理 protocol v1 entry 残留，拆分科学 claims 与评分 rubric
- 使用独立 evaluator 完成既有 artifacts 的迁移期离线重评
- 完成原 bench-003 的五次远端首跑；结果保留为开发期观测，不建立发布级 baseline
- baseline 改为 release-gated：entry、oracle 与协议冻结前不追踪历史分数
- 退回 DESIGN，提出 L3/L4/L5 分层 InputBundle、runner-only bundle lock 和 provenance 契约
- 完成首批六个 entry 的本地材料审计；原 bench-003 标记为需要重建的假 L4 输入
- 冻结 runner-only bundle lock 契约，实现 schema、validator、staging gate 和 bench-001 pilot
- 完成五个构造 L3 entry 的 bundle 迁移，清理无 provenance PDF 与 bench-006 隐藏重复数据
- 从 PLOS/PMC、GEO、ENA 和 Taffeta 原始材料重建真实论文 entry，重编号为 bench-100，修正 DESeq2/airway 方法误归因并通过 L4 bundle gate
- 划分 entry ID 命名空间：001-099 用于构造论文，100-999 用于真实论文，并由 bundle validator 强制校验
- 完成六个 entry 的人工 fidelity review；将宿主机强隔离移交 Plan 005，将 L4 可执行环境冻结保留在 Plan 002
- 完成 12 个 component 与 2 个 handoff 的真实 LLM smoke，并修复标量断言、blocked 文本误判与 Package phase-only 恢复

## [0.1.0] — 2026-07-19

### Added
- Benchmark 与测试体系设计（L1-L5）
- devloop 文档体系接入
- 6 个初始 benchmark entries（当时编号 bench-001 ~ bench-006）
- Benchmark runner CLI + engine adapter
- L1/L2 测试骨架（7 个 Phase 单元测试 + 2 个集成测试）
- CI 静态检查（YAML、frontmatter、JSON Schema）
