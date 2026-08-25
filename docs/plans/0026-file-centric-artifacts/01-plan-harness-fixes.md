# Plan 01 — harness 修复（先修使数据不可信的缺陷）

依据：ADR-0011；backlog BL-018 / BL-019 / BL-024

## 为什么先做这个

35 篇批量的数据**不能作为能力测量**，根因全在 harness：

| 缺陷 | 证据 | 后果 |
|------|------|------|
| ~~容器出口网络不通~~ **已证伪** | 探针在运行时镜像 + 同款 flags 下实测：Crossref/EuropePMC/NCBI-FTP 全 `code=200`（`benchmarks/harness-probe.sh`） | 该假设作废；bench-213 的「curl 全超时」为个案（单 run），不是批次性根因 |
| **技能声明的前置从未满足**（实测真因） | `paperutils` 要求 bin `paperutils`（两端均不存在）、`mineru-api` 要求 env `MINERU_API_URL`（两端未设置）；探针报「未满足前置数: 2」 | 28/35 run 降级；agent 报「技能不可用」属实话 |
| 挂载 `/var/run/docker.sock` + 整个 `$HOMEDIR` | `bench-v3.sh:28,31` | 与 ADR-0009「host runtime socket 不进入 VM」冲突，结果不能作正式隔离证据 |
| DinD 挂载缺陷致 Nextflow 降级 | 19 个 run 手工降级为 `docker run` + `docker cp` | 交付的 `main.nf` 从未真正执行 |
| 镜像缺 wget | bench-234：`curl: (35) Recv failure` 紧接 `wget: command not found` | 下载回退路径静默失效，成为最高频失败的机械成因 |

**注意 BL-019 的诊断已纠正**：技能注入没有坏（loopflow 缺技能是 `raise RuntimeError`，
35 个 run 无一命中该报错），是网络断导致技能不可用、agent 误报为「技能不可用」。因此
本单元修网络，不动技能注入代码。

## 范围

1. ~~出口网络修复~~ → **改为技能前置补齐**（2026-08-22 实测后修正范围）：
   网络实测正常，无需修复；探针 `benchmarks/harness-probe.sh` 保留为回归证据（每次
   正式批次前跑一次，输出入库）。真正要补的是技能前置：
   - `paperutils`：确认 CLI 是否存在/可安装；不可得则从 `agents/reader.md` 的 `skills:`
     移除声明，并要求 Reader 直调 Crossref/EuropePMC API（探针已证可达）
   - `mineru-api`：确认是否有可用 MinerU 端点；有则由 harness 注入 `MINERU_API_URL`，
     无则同上移除声明
   - **不允许保留「声明了但用不了」的技能**：那会让 agent 每次都先撞墙再兜底，
     并把基建缺失伪装成能力缺失
2. **隔离边界**：从 `bench-v3.sh` 移除 `/var/run/docker.sock` 与 `$HOMEDIR` 全量挂载，
   改为**沙箱内嵌套 docker daemon（dind）**。
   **不需要 qemu、不需要 sudo**（2026-08-22 远端实测：`gs` 在 docker 组 gid 999、
   privileged 容器可运行、`/dev/fuse` 可用、`docker:latest` 镜像已在本地）。
   qemu/VM 只在产出**可发布级正式结果**时才需要（ADR-0009 / BR-013），属跑正式批次
   阶段的前置，不是本单元的前置——此处原先写「依赖 VM-local docker」是错误推理，已纠正。
   **副效应（很可能是 BL-021 的正解）**：Nextflow 的 docker executor 需把 work 目录挂进
   任务容器，而挂宿主 socket 时容器内路径对宿主 daemon 不存在，挂载必然失败 → 只能退回
   手工 `docker run` + `docker cp`（19 个 run 的实际情况）。嵌套 daemon 下沙箱内路径对
   该 daemon 真实存在，挂载成立
3. **DinD**：修 work 目录挂载使 Nextflow executor 可用；无法修则在 provision 阶段显式
   声明「Nextflow 不可用，降级为 docker run」并写入产物（不许静默降级）
4. **下载工具**：运行时镜像补 `wget`/`aria2c`，或统一 `curl -C -` 断点续传；provision
   自检验证下载工具存在

## 验收

| 项 | 判据 |
|----|------|
| 出口网络 | ✅ **已通过（2026-08-22）**：探针实测 3 个目标全 `code=200`，记录可复现 |
| 技能前置 | 探针 [3] 段「未满足前置数: 0」；当前为 2（paperutils bin、mineru-api env） |
| 技能可用性 | 保留声明的技能必须在同一容器内跑通一次真实调用；用不了的技能必须从 agent 声明中移除 |
| 隔离 | `bench-v3.sh` 不再挂 docker.sock 与 $HOMEDIR，改用嵌套 daemon；grep 可证 + 沙箱内 `docker info` 显示的是自己的 daemon |
| DinD | 一个最小 Nextflow 流程在容器内用 docker executor 跑通；或降级被显式写入产物 |
| 下载 | 断点续传实测：中断后续传成功，日志留下两段记录 |
| 回归 | 141 个确定性测试全绿 |

## 风险

- 出口网络可能受机构防火墙限制，非本项目可控 → 若不可修，必须把网络条件写入
  ExecutionEnvelope 并在所有结果中声明，使跨批次可比（不可默默继续）
- dind 需要 `--privileged`：它对宿主内核的暴露面仍大于 VM，但**不再暴露宿主 docker
  daemon**（去掉了「容器内即宿主 root」这条路径）。这是开发期的正确权衡；发布级结果
  仍须按 ADR-0009 走 VM，两者不可混同，结果标注必须区分
- dind 的镜像层与缓存不与宿主共享 → provision 首次拉取会变慢，且 BL-009 的「镜像复用」
  纪律需重新评估（复用范围从宿主 image store 变为沙箱内 store）
