# Benchmark Changelog

All notable changes to the bio-reproducer benchmark suite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Adopted level-specific InputBundle fidelity and provenance requirements for L3, L4, and L5.
- Marked all existing entries as internal development inputs pending bundle-lock and cited-resource review.
- Marked bench-003 for L4 reconstruction because its current input is a derived summary and subset dataset.
- Added the runner-only bundle schema, validator, staging gate, and bench-001 migration pilot.
- Migrated all five constructed L3 entries and added bundle validation to the deterministic lint gate.
- Removed untraceable constructed PDFs and bench-006's byte-identical hidden data duplicate.
- Rebuilt bench-003 as L4 from the publisher article, PMC supplementary archive, official GEO outputs, an ENA raw-read resolver, and a frozen Taffeta source snapshot.
- Replaced the incorrect airway/DESeq2 oracle with the paper's Cuffdiff workflow, 316-gene result, and DEX-induced gene conclusions.

## [2.0.0] - 2026-07-19

### Added
- Engine-neutral `input/`, private `oracle/`, and `submission.json` protocol.
- Independent artifact evaluator with versioned claims, rubrics, submissions, and results.
- Release-gated baseline policy separated from gitignored development results.

### Changed
- Entry layout is now exactly `input/`, `oracle/`, and `metadata.yaml`.
- Scientific facts live in `claims.yaml`; scoring rules and tolerances live in `rubric.yaml`.
- Development and migration observations are no longer tracked as release baselines.

### Removed
- Entry-level `golden/`, `expected.yaml`, generated figures, and duplicated data directories.
- Protocol v1 evaluator runtime and system-owned final scoring.
- L1/L2 implementation tests from the public benchmark domain; those now live under `tests/` and `evals/`.

## [0.1.0] — 2026-07-19

### Added
- bench-001: 构造论文，DESeq2 差异表达分析（基础图表复现型）
- bench-002: 构造论文，多工具编排（DESeq2 + clusterProfiler + pathview）
- bench-003: 真实论文，airway 数据集（Himes et al. 2014, PLOS ONE）
- bench-004: 构造论文，跨平台转录组分析（Python + R 混合）
- bench-005: 构造论文，环境漂移 + 冲突信息注入
- bench-006: 构造论文，数据降级 + 故障注入
- Benchmark runner CLI（`bench-run run/eval/report`）
- Engine adapter（loopflow 桥接层）
- L1/L2 测试体系（7 个 Phase 单元测试 + 2 个集成测试）
