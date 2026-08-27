---
name: package
description: Phase 7 — 打包复现产物
extends: _base
---
# Phase 7: Package

## 目标
将通过验证的复现产出打包为可交付状态：写 README 和顶层入口脚本，
使他人 clone 后可以理解复现内容并一键运行。复现范围非空时，README
与入口脚本只覆盖范围内目标（见 `01_plan/plan.md` Reproduction Target
表与 `_base.md`「复现范围」），并明示复现范围与 out-of-scope 说明。

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
| `07_package/check.log` | **`bash run.sh check` 的真实执行日志（含退出码 0 记录）——FC-008 证据**；未执行或退出码非 0 时本阶段不得声明 completed |

## 自包含（BL-025，单元 06）

**交付包只要求 Docker**。Java/Nextflow/R/分析环境全部在镜像内：

- 镜像清单从 `03_provision/digests.txt`（`docker images --digests` 输出）读取，
  包内携带 digests.txt 与 Dockerfile（构建配方）
- `run.sh check` **不检查宿主 java/nextflow/R**（它们不再作为前置）；只检查
  docker 可用 + digests.txt 中镜像可 `docker image inspect`；镜像缺失时给出明确
  指令（`bash run.sh provision` 自动按清单 build）
- `run.sh` 的 `run`/`validate` 子命令用 `docker run` 执行分析镜像（挂载 `$ROOT`
  为 work 目录），不在宿主直跑 java/R/nextflow
- 目的：别人拿到包后，在只有 Docker 的环境里 `check` 能过、`provision` 能建环境、
  `run` 能跑——0/6 干净容器失败（缺宿主 java/nextflow/R）由此消除

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
  - `check` — 检查前置条件：docker 可用 + digests.txt 中镜像可 inspect；
    **不检查宿主 java/nextflow/R**（分析环境在镜像内，BL-025 自包含）
  - `provision` — 按 digests.txt 清单检查/构建镜像（缺失时 build 包内 Dockerfile）
  - `all` — 串行运行所有可执行 phase（提示用户确认）
  - `bootstrap`、`data`、`run`、`validate` — 分别运行各 phase（run/validate 用
    `docker run` 分析镜像执行，不依赖宿主 java/R/nextflow）
- 每个 phase 子命令应打印说明（该 phase 做什么、预计耗时）再执行
- Phase 1 不在 run.sh 中重跑；README 指向已有的 plan.md
- Phase 2-6 内部逻辑从各 phase 的产出中读取（如 main.nf、data_manifest.md），
  不做重复实现；run.sh 的角色是入口和引导，不是替代已有产出
- **check 执行后必须保存日志**：`bash run.sh check` 的输出写入
  `07_package/check.log` 并在末尾记录退出码（如 `EXIT=0`）——这是 Package 声明
  completed 的必要证据（FC-008）

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# 分析镜像清单（03_provision/digests.txt，docker images --digests 原始输出）；
# 交付包只要求 Docker——Java/Nextflow/R 全在镜像内（BL-025 自包含）
DIGESTS="$ROOT/03_provision/digests.txt"

first_image() {
    # 从 digests.txt 提取第一个可构建镜像的仓库:tag（简例；按实际清单调整）
    grep -E "^[^ ]+ +[^ ]+ +sha256:" "$DIGESTS" | head -1 | awk '{print $1 ":" $2}' || true
}

check() {
    echo "=== 检查前置条件（只要求 Docker）==="
    command -v docker >/dev/null 2>&1 || { echo "ERROR: docker CLI 缺失（唯一必需宿主依赖）"; exit 1; }
    docker info >/dev/null 2>&1 || { echo "ERROR: docker daemon 不可用"; exit 1; }
    IMAGE="$(first_image)"
    if [ -n "$IMAGE" ] && ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
        echo "WARN: 分析镜像 $IMAGE 不存在 — 运行 'bash run.sh provision' 构建"
        echo "（check 不因镜像缺失而失败；provision 负责构建）"
    fi
    echo "OK: 前置条件满足（仅需 Docker；分析环境在镜像内）"
}

