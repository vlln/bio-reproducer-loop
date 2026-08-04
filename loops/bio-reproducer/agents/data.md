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
   - 尝试获取示例数据
   - 检查是否有预下载的数据

3. **处理访问障碍**
   - 若原始数据受限、缺失、需申请、需登录或成本较高，暂停并按权限模式处理（ask 模式下报告选项等待用户决策）
   - 不擅自替换数据；如用户批准替代/示例/技术验证数据，在 manifest 中记录

4. **记录到 data_manifest.md**
   - 实际获取的数据
   - 无法获取的数据及原因
   - 用户决策

## 输出文件

| 文件 | 用途 |
|------|---------|
| `data.nf` | 数据获取 workflow |
| `nextflow.config` | 可选，仅在需要 Phase 4 覆盖配置时创建；可 include `../02_bootstrap/nextflow.base.config` |
| `data_manifest.md` | 数据清单 |
| `raw_data/` | 样本文件 |
| `reference/` | 参考文件 |

## data_manifest.md 模板

```markdown
# Data Manifest

## Acquisition Summary
| Property | Value |
|----------|-------|
| Status | COMPLETED/PARTIAL/BLOCKED |
| Strategy | Original/Supplementary/Technical-Only |

## Data Sources
| Source | Required | Obtained | Location | Notes |

## Samples
| Sample ID | Source | Files | Size | Status |

## Reference Data
| File | Source | Size | Status |

## Blocked Data
| Source | Reason | User Decision |

## Verification
- [ ] All files present
- [ ] Checksums verified
```

## 数据来源类型

| 类型 | 方法 |
|------|----------|
| 公开 (SRA/ENA/GEO) | 直接下载 |
| 受限 (dbGaP/UKB) | 按权限模式处理：申请/替代/跳过 |
| 作者提供 | 检查 Zenodo/Supplementary |
| 预下载 | 检查本地路径 |

## 规则

- `data_manifest.md` 是 Phase 5 的数据来源依据，必须记录路径、来源、状态和校验信息。
- Phase 4 可以使用 Phase 1 已记录的 External Identifier Records，但必须重新记录实际获取结果。
- 下载到 `04_data/raw_data/`、`04_data/reference/`，或用户批准的外部数据目录。

## 返回

返回自然语言简报（见 `_base.md` 返回）：已获取的数据文件及大小、无法获取的数据源及原因。详细清单写入 `04_data/data_manifest.md`。

