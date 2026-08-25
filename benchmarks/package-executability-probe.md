# 复现包可执行性实测（Package Executability Probe）

**日期**：2026-08-26
**远端**：`gs@172.16.209.237`，归档根目录 `/storeData/gs/claroai-calibration/runs/`
**范围**：`bench-2NN`（35 个，`*-legacy-*` 目录全部忽略）
**性质**：只读探测。归档目录以 `:ro` 挂载，未做任何写入、未 `git add/commit`。

---

## 1. 方法说明

### 镜像
`ubuntu:22.04`（远端 `docker images` 中已存在，image id `b8e6b596a324`，78.1MB）。
这是一个**干净的通用基础镜像**：没有 java、没有 nextflow、没有 R、没有 docker CLI、没有 python 科学栈。
选它的目的正是模拟"别人拿到这个包"的真实起点——交付包声称"一键重跑"，那么它至少应该
在 check 阶段清楚地告诉接收者缺什么，而不是隐式假设宿主已经装好一整套工具链。

### 挂载与执行方式
每个 run 一次性容器，命令模板：

```bash
docker run --rm -v /storeData/gs/claroai-calibration/runs/<entry>/repro-data:/src:ro \
  ubuntu:22.04 bash -c 'cp -r /src /work && cd /work && timeout 300 bash run.sh check; echo "EXIT=$?"'
```

- `:ro` 保证归档目录在容器内**物理不可写**；
- 再 `cp -r /src /work`，脚本在容器可写副本里执行，`ROOT="$(cd "$(dirname "$0")" && pwd)"` 解析为 `/work`，
  因此即使脚本试图写产物，也只会写进容器 overlay，容器 `--rm` 后消失；
- `timeout 300` 防止 `read -rp` 之类交互提示或网络请求把探测卡死；
- `--rm` 保证不留容器残骸。

**执行后校验**：`find <6 个 repro-data> -newermt "-2 hours"` 返回**空**，确认 6 个归档目录内
没有任何文件被新建或修改。

### 为什么只跑 `check`
`run.sh` 的 `all` / `data` / `run` / `provision` 分支会下载数据（PMC 补充材料、hg38 参考基因组、
训练数据包）、`docker build` 构建数 GB 的分析镜像、跑 Nextflow 全流程。这些既有网络副作用、
又有数小时级耗时，属于明确禁止范围。`check` 按设计是**纯只读的前置条件探测**。

### 预检（步骤 3）
6 个候选的 `check()` 函数体在执行前逐个通读，确认其中只有：
`command -v <tool>`、`<tool> --version`、`[ -f ... ]` / `[ -d ... ]` 存在性判断、
`df -k`/`free -g` 容量查询、`docker image inspect` / `docker info`（只读查询）、`echo`。
**没有任何 `curl`/`wget`/`nextflow run`/`docker build`/重定向写文件的动作。**
因此 6 个候选全部通过预检，**无一需要因"check 分支实际会下载或改文件"而被跳过替换**。

---

## 2. 样本选取

统计：35 个非 legacy 的 `bench-2NN` 中，**26 个实际存在 `repro-data/run.sh`**，
9 个没有（bench-202/203/204/205/206/213/217/218/232）。
这 26 个**全部**在 `06_validate/report.md` 里有报告文件，即系统自认为跑完了 Package 阶段，
所以"优先挑有 report.md 的"这一条对全体成立，不构成区分度，实际区分维度落在产物体积上。

按 `du -sh repro-data` 排序后分层取样，大/中/小各 2 个：

