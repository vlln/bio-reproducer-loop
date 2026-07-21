# bio-reproducer

AI Agent 驱动的生物信息学论文复现系统，配套内部测试体系和公开 benchmark。

## 项目组成

| 部分 | 路径 | 说明 |
|------|------|------|
| 复现系统 | `loops/bio-reproducer/` | 7 阶段 workflow，输入论文自动完成复现全流程 |
| 软件测试 | `tests/` | 确定性工程门禁，不调用真实 LLM/网络 |
| 内部评测 | `evals/` | 真实 LLM 的单 Phase 与跨 Phase 行为评测 |
| 公开 benchmark | `benchmarks/` | L3-L5 引擎无关的论文复现基准，6 个 entry |

## 版本

| 组件 | 版本 |
|------|------|
| 项目 | `0.1.0` |
| Benchmark | `0.1.0`（独立版本） |

## 前置依赖

- [pixi](https://pixi.sh) — 环境和依赖管理
- [loop](https://github.com/vlln/loopflow) — workflow 运行时
- Python ≥ 3.10

## 复现系统

```bash
# 安装
git clone git@github.com:vlln/bio-reproducer-loop.git
mkdir -p ~/.loopflow/loops
cp -r bio-reproducer-loop/loops/bio-reproducer ~/.loopflow/loops/bio-reproducer

# 安装依赖
cd ~/.loopflow/loops/bio-reproducer
pixi run install-skit
pixi run install-mip
pixi run install-skills

# 运行复现
pixi shell
loop run bio-reproducer --args '{"paper_path": "paper.pdf", "language": "zh"}'
```

### 阶段

| Phase | 名称 | 描述 |
|-------|------|------|
| 1 | Reader | 提取论文声明，创建复现计划 |
| 2 | Bootstrap | 检查系统环境 |
| 3 | Provision | 部署工具容器 |
| 4 | Data | 下载分析数据 |
| 5 | Run | 运行分析流水线 |
| 6 | Validate | 验证复现结果 |
| 7 | Package | 打包复现产物 |

## Benchmark 系统

```bash
# 运行 L1 单元测试
make test-l1

# 运行 L2 集成测试
make test-l2

# 运行 L3 benchmark（5 次）
make bench-l3

# 评估结果
python3 -m benchmarks.runner.cli eval --entry bench-001

# 生成报告
python3 -m benchmarks.runner.cli report
```

### 测试层级

| 层级 | 说明 | 路径 |
|------|------|------|
| L1 | 单 Phase Agent 业务逻辑 | `tests/unit/` |
| L2 | 跨 Phase 信息流 | `tests/integration/` |
| L3 | 构造论文端到端（5 entries） | `benchmarks/entries/` |
| L4 | 真实论文 + 冻结材料（1 entry，审查中） | `benchmarks/entries/bench-003/` |
| L5 | 生产基准（规划中） | — |

### Benchmark Entries

| Entry | 场景 | 难度 | 期望 |
|-------|------|------|------|
| bench-001 | 差异表达分析（DESeq2） | easy | REPRODUCED |
| bench-002 | 多工具编排（DESeq2 + clusterProfiler + pathview） | easy | REPRODUCED |
| bench-003 | Himes et al. 2014 原始材料；GEO Cuffdiff/FPKM 结果验证 | hard | UNDER REVIEW |
| bench-004 | 跨平台转录组（Python + R） | medium | REPRODUCED |
| bench-005 | 环境漂移 + 冲突信息 | medium | REPRODUCED |
| bench-006 | 数据降级 + 故障注入 | medium | REPRODUCED |

## 文档

- [AGENTS.md](AGENTS.md) — 项目入口地图
- [CONTRIBUTING.md](CONTRIBUTING.md) — 编码/Commit/分支规范
- [CHANGELOG.md](CHANGELOG.md) — 版本变更记录
- [docs/](docs/) — 设计文档（vision, spec, ADR, AC, plans）

## 结构

```
bio-reproducer/
├── loops/bio-reproducer/     # 复现系统（7 阶段 workflow）
│   ├── workflow.py
│   ├── pixi.toml
│   └── agents/
├── tests/                    # L1-L2 内部测试
│   ├── unit/
│   └── integration/
├── benchmarks/               # L3-L5 公开 benchmark
│   ├── VERSION
│   ├── entries/              # 6 个论文包
│   └── runner/               # 执行器 + 适配器
├── docs/                     # devloop 设计文档
└── .github/workflows/        # CI 静态检查
```
