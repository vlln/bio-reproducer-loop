---
name: bio-reproducer
description: 复现生物信息学论文：7 阶段从论文提取到打包交付
triggers:
  - type: manual
requires:
  environment: pixi.toml
failure_threshold: 3
phases:
  - title: Reader
    detail: 提取论文声明，创建复现计划 plan.md
  - title: Bootstrap
    detail: 检查系统环境：Java、Nextflow、容器运行时
  - title: Provision
    detail: 部署工具容器环境
  - title: Data
    detail: 下载分析所需数据
  - title: Run
    detail: 运行分析流水线
  - title: Validate
    detail: 对比复现结果与论文声称
  - title: Package
    detail: 生成 README 和 run.sh
args:
  - name: paper_path
    description: 论文 PDF 本地路径（与 paper_doi 二选一）
    required: false
  - name: paper_doi
    description: 论文 DOI（与 paper_path 二选一）
    required: false
  - name: output_dir
    description: 复现产物输出目录
    default: repro-data
    required: false
  - name: language
    description: 输出文档语言
    default: zh
    required: false
  - name: confirm_plan
    description: Reader 后人工确认复现计划；无人值守运行（benchmark/沙箱）设为 false
    default: true
    required: false
  - name: consent
    description: 权限模式：ask = 安装/下载大文件前汇总计划并停止等待批准；auto = 无需询问直接执行（沙箱/benchmark 用）
    default: ask
    required: false
---

# bio-reproducer

复现生物信息学论文的完整工作流。从论文 PDF 提取声明，部署分析环境，运行计算，验证结果，打包交付。

## 阶段

1. Reader - 提取论文声明，创建复现计划
2. Bootstrap - 检查系统环境
3. Provision - 部署工具容器环境
4. Data - 下载分析所需数据
5. Run - 运行分析流水线
6. Validate - 对比复现结果与论文声称
7. Package - 生成 README 和 run.sh
