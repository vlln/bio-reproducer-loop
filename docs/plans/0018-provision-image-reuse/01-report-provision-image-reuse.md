---
title: provision 镜像复用与技能纪律执行报告
description: 内容无关 prompt 规则落地、行为审计 eval case、远端环境自洽完成情况
type: report
status: complete
created: 2026-08-04T00:00:00Z
---

# provision 镜像复用与技能纪律执行报告

## 结果

范围完成。`pytest tests/unit` 125 通过（+1 prompt 规则存在性测试）；eval case
`provision-image-reuse` 已登记（真实 LLM 运行待补跑）。

## 规则落地（内容无关，不含任何具体镜像/论文名）

| 规则 | 位置 | 要点 |
|------|------|------|
| 镜像复用 | provision.md「镜像复用」 | 先查 `docker images` 与既往 run 目录；验证内容匹配后直接复用并记录来源；禁止盲目重建 |
| 技能强制使用 | provision.md「技能强制使用」 | 容器查找必须走 biocontainers（TRS API）+ quay（tag 解析）；拉取必须走 image-mirror-skill（mip）；手动 pull 仅限技能全失败并记录原因 |
| 镜像构建纪律 | provision.md「镜像构建纪律」 | 交互容器验证→固化 Dockerfile 一次成型；补包用 docker commit/追加 RUN 增量；全量重建挂 BuildKit 下载缓存且至多一次 |
| 工具与技能纪律（通用） | _base.md「工具与技能纪律」 | 声明技能优先使用；缺工具按技能指引安装，禁止跳过/换替代路径假装等效；本地资源复用优先 |
| 行为审计载体 | provision.md 模板新增 `Image & Reuse Decisions` 节 | 强制记录：本地镜像检查、TRS 查询、镜像源选择、构建方式决策 |

## eval case

- `evals/cases/component/provision-image-reuse/case.yaml`：phase Provision，
  断言 provision.md 含 `image & reuse decisions` 与 `docker images`
- `evals/coverage.yaml` 新增 capability `image_reuse_decision`
- 行为审计式断言：验证"记录决策"，而非自动判定构建次数（构建行为本身难以
  确定性断言，以决策记录作为审计证据）

## 远端环境自洽（BL-007 item 3）

- 装 mip（远端宿主机）
- 建 loop .pixi 环境（pixi install，远端原先无 pixi）
- 清理空技能目录 `~/.loopflow/loops/bio-reproducer/.skills/image-mirror-skill/`

## 遗留

- `provision-image-reuse` eval case 的真实 LLM 运行基线待补跑（1 run）
- 下次 paper-01 类运行验证 Provision 时长压缩效果（预期 4h44m → 30-60min）
