---
name: bootstrap
description: Phase 2 — 系统环境检查和引导
extends: _base
---
# Phase 2: Bootstrap

## 目标
确保运行环境就绪：Java 11+、Nextflow、容器运行时。

## 输入
`01_plan/plan.md` - "System Requirements" 和 "Environment Requirements"

## 工作流程

先完成所有非破坏性检查并记录结果。需要安装、升级、下载大文件、
更改系统配置或使用大量资源时，按权限模式（`{{ consent }}`，见 `_base.md`）
处理；耗时操作通过 `async_submit.sh` 执行。

1. **检查 Java** - 检查是否已安装且版本 ≥11
   - 若缺失或版本不足：按权限模式处理安装

2. **检查 Nextflow** - 检查是否已安装
   - 若缺失：按权限模式处理安装

3. **检查容器运行时** - 按优先级检查可用性：
   - 论文指定 > Singularity/Apptainer > Docker > Conda
   - 若都不可用：按权限模式处理（ask 模式下向用户报告安装偏好选项）

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
  - 基础配置应该避免过度约束，关键选项按权限模式处理
  - 阶段交接以 `bootstrap.md` 为准，不以 config 为准

## 关键原则

- **先检查，后询问** - 不假设环境状态；ask 模式下绝对禁止不经同意的安装（同意通道见 `_base.md` 权限模式）
- **尊重用户选择** - 安装方式按权限模式处理
- **记录实际状态** - 系统已有 vs 本次安装

## 返回

返回自然语言简报（见 `_base.md` 返回）：可用/缺失的运行时组件及建议安装方式。详细状态写入 `02_bootstrap/bootstrap.md`。