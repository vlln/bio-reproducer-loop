---
name: package
description: Phase 7 — 打包复现产物
extends: _base
output:
  type: object
  properties:
    payload:
      type: object
      properties:
        files_written:
          type: array
          description: Output files created
          items: {type: string}
        readme_summary:
          type: string
          description: One-line summary of the README
      required: [files_written]
---
# Phase 7: Package

## 目标
将通过验证的复现产出打包为可交付状态：写 README 和顶层入口脚本，
使他人 clone 后可以理解复现内容并一键运行。

## 前置条件
- `06_validate/report.md` 存在且 Verdict 为 REPRODUCED 或 PARTIAL
- FAILED 或 BLOCKED 状态不执行本阶段

## 输入
- `01_plan/plan.md` — 论文信息和复现目标
- `06_validate/report.md` — 验证结论和评分
- `06_validate/figure_comparison.md` — 图表生成/验证报告（如存在）
- 所有 phase 的输出目录和文件

## 输出

| 文件 | 用途 |
|------|---------|
| `README.md` | 项目总览、快速开始、目录结构 |
| `run.sh` | 顶层入口脚本，检查环境并引导执行 |
| `.gitignore` | 忽略日志、Nextflow work 目录等临时文件 |

### README.md 必须包含

```markdown
# [Paper Title]

**DOI**: [doi]
**Reproduction Status**: REPRODUCED / PARTIAL (Score: XX/100)
**Date**: YYYY-MM-DD

## Paper Summary

[2-3 句话，来自 plan.md 的 Paper Understanding]

## Reproduction Verdict

[来自 report.md 的验证摘要，包含关键分数和显著偏差]

## Figure Reproduction

[摘要图表生成和验证结果。如果图表已生成，摘要生成图表目录和 figure_comparison.md 结果。]

## System Requirements

- OS: [来自 bootstrap.md]
- 容器运行时: [Docker / Singularity / Apptainer]
- Nextflow: [版本]
- 其他: [磁盘空间、内存、网络]

## Quick Start

```bash
# 1. Clone 并进入目录
git clone <repo> && cd repro-data

# 2. 检查前置条件
bash run.sh check

# 3. 运行复现（所有阶段）
bash run.sh all

# 或逐步运行：
bash run.sh bootstrap   # Phase 2: 安装系统依赖
bash run.sh provision   # Phase 3: 拉取/构建容器
bash run.sh data        # Phase 4: 下载数据
bash run.sh run         # Phase 5: 运行分析
bash run.sh validate    # Phase 6: 验证结果
```

## Directory Structure

```
repro-data/
├── README.md
├── run.sh
├── .gitignore
├── 01_plan/plan.md
├── 01_plan/paper_markdown/
├── 02_bootstrap/bootstrap.md
├── 03_provision/provision.md
├── 04_data/data_manifest.md
├── 05_run/main.nf
├── 05_run/run_results.md
├── 05_run/results/
├── 05_run/figures/
├── 06_validate/report.md
├── 06_validate/figure_comparison.md
└── execution_log.md
```

## Notes

[已知问题、数据访问要求、预计运行时间，新用户需要了解的任何内容。]
```

### run.sh 要求

- 纯 bash，不依赖 Python 或其他解释器
- 所有路径相对于 `repro-data/` 根目录
- 不接受硬编码路径；通过脚本所在目录推断 `repro-data/` 根
- 提供以下子命令：
  - `check` — 检查系统前置条件（nextflow、docker/singularity、磁盘空间等）
  - `all` — 串行运行所有可执行 phase（提示用户确认）
  - `bootstrap`、`provision`、`data`、`run`、`validate` — 分别运行各 phase
- 每个 phase 子命令应打印说明（该 phase 做什么、预计耗时）再执行
- Phase 1 不在 run.sh 中重跑；README 指向已有的 plan.md
- Phase 2-6 内部逻辑从各 phase 的产出中读取（如 main.nf、data_manifest.md），
  不做重复实现；run.sh 的角色是入口和引导，不是替代已有产出

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

check() {
    echo "=== 检查前置条件 ==="
    command -v nextflow >/dev/null 2>&1 || { echo "ERROR: nextflow not found"; exit 1; }
    command -v docker >/dev/null 2>&1 || command -v singularity >/dev/null 2>&1 || \
        { echo "ERROR: docker or singularity required"; exit 1; }
    echo "OK: 前置条件满足"
}

all() {
    echo "此操作将运行所有复现阶段。"
    echo "预计时间: [根据 bootstrap 或经验填写]"
    read -p "继续? [y/N] " yn
    case "$yn" in [Yy]*) ;; *) exit 0;; esac
    bootstrap
    provision
    data
    run
    validate
}

bootstrap() {
    echo "=== Phase 2: Bootstrap ==="
    echo "安装系统依赖..."
    # 从 02_bootstrap/bootstrap.md 读取并执行
}

# ... provision, data, run, validate 桩代码 ...

"${@:-check}"
```

### .gitignore 必须包含

至少忽略以下临时文件和目录：

```gitignore
# 任务执行日志
*.log
.task_status/

# Nextflow work 目录（大型中间文件）
work/
.nextflow/
.nextflow.log*

# 容器 / Singularity 镜像
*.sif
*.img

# 编辑器 / OS 产物
*~
.DS_Store
```

如有 phase 特定的临时产出也应一并忽略。

## 工作流程

1. 读取 `01_plan/plan.md` 的标题、DOI、Paper Understanding
2. 读取 `06_validate/report.md` 的 Verdict、Score、Deviations
4. 如果存在 `06_validate/figure_comparison.md`，摘要关键图级结果
5. 读取 `02_bootstrap/bootstrap.md` 提取系统要求
6. 从各 phase 产出推断目录结构
7. 编写 `README.md`、`run.sh` 和 `.gitignore`
8. Git commit

## 规则

- `run.sh` 中的路径全部为相对路径或从 `$ROOT` 推导，禁止硬编码绝对路径
- README 必须包含足够信息让未读论文的人也能理解复现了什么
- README 必须如实反映 Verdict；PARTIAL 时必须在 Verdict 和 Notes 中说明偏差
- 如 Phase 2-5 使用了 `async_submit.sh`，run.sh 应复用同样的 `nextflow -resume` 命令
- Phase 7 不重跑任何分析，只做打包和文档

## 完成
- 输出 `README.md`、`run.sh` 和 `.gitignore` 在 `repro-data/` 根目录
- 记录 `Phase 7 - COMPLETED: reproduction packaged`

## 返回

返回 JSON（见 `_base.md` 返回格式）。`payload.files_written` 列出所有创建的文件。

