---
name: bootstrap
description: Phase 2 — 系统环境检查和引导
extends: _base
output:
  type: object
  properties:
    payload:
      type: object
      properties:
        available:
          type: array
          description: Available runtime components
          items:
            type: object
            properties:
              component: {type: string}
              version: {type: string}
              provider: {type: string}
        missing_runtime:
          type: array
          description: Missing runtime components
          items:
            type: object
            properties:
              component: {type: string}
              required_by: {type: string}
              install_option: {type: string}
      required: [available]
---
# Phase 2: Bootstrap

## 目标
确保运行环境就绪：Java 11+、Nextflow、容器运行时。

## 输入
`01_plan/plan.md` - "System Requirements" 和 "Environment Requirements"

## 工作流程

先完成所有非破坏性检查并记录结果。需要安装、升级、下载大文件、
更改系统配置或使用大量资源时，先汇总计划并取得用户同意；耗时操作
通过 `async_submit.sh` 执行。

1. **检查 Java** - 检查是否已安装且版本 ≥11
   - 若缺失或版本不足：询问用户是否安装

2. **检查 Nextflow** - 检查是否已安装
   - 若缺失：询问用户是否安装

3. **检查容器运行时** - 按优先级检查可用性：
   - 论文指定 > Singularity/Apptainer > Docker > Conda
   - 若都不可用：询问用户安装偏好

4. **检查资源** - 磁盘（包括各个分区）/内存/CPU/GPU（如果需要）
   - 对比 plan.md 要求，不足时警告用户

5. **记录宿主机网络** - 记录宿主机网络拓扑，供后续阶段检测容器
   网络冲突：
   - 网络接口及子网、路由表、DNS 配置
   - 代理环境变量（`HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY`）
   - 仅如实记录，不做容器内测试（此时尚无容器环境）

6. **测试** - 验证安装：
   - `nextflow run hello`
   - 容器测试运行

## 输出

- `02_bootstrap/bootstrap.md` - 环境状态报告（含宿主机网络记录）
- `02_bootstrap/nextflow.base.config` - 可选基础运行配置
  - 只有后续 Nextflow 阶段需要固定 executor、容器 runtime、profile 或资源默认值时才生成
  - 基础配置应该避免过度约束，而且应该对关键选项询问用户
  - 阶段交接以 `bootstrap.md` 为准，不以 config 为准

## 关键原则

- **先检查，后询问** - 不假设环境状态，绝对禁止不经同意的安装
- **尊重用户选择** - 安装方式询问用户
- **记录实际状态** - 系统已有 vs 本次安装

## 返回

返回 JSON（见 `_base.md` 返回格式）。`payload.available` 列出所有可用的运行时组件，`payload.missing_runtime` 列出缺失的组件及建议安装方式。若关键运行时（Java/Nextflow/容器引擎）全部缺失，`status` 应为 `blocked`。部分缺失为 `partial`。