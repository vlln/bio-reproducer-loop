# Plan 06 — 交付包自包含（BL-025 / FC-008）

依据：ADR-0011 §2/§5（FC-008）、BL-025；证据 `benchmarks/package-executability-probe.md`
（0/6 干净容器通过，根因：交付包把 Java/Nextflow/Docker/R 当宿主既有环境）。

## 目标

Package 交付物首次具备可执行证明：`run.sh check` 在干净容器（只有 Docker）中通过，
且 Package 声明 completed 必须有真实执行日志（退出码 0）。

## 自包含边界（设计决策，留档）

**交付包只要求 Docker**。Java/Nextflow/R/分析环境全部在镜像内——镜像清单由
`03_provision/digests.txt`（单元 04 已落，docker images --digests 输出）+ Dockerfile
提供；run.sh 自动 inspect（缺失则按清单 build）。这是「干净 ubuntu 容器 + docker 能过
check」的可验证目标（0/6 的缺 java/nextflow/R 全部消除），不过度设计（不要求无 Docker
宿主也能跑——Docker 是通用运行时前置，等价于 Java 之于 Maven）。

## 改动点

### 1. `agents/package.md`：自包含规则 + check 执行日志

- 新增「自包含」规则节：只要求 Docker；分析环境在镜像内（从 `03_provision/digests.txt`
  读镜像清单；缺失镜像时 `check` 提示、`provision` 分支自动 build 包内 Dockerfile）；
  宿主 java/nextflow/R 不作为前置（check 不再检查它们）
- run.sh 模板更新：`check` = docker 可用 + digests.txt 中镜像 `docker image inspect`
  通过（或给出明确 build 指引）；`run`/`validate` = `docker run` 分析镜像（挂载
  `$ROOT` 为 work 目录）
- **新增 FC-008 证据**：Package 必须实际执行 `bash run.sh check`，输出保存为
  `07_package/check.log`（含退出码 0 记录）；未执行或退出码非 0 → 不得声明 completed

### 2. `artifact_checks.py`：`check_package_phase`

判据：`run.sh` 存在（交付根目录）+ `07_package/check.log` 存在且含退出码 0 记录
（`exit 0` / `EXIT=0` / `status: 0` 任一种，标准格式）。返回 (ok, detail)。

### 3. `workflow.py`：Package 后 `_require_parsable(check_package_phase)`

Package agent 返回 complete 但无 check.log（或退出码非 0）→ fail-fast（FC-008）。

### 4. 测试

- `check_package_phase` 四态（ok / 缺 run.sh / 缺 check.log / 退出码非 0）
- package.md prompt 断言（自包含 markers：只要求 Docker、digests.txt、check.log）
- workflow：Package 后 fail-fast 用例；happy path 补 package evidence
- 全套回归

## 验收

| 项 | 判据 |
|----|------|
| 自包含规则 | package.md 含「只要求 Docker / digests.txt 镜像清单 / run.sh check 不再查宿主 java/nextflow/R」 |
| FC-008 | Package 无 check.log 或退出码非 0 → fail-fast；check.log 退出码 0 → 通过 |
| 回归 | 全套确定性测试全绿 |

## 风险与边界

- 已归档 35 个 run 的 run.sh 是旧契约（查宿主工具链）——不重写旧产物；新 run 的
  Package agent 按新规则打包；干净容器验证由 run-entry.sh 首次实跑时执行
- run.sh 的 `all` 分支不在本单元实测（probe 边界：只测 check，all 的可执行性未测量
  不做猜测）
- 「只要求 Docker」假设 docker CLI + daemon 在接收方环境可用（run-entry.sh 的 dind
  sidecar 已验证此路径）
