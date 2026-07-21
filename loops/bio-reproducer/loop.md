---
name: bio-reproducer
description: 复现生物信息学论文：7 阶段从论文提取到打包交付
triggers:
  - type: manual
---

# bio-reproducer

复现生物信息学论文的完整工作流。从论文 PDF 提取声明，部署分析环境，运行计算，验证结果，打包交付。

## 阶段

1. Reader — 提取论文声明，创建复现计划
2. Bootstrap — 检查系统环境
3. Provision — 部署工具容器环境
4. Data — 下载分析所需数据
5. Run — 运行分析流水线
6. Validate — 对比复现结果与论文声称
7. Package — 生成 README 和 run.sh
