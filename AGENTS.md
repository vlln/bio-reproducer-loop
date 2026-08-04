## 一、项目简介

bio-reproducer 包含三个部分：

1. **论文复现系统** — AI Agent 驱动的 7 阶段工作流。输入论文 PDF/DOI，自动完成信息提取、环境搭建、数据获取、分析运行、结果验证。基于 [loopflow](https://github.com/vlln/loopflow) 引擎。
2. **软件测试与内部评测** — `tests/` 提供确定性工程门禁；`evals/` 使用真实 LLM 验证单 Agent 业务逻辑和跨 Phase 信息流。
3. **公开 benchmark（L3-L5）** — 引擎无关、独立评分的论文复现基准，可独立发布，被任何复现系统采用。

---

## 二、文档体系

### 文档类型

| 文档 | 用途 |
|------|------|
| 本文档（AGENTS.md） | 项目入口地图 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 编码/Commit/文档/测试规范 |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录（Keep a Changelog） |
| [docs/vision.md](docs/vision.md) | 全局顶层愿景：业务目标、用户范围、长期理想形态（有 frontmatter） |
| [docs/spec/](docs/spec/) | Spec：需求规格。用户故事、模块划分、数据模型 |
| [docs/interface/](docs/interface/) | 接口定义：入参/出参/错误码 |
| [docs/ac/](docs/ac/) | 验收标准（AC）：正常/边界/异常/失败四场景。测试唯一权威依据 |
| [docs/adr/](docs/adr/) | 架构决策记录：技术选型、方案对比、取舍 |
| [docs/plans/](docs/plans/) | 执行容器：对应一个 Git 分支，内含多个最小执行单元（Plan + Report 成对） |
| [docs/README.md](docs/README.md) | 子目录索引 + **当前系统状态** |
| 各级 README.md | 该目录的索引和状态说明 |

### 文档目录结构

```
项目根目录
├── AGENTS.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── docs/
│   ├── README.md          # 索引 + 当前系统状态
│   ├── vision.md
│   ├── spec/
│   │   ├── README.md
│   │   └── 0001-benchmark.md
│   ├── interface/
│   │   ├── README.md
│   │   └── 0001-benchmark-protocol.md
│   ├── ac/
│   │   ├── README.md
│   │   ├── 0001-benchmark-layers.md
│   │   └── 0002-benchmark-runner.md
│   ├── adr/
│   │   ├── README.md
│   │   ├── 0001-language.md
│   │   ├── 0002-benchmark-format.md
│   │   ├── 0003-test-layers.md
│   │   ├── 0005-independent-evaluation.md
│   │   └── 0006-test-eval-domains.md
│   └── plans/
│       └── README.md
├── benchmarks/
│   ├── paper-entries.md
│   └── entries/
├── loops/bio-reproducer/  # 论文复现系统
├── tests/                 # 确定性软件测试
└── evals/                 # 真实 LLM 内部行为评测
```
