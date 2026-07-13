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
  required:
  - language
  - output_dir
output:
  type: object
  properties:
    status:
      type: string
      enum: [completed, partial, blocked, failed]
      description: Phase completion status
    summary:
      type: string
      description: One-line summary for workflow log
    missing:
      type: array
      description: What downstream phases need to know is missing
      items:
        type: object
        properties:
          item:
            type: string
            description: What is missing
          reason:
            type: string
            description: Why it is missing
          action:
            type: string
            enum: [ask_user, block, retry, skip]
            description: Recommended action for the workflow
    decisions:
      type: array
      description: Decisions made by this phase that need user awareness
      items:
        type: object
        properties:
          decision:
            type: string
          reason:
            type: string
    payload:
      type: object
      description: Phase-specific output data
  required:
  - status
  - summary
---
## 工作约定

### 文件与状态
- 产出目录: {{ output_dir }}。所有复现产物、中间文件和日志必须在此目录下。
- 前置阶段的文件已存在，直接读取。阶段之间通过显式报告和清单交接，不依赖聊天记忆。
- 写入阶段输出前检查是否已存在，避免重复工作。
- 所有阶段产物、中间文件和日志存放在该阶段自身的输出目录中（如 `03_provision/`）。
- 在 {{ output_dir }} 内提交有意义的 Git 变更；不得提交该目录外的文件。

### 异步任务
- 耗时命令（安装、下载、容器拉取/构建、Nextflow 运行）通过 background-task 技能异步执行，不要同步等待。
- 使用 `async_submit.sh` 提交任务，`check_status.sh` 检查状态。
- 异步任务名称使用 `{phase}_{action}_{instance}` 格式，如 `p4_data_fetch_batch1`。
- 判定长时间任务失败前，检查其任务状态、进程状态和日志。
- 同步命令仅用于状态读取、脚本生成、配置编辑和简短检查。

### 代码规范
- 脚本和代码不得使用硬编码或绝对路径，所有路径从 {{ output_dir }} 推导。
- Nextflow 运行使用 `nextflow ... -resume`。

### 产出语言
- 产出语言：{{ language }}。所有标题、章节名、描述文字和表格内容必须使用 {{ language }} 编写。
- 不受语言配置影响：代码块、命令、文件路径、URL、状态值、模板字段名、日志条目格式。
- 脚本文件（如 `run.sh`）中的注释和 echo 输出应跟随产出语言。

### 返回格式

任务完成后，你必须返回一个 JSON 对象，不得包含其他内容。字段含义：

- `status` — 阶段完成状态：
  - `completed`：全部目标完成，下游可正常运行
  - `partial`：部分目标完成，下游需降级处理（在 `missing` 中列出缺失项）
  - `blocked`：关键目标无法完成，下游不应继续
  - `failed`：阶段执行失败，需要重试或人工介入
- `summary` — 一句话摘要，用于 workflow 日志
- `missing` — 缺失项列表。每项包含 `item`（缺失什么）、`reason`（为什么）、`action`（建议动作：`ask_user`/`block`/`retry`/`skip`）
- `decisions` — 本阶段做出的重要决策，供用户审查
- `payload` — 阶段特定的结构化输出数据，供下游阶段读取

**重要**：只返回 JSON，不要包裹在 markdown 代码块中。

### 辅助工具
- **background-task** — 异步任务提交与状态管理（`async_submit.sh` / `check_status.sh`）
- `paperutils get` / `paperutils explain` — 解析论文标识符（仅对论文中已出现的标识符使用）