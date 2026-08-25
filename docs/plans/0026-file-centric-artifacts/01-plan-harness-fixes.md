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
2. **隔离边界**：从 `bench-v3.sh` 移除 `/var/run/docker.sock` 与 `$HOMEDIR` 全量挂载；
   容器内需要 docker 时改用 VM-local docker（qemu 装好后）或显式声明为 validation-only
3. **DinD**：修 work 目录挂载使 Nextflow executor 可用；无法修则在 provision 阶段显式
   声明「Nextflow 不可用，降级为 docker run」并写入产物（不许静默降级）
4. **下载工具**：运行时镜像补 `wget`/`aria2c`，或统一 `curl -C -` 断点续传；provision
   自检验证下载工具存在

## 验收

| 项 | 判据 |
|----|------|
| 出口网络 | 探针脚本 4 个目标全部拿到真实响应（非超时），输出可复现记录文件 |
| 技能可用性 | 同一容器内 paperutils / mineru-api / biocontainers 各跑一次真实调用成功 |
| 隔离 | `bench-v3.sh` 不再挂 docker.sock 与 $HOMEDIR；grep 可证 |
| DinD | 一个最小 Nextflow 流程在容器内用 docker executor 跑通；或降级被显式写入产物 |
| 下载 | 断点续传实测：中断后续传成功，日志留下两段记录 |
| 回归 | 141 个确定性测试全绿 |

## 风险

- 出口网络可能受机构防火墙限制，非本项目可控 → 若不可修，必须把网络条件写入
  ExecutionEnvelope 并在所有结果中声明，使跨批次可比（不可默默继续）
- 移除 docker.sock 后容器内无法用 docker → 依赖 qemu VM-local docker，而 qemu 需人类
  安装（已认领）；未装好前该项标注为 blocked，不得以「继续挂 socket」绕过
