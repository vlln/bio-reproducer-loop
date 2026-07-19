# Benchmark Changelog

All notable changes to the bio-reproducer benchmark suite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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