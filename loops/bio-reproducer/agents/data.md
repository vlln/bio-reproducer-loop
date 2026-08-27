---
name: data
description: Phase 4 — 数据获取
extends: _base
skills:
- zenodo
---
# Phase 4: Data

## 目标
获取分析所需数据。复现范围非空时只获取范围内目标（见 `01_plan/plan.md` Reproduction Target 表与 `_base.md`「复现范围」）所需数据；范围外数据源记录但标记 `out-of-scope`，不下载。

## 输入
- `01_plan/plan.md` - Data Requirements 和 External Identifier Records
- `02_bootstrap/bootstrap.md` - 系统环境参考
- `03_provision/provision.md` - 已部署工具和容器

## 工作流程

1. **分析数据来源**
   - 识别 plan.md 中的数据来源和已解析外部标识符记录
   - 评估可获取性（公开/需申请/受限）

2. **尝试获取**
   - 尝试下载公开数据；大文件下载必须通过 `async_submit.sh`
   - 下载统一使用 `curl -C -`（断点续传；实测 NCBI 支持 Range/HTTP 206）。
     **不要安装或调用 wget/aria2c**——运行时镜像内不存在，回退路径会静默失效
   - 尝试获取示例数据
   - 检查是否有预下载的数据

3. **处理访问障碍**
   - 若原始数据受限、缺失、需申请、需登录或成本较高，暂停并按权限模式处理（ask 模式下报告选项等待用户决策）
   - 不擅自替换数据；如用户批准替代/示例/技术验证数据，在 manifest 中记录
   - **即使某数据源整体无法获取，也必须为该源落下一份获取日志**（请求了什么 URL、返回了什么），
     禁止只写一句"不可获取"——没有尝试日志的阻塞在证据面上等同"未尝试"

4. **记录标准格式证据（每资源）**
   - 每个数据资源一份获取日志：`04_data/<source>_<id>.log`，保存 curl/wget 的**原始输出**
     （含进度、HTTP 响应、错误行、`Download complete`）
   - 每个已下载数据文件跑 `sha256sum`，全部输出汇总到 `04_data/sha256sums.txt`（任何人可重算）
   - 从上述文件渲染 `data_manifest.md` 散文摘要；散文不得包含日志/校验文件中不存在的状态结论

## 输出文件

| 文件 | 用途 |
|------|---------|
| `data.nf` | 数据获取 workflow |
| `nextflow.config` | 可选，仅在需要 Phase 4 覆盖配置时创建；可 include `../02_bootstrap/nextflow.base.config` |
| `data_manifest.md` | 数据清单（散文摘要，从日志/校验文件渲染） |
| `<source>_<id>.log` | **每资源一份获取日志**（原始输出；阻塞时也必须有） |
| `sha256sums.txt` | 全部已下载文件的 sha256 校验和输出 |
| `raw_data/` | 样本文件 |
| `reference/` | 参考文件 |

## 状态词表（终态类别，依证据判定）

每个数据资源在 manifest 中必须标注以下状态之一，**不得使用含糊词**（如"不可获取""需要更好网络"）：

| 状态 | 含义 | 判定依据（终态信号，非尝试次数） |
|------|------|------|
| `completed` | 已获取 | 获取日志含 `Download complete` 且文件存在（`ls -l` 输出/校验文件） |
| `partial` | 部分获取 | 部分文件完成、其余未完成 |
| `unavailable` | 外部不可得 | HTTP 404/403/451、注册墙、DUA 等访问墙信号 |
| `not_attempted` | 未完成获取 | 传输层失败（`curl: (35)` 连接重置、`curl: (56)` SSL、超时）、回退工具缺失（`command not found`） |

要点：
- 传输层失败 ≠ 外部不可得：前者可能重试/续传成功，后者是访问墙。**按终态信号区分，不按尝试次数**
- 中途传输失败但最终 `Download complete` → 记 `completed`（续传已克服）
- 无任何日志的资源 → 记 `not_attempted`（无证据），不得标 `unavailable`

## data_manifest.md 模板

```markdown
# Data Manifest

## Acquisition Summary
| Property | Value |
|----------|-------|
| Status | COMPLETED/PARTIAL/BLOCKED |
| Strategy | Original/Supplementary/Technical-Only |

## Data Sources
| Source | Required | Obtained | Location | Status | Log | Notes |
|--------|----------|----------|----------|--------|-----|-------|

## Samples
| Sample ID | Source | Files | Size | Status |

## Reference Data
| File | Source | Size | Status |

## Blocked Data
| Source | Reason | User Decision | Attempt Log |
|--------|--------|---------------|-------------|

## Verification
- [ ] sha256sums.txt 已生成且可被 `sha256sum -c` 解析
- [ ] 每个数据源都有获取日志（含阻塞源）
```

## 数据来源类型

| 类型 | 方法 |
|------|----------|
| 公开 (SRA/ENA/GEO) | 直接下载 |
| 受限 (dbGaP/UKB) | 按权限模式处理：申请/替代/跳过 |
| 作者提供 | 检查 Zenodo/Supplementary |
| 预下载 | 检查本地路径 |

## 规则

- 标准格式证据（获取日志 + `sha256sums.txt`）是 Phase 5 与外部评估者的数据来源依据；
  `data_manifest.md` 是从它们渲染的散文摘要，**不得包含证据中不存在的状态结论**。
- Phase 4 可以使用 Phase 1 已记录的 External Identifier Records，但必须重新记录实际获取结果。
- 下载到 `04_data/raw_data/`、`04_data/reference/`，或用户批准的外部数据目录。
- 下载只用 `curl -C -`（续传）；不安装 wget/aria2c。
- 阻塞也必须落尝试日志：请求了什么 URL、返回了什么；无日志的阻塞记 `not_attempted`。

## 返回

返回自然语言简报（见 `_base.md` 返回）：已获取的数据文件及大小（附 sha256sums.txt 路径）、
未获取数据源的终态类别（`unavailable`/`not_attempted`）及对应日志文件名。
详细清单写入 `04_data/data_manifest.md`。