| 层 | entry | 体积 | 选取理由 |
|---|---|---|---|
| 大 | bench-201 | 14G | 全样本体积最大，产物最"重"，最像一个真跑完的复现 |
| 大 | bench-219 | 6.4G | 第二大；含深度学习流程（提到 4× A100 / hg38 参考基因组），依赖面最广 |
| 中 | bench-230 | 1018M | 中位偏上；典型 Nextflow + Docker 组合 |
| 中 | bench-216 | 510M | 中位；依赖形态不同（以直接跑 R 为主，非 Nextflow），增加多样性 |
| 小 | bench-215 | 11M | 全样本体积最小，且 run.sh 行数最多之一（262 行），"脚本重、产物轻"的对照 |
| 小 | bench-200 | 19M | 第二小，且 check 逻辑最简（7 行），作为"最低门槛"对照 |

覆盖的 run.sh 行数区间为 157–287 行，依赖形态覆盖 Nextflow 系、纯 R 系、GPU 训练系。

---

## 3. 事实表

| entry | 产物体积 | run.sh 行数 | 退出码 | 首个失败原因 | 失败输出末尾片段（≤120 字符） |
|---|---|---|---|---|---|
| bench-201 | 14G | 208 | **1** | 缺宿主依赖：java 未找到（随后 nextflow、docker 亦缺） | `ERROR: docker 未找到（需要 Docker 容器运行时）` … `FAIL: 部分前置条件不满足，请修复后重试` |
| bench-219 | 6.4G | 287 | **1** | 缺宿主依赖：java 未找到（≥11） | `=== 检查前置条件 ===` / `[FAIL] Java 未安装（需要 ≥11）` |
| bench-230 | 1018M | 191 | **1** | 缺宿主依赖：java 未找到 | `=== 检查前置条件 ===` / `  [ERROR] Java 未安装（Nextflow 需要 Java 11+）` |
| bench-216 | 510M | 178 | **1** | 缺宿主依赖：R 未安装（需要 R ≥ 4.0） | `=== 检查前置条件 ===` / `❌ R 未安装（需要 R >= 4.0）` |
| bench-215 | 11M | 262 | **1** | 缺宿主依赖：java 未安装（随后 nextflow、docker/singularity 亦缺） | `ERROR: docker 或 singularity 至少需要一个` … `请先安装缺失的前置条件后再运行。` |
| bench-200 | 19M | 157 | **1** | 缺宿主依赖：nextflow 未找到 | `=== 检查前置条件 ===` / `ERROR: nextflow not found` |

### 各 run 的完整 check 输出（stdout+stderr，全部短于 15 行，故为全文）

**bench-201**（EXIT=1）
```
=== 检查前置条件 ===
ERROR: java 未找到（需要 Java 11+）
ERROR: nextflow 未找到
ERROR: docker 未找到（需要 Docker 容器运行时）

--- 磁盘空间 ---
Filesystem      Size  Used Avail Use% Mounted on
overlay          29T  3.7T   25T  14% /

FAIL: 部分前置条件不满足，请修复后重试
EXIT=1
```

**bench-219**（EXIT=1）
```
=== 检查前置条件 ===

[FAIL] Java 未安装（需要 ≥11）
EXIT=1
```

**bench-230**（EXIT=1）
```
=== 检查前置条件 ===

  [ERROR] Java 未安装（Nextflow 需要 Java 11+）
EXIT=1
```

**bench-216**（EXIT=1）
```
=== 检查前置条件 ===

❌ R 未安装（需要 R >= 4.0）
EXIT=1
```

**bench-215**（EXIT=1）
```
=== 检查前置条件 ===
ERROR: java 未安装（需要 Java 11+）
ERROR: nextflow 未安装
ERROR: docker 或 singularity 至少需要一个
OK: 补充材料数据已下载
WARN: 分析结果未生成，请先运行 'bash run.sh run'

请先安装缺失的前置条件后再运行。
EXIT=1
```

**bench-200**（EXIT=1）
```
=== 检查前置条件 ===
ERROR: nextflow not found
EXIT=1
```

---

## 4. 统计

### 退出码
- 退出码为 **0**：**0 / 6**
- 退出码为 **1**：**6 / 6**
- 超时（124）/ 段错误 / 语法错误：0

