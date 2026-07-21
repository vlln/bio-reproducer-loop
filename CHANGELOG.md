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
- 完成 bench-003 的五次远端首跑；结果保留为开发期观测，不建立发布级 baseline
- baseline 改为 release-gated：entry、oracle 与协议冻结前不追踪历史分数
- 退回 DESIGN，提出 L3/L4/L5 分层 InputBundle、runner-only bundle lock 和 provenance 契约
- 完成 bench-001 至 bench-006 的本地材料审计；bench-003 标记为需要重建的假 L4 输入

## [0.1.0] — 2026-07-19

### Added
- Benchmark 与测试体系设计（L1-L5）
- devloop 文档体系接入
- 6 个 benchmark entries（bench-001 ~ bench-006）
- Benchmark runner CLI + engine adapter
- L1/L2 测试骨架（7 个 Phase 单元测试 + 2 个集成测试）
- CI 静态检查（YAML、frontmatter、JSON Schema）
