---
title: provision 镜像复用与技能纪律
description: paper-01 scope 运行暴露的 Provision 效率问题：镜像复用、强制技能使用、Dockerfile 构建纪律的行为规则化 + 行为审计 eval case
type: plan
status: done
created: 2026-08-04T00:00:00Z
---

# provision 镜像复用与技能纪律

## 背景

paper-01 scope 运行（0016/0017 遗留观察）暴露 Provision 4h44m 的根因：
agent 无视本地已有镜像从零重建、有 biocontainers/quay/image-mirror 技能不用、
Dockerfile 反复全量重建导致 2GB 层重复下载、mip 缺失。经确认，修复以
**内容无关的 agent prompt 规则**为主（不写死具体镜像/论文），辅以远端环境
自洽与行为审计 eval。

## 范围

1. provision.md 新增三条内容无关规则：
   - 镜像复用（先查本地已有镜像，验证命中即用）
   - 技能强制使用（容器查找走 biocontainers/quay TRS API、拉取走
     image-mirror-skill/mip，手动 pull 仅限技能全失败并记录原因）
   - 镜像构建纪律（交互验证→固化、docker commit 增量、BuildKit 缓存、
     全量重建至多一次）
2. provision.md 模板新增 `Image & Reuse Decisions` 节（行为审计载体）
3. _base.md 新增「工具与技能纪律」通用规则（技能优先、缺工具按指引安装、
   本地资源复用优先）
4. 新增 eval case `provision-image-reuse`（断言 provision.md 含镜像决策节）
   + coverage capability + 确定性 prompt 规则存在性测试
5. 远端环境自洽：装 mip、建 loop .pixi 环境、清理空技能目录

## 验证

- `pytest tests/unit` 全绿（125）
- 远端：`mip version` 可用、loop .pixi 环境建成、空技能目录清除

## 关联

- BL-009（provision 镜像复用与技能纪律）
- 0016/0017 的 paper-01 scope 运行观察