**6 个交付包在干净 `ubuntu:22.04` 容器里没有一个能通过自己的 `check`。**

### 失败原因归类（首个失败原因，n=6）

| 分类 | 计数 | 具体 |
|---|---|---|
| 缺宿主依赖（未在包内声明/自备的宿主工具链） | **6** | java ×4（201/219/230/215）、nextflow ×1（200）、R ×1（216）；其中 201/215 连 docker/singularity 也一并缺 |
| ├ 其中"缺宿主 docker" | 2 | bench-201、bench-215 显式报 docker/singularity 缺失 |
| 路径硬编码 | 0 | 未观察到；`ROOT` 均由 `dirname $0` 动态解析，拷贝到 `/work` 后仍正确 |
| 缺文件（包内应有而实际缺失） | 0 | 未成为首个失败原因；bench-215 的数据存在性检查甚至通过（`OK: 补充材料数据已下载`） |
| 脚本错误（语法/`set -euo pipefail` 误触发/未定义变量） | 0 | 6 个脚本均正常解析并执行到 check 逻辑，报错是**主动 `exit 1`**，不是崩溃 |
| 其他 | 0 | — |

### 需要如实说明的边界
- 这些 `exit 1` **不是脚本 bug**，而是脚本自己的前置条件判定生效后主动退出。
  从"脚本质量"角度看，check 分支写得是可用的：它准确说出了缺什么。
- 但从"交付物可执行性"角度看，结论是明确的：
  **交付包把整套运行时（Java 11+ / Nextflow / Docker CLI+daemon / R ≥ 4.0）当成了宿主既有环境，
  包内既不携带也不安装，README + run.sh 组合并不构成一个自包含的"一键重跑"制品。**
  尤其 bench-201 / bench-215 的失败直接落在"宿主没有 docker CLI"上——这正是任务里预判的
  "依赖宿主环境却未声明"的情形；按纪律，未在容器内安装 docker 去凑一个 0。
- 本次只测 `check`，因此**不能推断** `all` 分支能否跑通。`all` 的可执行性未测量，不做任何猜测。

---

## 5. 覆盖率

- **有 `run.sh` 的 run 总数：26 / 35**
- 缺 `run.sh` 的 9 个：`bench-202`、`bench-203`、`bench-204`、`bench-205`、`bench-206`、
  `bench-213`、`bench-217`、`bench-218`、`bench-232`
- 26 个有 run.sh 的 run **全部**存在 `06_validate/report.md`
- 本次实测覆盖：**6 / 26**（约 23%），分层抽样，非随机

### 全部 26 个有 run.sh 的 run（体积 / 行数）

| entry | 体积 | run.sh 行数 | 本次实测 |
|---|---|---|---|
| bench-215 | 11M | 262 | ✅ |
| bench-200 | 19M | 157 | ✅ |
| bench-211 | 19M | 98 | |
| bench-208 | 27M | 100 | |
| bench-220 | 38M | 302 | |
| bench-222 | 144M | 509 | |
| bench-229 | 240M | 144 | |
| bench-209 | 268M | 98 | |
| bench-227 | 271M | 151 | |
| bench-223 | 310M | 185 | |
| bench-212 | 370M | 107 | |
| bench-216 | 510M | 178 | ✅ |
| bench-231 | 565M | 210 | |
| bench-233 | 577M | 92 | |
| bench-221 | 688M | 206 | |
| bench-230 | 1018M | 191 | ✅ |
| bench-228 | 1.4G | 223 | |
| bench-207 | 1.5G | 187 | |
| bench-210 | 1.6G | 156 | |
| bench-214 | 1.7G | 230 | |
| bench-225 | 2.3G | 199 | |
| bench-226 | 2.5G | 182 | |
| bench-224 | 3.6G | 160 | |
| bench-234 | 3.8G | 253 | |
| bench-219 | 6.4G | 287 | ✅ |
| bench-201 | 14G | 208 | ✅ |
