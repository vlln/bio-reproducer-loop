---
title: Plan 013 - Tagged Runtime Formal Smoke
description: 使用 tagged runtime archive 和 fixed worker 的正式 bench-001 smoke 执行报告 — REPRODUCED 93/100，loopflow 全链路首次正式跑通
type: report
status: complete
created: 2026-08-04T06:30:00Z
---

# Plan 013 - Tagged Runtime Formal Smoke 执行报告

## 结论

**正式 smoke 成功。** 唯一 formal run 使用最新受控 source（repo `d30feef`、loopflow `0596c18`）、
fixed worker（qcow2 `18eb5e4a`）与 tagged runtime（`bio-reproducer-runtime:system`）在
QEMU/KVM disposable VM 中完成 `bench-001`：**loopflow 全 7 阶段真实执行，claimed_verdict
REPRODUCED（93/100）**。这是本 benchmark 项目历史上正式路径（formal/disposable-vm/qemu-kvm）
第一次跑通全链路并产生 REPRODUCED submission。

## 资产与门禁

| 资产 | 值 |
|------|-----|
| 受控 source（repo commit） | `d30feef1715fbbbbdaea9b4efd9b5e3c908eea1a` |
| loopflow commit / version | `0596c18f267303d28d2338e7da3ec5e5cb21c4ce` / 0.27.1 |
| worker qcow2 SHA256 | `18eb5e4a0f84e72a67e0940df3e033e03fe00e0f32d3a7add246290c1467d102` |
| runtime archive SHA256 | `7e706321c6896134bbe5660938f44906d53cf12f1b0b27701594bc9a690a23b5` |
| runtime reference | `bio-reproducer-runtime:system` |
| system artifact digest | `603b7dabeb53606f7efd8af4309edfc18e1de5ac425185e172d2b8124581b750`（submission 记录） |
| 唯一 submission | `bench-001-20260804T055739Z`（`repro-data/run_01/submission.json`） |

| 检查点 | 结果 |
|--------|------|
| CP-1 受控 source staged、home hash 记录、确定性门禁 | PASS（118 unit + 4 Docker probe + 7 bundle validators + lint 全绿；home hash `c04abf2b…`） |
| CP-2 worker/runtime/artifact 构建与校验 | PASS（qcow2 check、archive tag binding、validate-system、fresh daemon load/run probe） |
| CP-3 唯一 formal run + loopflow 启动证据 | PASS（见下） |
| CP-4 release-check、teardown、清理、home hash 复核 | PASS（release-check FORMAL；teardown completed；home hash 未变） |

## 唯一 Formal Run（bench-001）

```text
submission_id: bench-001-20260804T055739Z
claimed_verdict: REPRODUCED
total_score: 93.0
purpose / isolation / provider: formal / disposable-vm / qemu-kvm
network_policy: controlled-egress
duration_seconds: 6265（约 104 分钟，含 provision R 环境编译安装）
boot_seconds: 11.051
stages: Reader/Bootstrap/Provision/Data/Run/Validate/Package 全部 completed
artifacts: deseq2_results.csv、provision.md、figure1_volcano.png、run_results.md
teardown: completed（worker_absent / overlay_absent / secrets_revoked 全 true）
```

评分维度：data_integrity 25/25、process_quality 22.5/25、quantitative_concordance 25.5/30、
figure_and_finding_reproduction 20/20。结果正确性：Gene_A（log2FC 2.93, padj 4.4e-119）与
Gene_B（log2FC -2.01, padj 5.6e-42）显著、其余不显著，与论文合成设计一致；volcano 图与
DESeq2 结果表真实产出。

**loopflow 实际启动证据**：guest 事件日志显示 7 个 agent 全部执行（Reader 03:00 → Package
05:57），各阶段产物（plan.md/bootstrap.md/provision.md/data_manifest.md/run_results.md/
report.md/metrics.json/README.md）逐阶段落盘。

## 执行过程中修复的基础设施缺陷（均先于唯一 formal run 阻断并修复）

1. **skills 挂载缺陷**：launcher 原将 `/system/skills` 嵌套挂载进只读 loop 挂载
   （`/opt/loopflow/loops/bio-reproducer/.skills`），docker 因挂载点父目录只读无法创建 →
   loopflow exit 125。修复：改挂到 `~/.loopflow/skills`（loopflow 用户级 skills 回退路径）。
2. **claude 拒绝 root**：runtime 容器以 root 运行，Claude Code 拒绝
   `--dangerously-skip-permissions`。修复：launcher 以 `--user 1000:1000` + guest docker
   group（`--group-add $(stat -c %g /var/run/docker.sock)`）运行容器。
3. **HOME 权限**：docker 挂载处理以 root 创建 `.system-home/.loopflow`（0755）阻断非 root
   HOME 写入。修复：launcher 预创建该链并 `chmod 777`。
4. **超时策略**：初设 2h 硬超时过紧（provision R/BiocManager 编译安装即 ~1.5h），operator
   指示移除硬超时后以 12h deadline 重跑成功。deadline 记录于 submission
   `deadline_seconds: 43200`。
5. **runner 输出持久化**：早期 `--output` 指向未挂载宿主路径导致产物随 `--rm` 容器销毁；
   修复为显式挂载 `run-output`。

以上缺陷修复落地于 `benchmarks/runner/system_artifact.py`（launcher 生成）与 run 脚本参数，
随本容器提交于 `test/0013-tagged-runtime-formal-smoke` 分支（见该分支 commit）。

## Teardown 与残留审计

- qemu 进程：0；Plan 容器：0；runtime 镜像已卸载
- guest worker/overlay/secrets 全部清除（submission teardown 字段）
- 远端 `~/bio-reproducer` home hash 与 CP-1 记录一致（`c04abf2b…`，未修改）
- Plan 专属大文件（runtime.tar 2.1G、worker.qcow2 2.5G、cloud image 0.7G）已清理，
  证据（submission、repro-data 产物、digests、logs）保留于 Plan 根目录
- 历史 Plan 009/011 的 BLOCKED submission 未改动

## Acceptance 对照

| 编号 | 条件 | 结果 |
|------|------|------|
| TF-001 | Worker ready、qcow2/digest/check、runtime tag/config/archive binding | PASS |
| TF-002 | 唯一 run 为 formal/disposable-vm/qemu-kvm，InputBundle 边界成立 | PASS |
| TF-003 | loopflow 实际启动；submission 保留真实结果与 artifacts | PASS（REPRODUCED 93/100） |
| TF-004 | ExecutionEnvelope 记录 worker/system digest、network、deadline、teardown | PASS |
| TF-005 | Release-check 结果与 provenance、blocked 原因、teardown 一致 | PASS（FORMAL） |
| TF-006 | Guest 无法看到 oracle/repository/host docker socket 等 control-plane 资产 | PASS |

## 遗留

- 本轮修复的 launcher 缺陷（skills 挂载、非 root、HOME 权限）为系统代码变更，已提交于
  本分支，待合并 develop（不 push，除非用户要求）
- `sudo: unable to resolve host bio-reproducer-worker` 为 guest hostname 解析警告（无害），
  可后续在 worker cloud-init 补 /etc/hosts 条目
- 远端网络环境限制：Ubuntu cloud images 与 Docker Hub 直连被墙（provision 使用 apt/BiocManager
  本地源策略绕过），后续正式 run 需继续沿用该策略或配置镜像加速
