---
name: provision
description: Phase 3 — 工具容器环境部署
extends: _base
skills:
- biocontainers
- quay
- image-mirror-skill
---
# Phase 3: Provision

## 目标
用 Nextflow 并行部署所有工具环境。复现范围非空时只部署范围内目标（见 `01_plan/plan.md` Reproduction Target 表与 `_base.md`「复现范围」）所需工具；仅服务于范围外目标的工具记录但标记 `out-of-scope`，不拉取/不构建。

## 输入
- `01_plan/plan.md` - Environment Requirements
- `02_bootstrap/bootstrap.md` - 系统环境参考
- `02_bootstrap/nextflow.base.config` - 可选，仅作为 Nextflow 运行配置

## 工作流程

**重要**：
- 禁止随意猜测镜像/环境版本，必须确认目标环境存在或可构建。
  - 如果无法找到完全对应的版本，则向上使用最近的版本
- 开始拉取/构建/安装前按权限模式（`{{ consent }}`，见 `_base.md`）处理；耗时操作通过 background-task 技能异步执行。

1. 根据 Environment Requirements 检查
  - 如果不存在，则考虑下载：优先使用单体工具，而非工具集中的工具（除非论文指定了使用某工具集）
  - 如果缺失工具，则考虑优先使用论文提供的环境（镜像），如果没有则搜索镜像。如果没有镜像则搜索 bioconda，如果也没有则考虑源码安装/编译。
  - 注意！安装工具前应该尝试检查是否冲突。如果安装遇到冲突问题则应该修复后继续尝试
2. 编写 `provision.nf` 和必要的阶段配置
3. 按权限模式处理部署批准（ask 模式下汇总部署计划并停止报告）
4. 拉取/构建容器
5. 验证每个工具可用

### 镜像复用（先查本地，命中即用）

- 任何构建开始前，先检查本地已有容器镜像（`docker images`）与既往运行目录中遗留的环境。
- 若存在可能满足本论文需求的镜像：先验证内容与任务匹配（关键工具是否齐全、能否运行），验证通过直接复用并在 provision.md 记录来源与验证结果；验证不通过才允许从头构建。
- 禁止无视本地已有资产、仅凭"论文要求 X 就去找 X"而盲目重建。

### 技能强制使用（容器查找与拉取必须走技能）

- 查找预构建容器：必须用 **biocontainers** 技能（GA4GH TRS API）与 **quay** 技能（tag 解析），优先官方维护的 Bioconductor 容器；禁止手工在 registry 网页/命令里猜 tag。
- 镜像拉取与加速：必须用 **image-mirror-skill**（mip CLI）探测与选择可用镜像源；mip 缺失时按该技能指引先安装。
- 仅在技能路径全部失败后，才允许手动 `docker pull` 并必须记录原因（哪些源、为何失败）。

### 镜像构建纪律（交互验证 → 固化，禁反复全量重建）

- 构建前先 `docker run` 交互容器验证包集与镜像源可用性，确认无误后把已验证命令固化成 Dockerfile，一次成型。
- 需要补包/修包时用 `docker commit` 或追加 RUN 行增量补层；不得重写已存在的 RUN 行（重写会使该层及后续层缓存全部失效）。
- 必须全量重建时，为下载/安装挂 BuildKit 缓存（如 `RUN --mount=type=cache,target=/root/.cache/R ...`），避免重复下载已获取的包。
- 同一镜像的全量重建至多一次，且必须建立在前一次失败根因已定位的基础上；禁止"换一个源就重试一次全量构建"的循环。

## 输出文件

| 文件 | 用途 |
|------|---------|
| `provision.nf` | 拉取/构建环境的 workflow |
| `nextflow.config` | 可选，仅在需要 Phase 3 覆盖配置时创建；可 include `../02_bootstrap/nextflow.base.config` |
| `provision.md` | 部署报告 |

## provision.md 模板

```markdown
# Provision Report

## Environment
| Property | Value |
|----------|-------|
| Container Engine | Docker/Singularity |

## Tools Provisioned
| Tool | Version | Image | Status |

## Image & Reuse Decisions
| 决策项 | 结论 | 依据 |
|--------|------|------|
| 本地已有镜像检查 | 复用/未命中 | docker images 结果与验证命令 |
| 预构建容器查找 | TRS/镜像名 | biocontainers/quay 查询结果 |
| 镜像源选择 | 源与速度 | mip/image-mirror 探测结果 |
| 构建方式 | 复用/增量/全量 | 决策理由（含失败根因，如有） |

## Verification
- [x] All containers pulled
- [x] Test execution passed
```

## 注意事项
- 失败时检查：容器仓库访问、磁盘空间、网络代理

## 返回

返回自然语言简报（见 `_base.md` 返回）：已部署的工具及版本、部署失败的工具及原因。详细清单写入 `03_provision/provision.md`。

