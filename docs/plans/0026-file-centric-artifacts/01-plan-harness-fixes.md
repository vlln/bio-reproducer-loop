# Plan 01 — harness 修复（先修使数据不可信的缺陷）

依据：ADR-0011；backlog BL-018 / BL-019 / BL-024

## 为什么先做这个

35 篇批量的数据**不能作为能力测量**，根因全在 harness：

| 缺陷 | 证据 | 后果 |
|------|------|------|
| 容器出口网络不通 | bench-213 原文「容器环境没有外网连接（所有 curl 请求超时），MinerU API 和 paperutils 工具也都不可用」；28/35 run 处于降级配置 | 系统能力被系统性低估，跨 entry 不可比 |
| 挂载 `/var/run/docker.sock` + 整个 `$HOMEDIR` | `bench-v3.sh:28,31` | 与 ADR-0009「host runtime socket 不进入 VM」冲突，结果不能作正式隔离证据 |
| DinD 挂载缺陷致 Nextflow 降级 | 19 个 run 手工降级为 `docker run` + `docker cp` | 交付的 `main.nf` 从未真正执行 |
| 镜像缺 wget | bench-234：`curl: (35) Recv failure` 紧接 `wget: command not found` | 下载回退路径静默失效，成为最高频失败的机械成因 |

**注意 BL-019 的诊断已纠正**：技能注入没有坏（loopflow 缺技能是 `raise RuntimeError`，
35 个 run 无一命中该报错），是网络断导致技能不可用、agent 误报为「技能不可用」。因此
本单元修网络，不动技能注入代码。

## 范围

1. **出口网络**：定位远端容器出口失效原因（DNS / 代理 / 防火墙 / registry 镜像策略，
   关联 BL-008），修复后以可复现的探针脚本验证：Crossref、PMC、GEO FTP、Docker Hub 镜像源
   各一次真实请求，记录状态码与字节数
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
| 出口网络 | 探针脚本 4 个目标全部拿到真实响应（非超时），输出可复现记录文件 |
| 技能可用性 | 同一容器内 paperutils / mineru-api / biocontainers 各跑一次真实调用成功 |
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
