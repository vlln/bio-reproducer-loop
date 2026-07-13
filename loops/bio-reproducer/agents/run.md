---
name: run
description: Phase 5 — 运行分析流水线
extends: _base
output:
  type: object
  properties:
    payload:
      type: object
      properties:
        steps:
          type: array
          description: Pipeline steps executed
          items:
            type: object
            properties:
              step: {type: string}
              status: {type: string, enum: [success, failed, skipped]}
              metrics: {type: object, description: "Key metrics from this step"}
        figures:
          type: array
          description: Figure generation status
          items:
            type: object
            properties:
              panel: {type: string}
              status: {type: string, enum: [generated, partial, blocked]}
              path: {type: string}
              source: {type: string, enum: [author_code, author_notebook, handwritten_fallback, N/A]}
        pipeline_duration:
          type: string
          description: Total pipeline execution time
      required: [steps, figures]
---
# Phase 5: Run

## 目标
使用 Nextflow 作为编排层运行分析 pipeline。Nextflow 负责输入/输出、
容器、资源、resume、日志和并行调度；具体分析逻辑应由论文指定的
脚本、工具、notebook、命令或已有 workflow 承担。

## 输入
- `01_plan/plan.md` - 步骤和参数
- `02_bootstrap/bootstrap.md` - 系统环境参考
- `03_provision/provision.md` - 可用容器
- `04_data/data_manifest.md` - 数据位置

## 图表生成

Phase 5 必须生成图表。当 `01_plan/plan.md` 的 `Figure Reproduction Inventory`
包含足够信息时，从记录输入或运行输出中创建图表。如果所需数据、代码、环境或权限缺失，
在 `run_results.md` 中将图表生成状态记录为 `blocked`。

绘图实现优先级：

1. 运行作者提供的绘图脚本或 notebook。
2. 包裹产生图表就绪文件的作者分析代码。
3. 从已记录的输出、参数和 source data 编写最小化的 R/Python 绘图代码。
4. 如果以上均不可行，将生成状态记录为 `blocked`；
   不得编造图表数据。

如果 `01_plan/plan.md` 中存在作者提供的绘图代码、notebook 或图表脚本，
agent 必须尝试运行作者代码或记录阻止执行的具体不兼容性之后，才能编写
手写绘图代码。"手写更方便"不是跳过作者代码的有效理由。

## 工作流程
2. 从 `plan.md` 提取步骤、参数和预期输出。
3. 从 `provision.md` 选择已验证的工具/容器；不猜测未部署环境。
4. 从 `data_manifest.md` 读取实际数据路径；不使用未记录数据。
5. 编写 `main.nf` 和必要的阶段配置，将论文指定的实际执行单元封装为 process。
6. 容器网络检查 — 启动测试容器验证 DNS 和外网连通性，对比 Phase 2 记录的
   宿主机网络检测子网冲突；若不通或冲突则在 `run_results.md` 记录并警告用户。
7. 通过 background-task 技能异步运行 `nextflow run main.nf -resume`。
8. 通过 `check_status.sh` 监控任务状态、Nextflow run ID、workdir 和日志；不凭耗时长短猜测状态。
9. 优先运行作者绘图代码；
   只有记录具体失败或不兼容后才编写 fallback 绘图执行单元，并保存脚本、输入表和图像。
10. 写入 `run_results.md`。

## 输出文件

| 文件 | 用途 |
|------|---------|
| `main.nf` | 论文指定执行单元的编排 workflow |
| `nextflow.config` | 可选，仅在需要 Phase 5 覆盖配置时创建；可 include `../02_bootstrap/nextflow.base.config` |
| `run_results.md` | 结果摘要 |
| `results/` | 输出文件 |
| `figures/` | 可选生成图表文件、绘图脚本和图表输入表 |
| `work/` | Nextflow work 目录 |
| `reports/` | Nextflow 报告、timeline、trace 和日志 |

## run_results.md 关键节

```markdown
# Run Results

## Execution Summary
| Item | Value |
|------|-------|
| Status | SUCCESS/FAILED |
| Duration | X hours |

## Pipeline Metrics
| Step | Samples | Avg Time | Status |

## Quality Metrics
| Metric | Value | Expected | Match |

## Figure Generation
| Field | Value |
|-------|-------|
| Generation Status | generated/partial/blocked |
| Figures Directory | figures/ or N/A |
| Plotting Source | author code / author notebook / handwritten fallback / N/A |
| Author Plotting Attempt | command and log path, or N/A |
| Handwritten Fallback Justification | concrete failure/incompatibility, or N/A |

| Figure/Panel | Original Image | Script/Notebook | Input Data | Output Figure | Status | Notes |
|--------------|----------------|-----------------|------------|---------------|--------|-------|

## Issues Encountered
[None / List]

## Nextflow Resume Info
Run ID: xxx
Work directory: work/
Command: nextflow run main.nf -resume ...
Trace/report files: reports/...
```

## 规则

- Phase 5 输出只能依赖 `plan.md`、`provision.md`、`data_manifest.md` 和用户批准的修正。
- 不要把论文分析逻辑无根据地重写为 Nextflow DSL；优先调用论文指定脚本、命令、notebook 或已有 workflow。
- 如果论文已有 Nextflow pipeline，优先复用或包裹它；如果论文使用 Snakemake/R/Python/shell，将其作为具体执行单元编排。
- 记录每个主要 pipeline step 的输入、输出、容器/环境、状态和关键指标。
- 图表生成为必须步骤；必须在 `run_results.md` 写明图表生成状态。
- 如果作者提供了绘图代码、notebook 或 figure script，Phase 5 必须优先运行；
  只有在记录具体失败、依赖缺失、输入缺失、版本不兼容、硬编码路径无法合理修复
  或权限限制后，才允许手写 fallback。
- 手写 fallback 必须只使用 `plan.md`、`data_manifest.md`、Phase 5 输出、
  作者 source data 或用户批准的修正；不得从原文图片描点或手工填造数据。
- `run_results.md` 必须记录每个跳过或失败的作者绘图脚本、尝试命令、日志路径、
  失败原因和 fallback 输入来源。

## 返回

返回 JSON（见 `_base.md` 返回格式）。`payload.steps` 列出所有 pipeline 步骤及执行状态，`payload.figures` 列出图表生成状态。若 pipeline 完全无法运行，`status` 为 `failed`。部分步骤失败但核心结果可用时为 `partial`。

