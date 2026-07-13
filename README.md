# bio-reproducer

复现生物信息学论文的 7 阶段 workflow loop。

## 前置依赖

- [pixi](https://pixi.sh) — 环境和依赖管理
- [loopflow](https://github.com/vlln/loopflow) — workflow 运行时

## 快速开始

```bash
# 1. 安装 pixi（如未安装）
curl -fsSL https://pixi.sh/install.sh | sh

# 2. 安装 loopflow（如未安装）
pip install loopflow

# 3. Clone 并进入项目
git clone git@github.com:vlln/bio-reproducer-loop.git
cd bio-reproducer-loop/loops/bio-reproducer

# 4. 安装工具链和 skills
pixi run install-skit      # skit — skill 包管理器
pixi run install-mip        # mip — 镜像管理工具
pixi run install-skills     # 所有 skill 依赖（paperutils、mineru-api 等）

# 5. 验证环境
pixi run check-env

# 6. 运行复现
cd ../..  # 回到项目根目录
loopflow run loops/bio-reproducer \
  --paper_path /path/to/paper.pdf \
  --language zh
```

也可以指定 DOI 而非本地 PDF：

```bash
loopflow run loops/bio-reproducer \
  --paper_doi 10.1101/2025.01.01.123456 \
  --language zh
```

## 阶段

| Phase | 名称 | 描述 |
|-------|------|------|
| 1 | Reader | 提取论文声明，创建复现计划 |
| 2 | Bootstrap | 检查系统环境 |
| 3 | Provision | 部署工具容器 |
| 4 | Data | 下载分析数据 |
| 5 | Run | 运行分析流水线 |
| 6 | Validate | 验证复现结果 |
| 7 | Package | 打包复现产物 |

## 结构

```
loops/bio-reproducer/
├── workflow.py      # 阶段编排和 phase gating
├── pixi.toml        # 环境和 skill 依赖
├── pixi.lock        # 锁定依赖版本
└── agents/          # 各阶段 agent 定义
    ├── _base.md     # 公共约定和输出 schema
    ├── reader.md
    ├── bootstrap.md
    ├── provision.md
    ├── data.md
    ├── run.md
    ├── validate.md
    └── package.md
```