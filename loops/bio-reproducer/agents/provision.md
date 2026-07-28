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
用 Nextflow 并行部署所有工具环境。

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

## Verification
- [x] All containers pulled
- [x] Test execution passed
```

## 注意事项
- 失败时检查：容器仓库访问、磁盘空间、网络代理

## 返回

返回自然语言简报（见 `_base.md` 返回）：已部署的工具及版本、部署失败的工具及原因。详细清单写入 `03_provision/provision.md`。