provision() {
    echo "=== Phase 3: Provision（按 digests.txt 清单确保镜像存在）==="
    IMAGE="$(first_image)"
    if [ -n "$IMAGE" ] && docker image inspect "$IMAGE" >/dev/null 2>&1; then
        echo "OK: 镜像 $IMAGE 已存在"
        return 0
    fi
    echo "构建镜像 $IMAGE ..."
    # 用包内 Dockerfile 构建（03_provision/Dockerfile 或 digests.txt 声明的配方）
    docker build -t "${IMAGE%%:*}" "$ROOT/03_provision"
}

all() {
    echo "此操作将运行所有复现阶段。"
    echo "预计时间: [根据 bootstrap 或经验填写]"
    read -p "继续? [y/N] " yn
    case "$yn" in [Yy]*) ;; *) exit 0;; esac
    provision
    data
    run
    validate
}

bootstrap() {
    echo "=== Phase 2: Bootstrap ==="
    echo "（环境在镜像内，宿主无需安装 Java/Nextflow/R）"
}

run() {
    echo "=== Phase 5: Run（docker run 分析镜像）==="
    IMAGE="$(first_image)"
    docker run --rm -v "$ROOT:/work" -w /work "$IMAGE" bash -c "nextflow run 05_run/main.nf -resume -work-dir 05_run/work"
}

validate() {
    echo "=== Phase 6: Validate（docker run 分析镜像）==="
    IMAGE="$(first_image)"
    docker run --rm -v "$ROOT:/work" -w /work "$IMAGE" bash -c "[ -f 05_run/run_results.md ]"
}

"${@:-check}"
```

（模板为示例：docker run 的具体命令从 `05_run/main.nf` 与 `03_provision/provision.md`
的实际执行方式推导；核心纪律是**不在宿主直跑 java/R/nextflow** 且 check 只查 Docker。）

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
3. 如果存在 `06_validate/figure_comparison.md`，摘要关键图级结果
4. 读取 `02_bootstrap/bootstrap.md` 提取系统要求
5. 从各 phase 产出推断目录结构
6. 编写 `README.md`、`run.sh` 和 `.gitignore`（run.sh 按自包含纪律：只依赖 Docker，
   镜像清单取自 `03_provision/digests.txt`）
7. **执行 `bash run.sh check`**，输出保存为 `07_package/check.log` 并在末尾记录
   退出码（`EXIT=0`）；退出码非 0 时排查修复后重跑，不得跳过
8. Git commit

## 规则

- `run.sh` 中的路径全部为相对路径或从 `$ROOT` 推导，禁止硬编码绝对路径
- **自包含纪律（BL-025）**：交付包只要求 Docker；check 不检查宿主 java/nextflow/R；
  分析环境在镜像内（digests.txt 清单 + 包内 Dockerfile）；run/validate 用
  `docker run` 执行
- README 必须包含足够信息让未读论文的人也能理解复现了什么
- README 必须如实反映 Verdict；PARTIAL 时必须在 Verdict 和 Notes 中说明偏差
- 如 Phase 2-5 使用了 `async_submit.sh`，run.sh 应复用同样的 `nextflow -resume` 命令
  （在镜像内执行）
- Phase 7 不重跑任何分析，只做打包和文档；但**必须执行 `run.sh check` 并落
  check.log**（这是打包动作的一部分，不是重跑分析）
- 未执行 check 或退出码非 0 → 不得声明 completed（FC-008）

## 完成
- 输出 `README.md`、`run.sh`、`.gitignore` 在 `repro-data/` 根目录
- **`07_package/check.log` 存在且退出码为 0**（FC-008：无执行证明不得声明 completed）
- 记录 `Phase 7 - COMPLETED: reproduction packaged`

## 返回

返回自然语言简报（见 `_base.md` 返回）：创建了哪些文件、README 一句话概括。

