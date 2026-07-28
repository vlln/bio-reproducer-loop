---
name: _base
description: 公共工作约定（抽象 agent，不直接调用）
skills:
- background-task
input:
  type: object
  properties:
    language:
      type: string
    output_dir:
      type: string
    consent:
      type: string
      description: 权限模式：ask 或 auto
  required:
  - language
  - output_dir
---
## 工作约定

### 文件与状态
- 产出目录: {{ output_dir }}。所有复现产物、中间文件和日志必须在此目录下。
- 前置阶段的文件已存在，直接读取。阶段之间通过显式报告和清单交接，不依赖聊天记忆。
- 写入阶段输出前检查是否已存在，避免重复工作。
- 所有阶段产物、中间文件和日志存放在该阶段自身的输出目录中（如 `03_provision/`）。
- 在 {{ output_dir }} 内提交有意义的 Git 变更；不得提交该目录外的文件。

### 权限模式
- 当前权限模式：`{{ consent }}`。
- `auto`：安装软件、拉取/构建容器、下载数据等操作无需逐条询问，按计划直接执行。
- `ask`：需要安装软件、修改系统配置或下载大文件前，汇总完整计划（做什么、多大、影响什么）并停止，用自然语言报告计划和风险，等待用户批准。不得假装已询问或擅自执行。

### 异步任务
- 耗时命令（安装、下载、容器拉取/构建、Nextflow 运行）通过 background-task 技能异步执行，不要同步等待。
- 使用 `async_submit.sh` 提交任务，`check_status.sh` 检查状态。
- 异步任务名称使用 `{phase}_{action}_{instance}` 格式，如 `p4_data_fetch_batch1`。
- 判定长时间任务失败前，检查其任务状态、进程状态和日志。
- 同步命令仅用于状态读取、脚本生成、配置编辑和简短检查。

### 代码规范
- 脚本和代码不得使用硬编码或绝对路径，所有路径从 {{ output_dir }} 推导。
- Nextflow 运行使用 `nextflow ... -resume`。
- **禁止修改或重新实现论文工具代码**。如果工具或依赖无法按原样使用（版本不兼容、依赖缺失、源码不可获取），标记为 `blocked` 并报告原因，不要尝试迁移、重写或替代实现。

### 产出语言
- 产出语言：{{ language }}。所有标题、章节名、描述文字和表格内容必须使用 {{ language }} 编写。
- 不受语言配置影响：代码块、命令、文件路径、URL、状态值、模板字段名、日志条目格式。
- 脚本文件（如 `run.sh`）中的注释和 echo 输出应跟随产出语言。

### 返回

完成后用自然语言简要汇报：完成了什么、关键产出文件路径、需要用户知道的缺失或风险。引擎会另行要求 `__goal` 完成标记，除此之外不要返回结构化业务数据——workflow 不解析返回文本，详细结果一律写入阶段产出文件。

例外：如果本阶段 frontmatter 定义了 output schema（如 Phase 6 的 `payload.verdict`），schema 中的字段是被程序消费的，返回的 JSON 必须包含它们。

### 辅助工具
- **background-task** — 异步任务提交与状态管理（`async_submit.sh` / `check_status.sh`）
- `paperutils get` / `paperutils explain` — 解析论文标识符（仅对论文中已出现的标识符使用）