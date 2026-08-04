# 0018-provision-image-reuse

## 子任务状态表

| Plan | 状态 | Report |
|------|------|--------|
| [01-plan-provision-image-reuse.md](01-plan-provision-image-reuse.md) | done | [01-report-provision-image-reuse.md](01-report-provision-image-reuse.md) |

## 概述

paper-01 scope 运行暴露 Provision 4h44m 的根因后，将修复落地为**内容无关的
agent prompt 规则**：镜像复用、技能强制使用（biocontainers/quay TRS +
image-mirror-skill/mip）、镜像构建纪律（增量补层 + BuildKit 缓存 + 禁反复
全量重建），并新增 `Image & Reuse Decisions` 行为审计载体与 eval case；
辅以远端环境自洽（装 mip、建 .pixi、清空技能目录）。
