# bio-reproducer

复现生物信息学论文的 7 阶段 workflow loop。

## 前置依赖

- [pixi](https://pixi.sh) — 环境和依赖管理
- [loop](https://github.com/vlln/loopflow) — workflow 运行时

## 快速开始

```bash
# 1. 安装 pixi 和 loop（如未安装）
curl -fsSL https://pixi.sh/install.sh | sh
pip install git+https://github.com/vlln/loopflow.git

# 2. 安装 loop 到 ~/.loopflow/loops/
git clone git@github.com:vlln/bio-reproducer-loop.git
mkdir -p ~/.loopflow/loops
cp -r bio-reproducer-loop/loops/bio-reproducer ~/.loopflow/loops/bio-reproducer

# 3. 安装工具链和 skills
#    pixi run 会自动创建 conda 环境并安装 openjdk、nextflow、python
cd ~/.loopflow/loops/bio-reproducer
pixi run install-skit      # 安装 skit 到 .local/bin
pixi run install-mip        # 安装 mip 到 .local/bin
pixi run install-skills     # 安装 skill 依赖到 .skills/

# 4. 切换到工作目录，激活环境
cd ~/my-paper-project       # 你的论文复现工作目录
pixi shell -m ~/.loopflow/loops/bio-reproducer
# ↓ 以下命令在 pixi shell 内执行

# 5. 验证环境
pixi run check-env          # 确认 Java、Nextflow、mip、paperutils 可用

# 6. 运行复现
loop run bio-reproducer \
  --args '{"paper_path": "paper.pdf", "language": "zh"}'
```

也可以指定 DOI 而非本地 PDF：

```bash
# 在 pixi shell 内
loop run bio-reproducer \
  --args '{"paper_doi": "10.1101/2025.01.01.123456", "language": "zh"}'
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