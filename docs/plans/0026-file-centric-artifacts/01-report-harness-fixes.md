# Report 01 — harness 修复

对应 [Plan 01](01-plan-harness-fixes.md)。全部结论基于远端实测，脚本入库可复现。

## 交付物

| 文件 | 用途 |
|------|------|
| `benchmarks/harness-probe.sh` | 前置探针：出口网络 / 下载工具 / **技能 SKILL.md 声明的 requires.bins·env** |
| `benchmarks/harness/run-entry.sh` | 取代仅存在于远端、未版本管理的 `bench-v3.sh`；dind sidecar 架构 + `selftest` 模式 |

## 验收结果

| 项 | 判据 | 结果 |
|----|------|------|
| 出口网络 | 探针目标全 200 | ✅ Crossref / EuropePMC / NCBI-FTP 全 `code=200`（运行时镜像 + 同款 flags） |
| 技能前置 | 未满足数为 0 | ❌ **当前 2 项**：`paperutils` bin（两端均不存在）、`mineru-api` env `MINERU_API_URL`（未设置）→ 待决策：补齐或移除声明 |
| 隔离 | 不挂 docker.sock | ✅ 新 harness 不挂 socket；沙箱内 `[ -S /var/run/docker.sock ]` 为假；`docker version` 指向 dind |
| DinD | Nextflow docker executor 跑通 | ✅ selftest 第 6 项产出 `nextflow-docker-executor-ok`（publishDir 落到 `/output`） |
| 下载续传 | 中断后续传成功 | ✅ 249MB 文件：第一段 13,479,599 B → `curl -C -` 得 **HTTP 206** → 13,647,134 B |
| 回归 | 141 测试全绿 | ✅ |

## 架构：privileged 只落在 sidecar

```
[dind sidecar]  --privileged, 无宿主 socket, 挂 /input /workspace /output（与沙箱同路径）
      ▲ tcp://dind:2375（per-run 私有网络）
[沙箱容器]      --cap-drop ALL --user 1000:1000, 只挂 docker **客户端二进制**（只读）
```

关键点：sidecar 与沙箱把 run 目录挂在**相同路径**，因此沙箱内 `docker run -v /output/x:/y`
对 dind daemon 是真实路径。**这正是 BL-021 的根因所在**——挂宿主 socket 时该路径对宿主
daemon 不存在，挂载必然失败，19 个 run 因此退回手工 `docker run` + `docker cp`。selftest
第 3/4/6 项已证明新架构下挂载、写回、Nextflow executor 全部成立。

## 实测挖出的四个隐藏前提（原设计都没写）

1. **dind 不继承宿主 registry-mirrors**：新 daemon 直连 `registry-1.docker.io` i/o timeout
   （BL-008 的 Docker Hub 封锁），任务容器一个镜像都拉不到。harness 现从宿主
   `docker info` 读 mirror 并透传 `--registry-mirror`
2. **运行时镜像内无 docker CLI**（实测 MISSING，bench-v3.sh 是从宿主挂 `/usr/bin/docker`）
   → 新 harness 只挂客户端二进制、不挂 socket
3. **Nextflow docker executor 要求任务镜像内有 `/bin/bash`**（以 `/bin/bash -ue` 启动）：
   用 alpine 会 exit 127。这可能是复现真实论文时的隐性坑（很多 biocontainer 是 alpine 基底）
4. **`wget` 与 `aria2c` 均缺失，但 `curl -C -` 可用且 NCBI 支持 Range** → BL-024 的正解是
   统一用 `curl -C -` 断点续传，不必往镜像里加 wget

## 未完成 / 移交

- **技能前置 2 项待决策**：`paperutils` CLI 是否存在？是否有可用 MinerU 端点？无则按 Plan 01
  纪律从 `agents/reader.md` 移除声明并让 Reader 直调 API（探针已证 Crossref/EuropePMC 可达）
- `run-entry.sh` 尚未跑过完整 entry（仅 selftest）；首次实跑安排在单元 02 契约改造之后，
  避免用旧产物契约跑一遍再改一遍
- 远端 `bench-v3.sh` 暂留但**不应再用于新 run**；确认 `run-entry.sh` 跑通完整 entry 后删除
- 实测传输速率约 674 KB/s（≈40 MB/min）：10GB 级数据集约需 4 小时 → 单元 03 的路由/预算
  设计必须把「大数据集需要长时间但可续传」与「不可获取」区分开（ADR-0011 §2.1 已定原则）
