---
title: Interface 001 — Benchmark 输入、执行、提交与评估协议
description: 定义 disposable VM execution envelope、可追溯 InputBundle、SubmissionBundle、EvaluatorResult 及其信任边界。
type: interface
status: proposed
created: 2026-07-19T00:00:00Z
---

# Interface 001: Benchmark 输入、执行、提交与评估协议

## 信任边界

```text
trusted control plane
├── Runner / Curator / bundle validator
├── worker image resolver / artifact collector
├── private oracle / evaluator
└── disposable VM (untrusted system boundary)
    ├── runner-owned immutable worker base
    ├── opaque system artifact + guest root + VM-local Docker
    ├── read-only InputBundle
    └── writable workspace / output
```

正式结果的 `isolation` 固定为 `disposable-vm`。Docker sandbox、mock executor 或 host
execution 不是并列的正式 runtime；允许存在的 Docker sandbox 结果必须标为
`validation-only`，release gate 不接受其进入 baseline。

## InputBundle

Runner 校验 `entries/<id>/bundle.yaml` 后，将整个 `input/` 物化到 entry-local staging，
再以只读语义 attach 到 disposable VM，并只向被测系统提供该目录。`bundle.yaml`、
`metadata.yaml`、`oracle/`、baseline、其他系统的历史结果和故障注入意图不属于运行时
InputBundle。

```text
entries/<id>/
├── bundle.yaml            # 必需，Runner 校验，不 stage
├── input/                 # 被测系统唯一可见
│   ├── paper/             # 论文原始文件与场景允许的派生表示
│   ├── supplementary/     # 补充材料原件
│   ├── code/              # cited code 的冻结快照
│   ├── data/              # 冻结数据、派生数据或访问 descriptor
│   ├── resources/         # 场景实际提供的辅助材料
│   └── questions.yaml     # 公开问题清单（ADR §4.1，单元 04）：target_id+question+unit，
│                          # 无期望值；被测系统按 target_id 填 answers.csv
├── oracle/                # evaluator 私有
└── metadata.yaml          # Runner 元数据，不 stage
```

每个 staged 文件都必须由 `bundle.yaml` 中的一个 resource 声明。目录可以不存在，但论文
引用而未打包的资源必须在控制平面有带状态的 resource record，不能通过省略目录表达。
该记录用于完整性审查，不会告诉被测系统哪些资源缺失、受限或由 benchmark 注入。
若 rubric 允许系统因资源限制而降级，该限制必须能从 staged input 或运行环境中观察，
不能只存在于 `bundle.yaml`。

### bundle.yaml

```yaml
schema_version: "1.0"
entry_id: bench-100
level: L4
input_root: input
primary_paper: paper-main
resources:
  - id: paper-main
    role: paper
    authority: original
    path: paper/article.pdf
    source: https://doi.org/10.1371/journal.pone.0099625
    retrieved_at: 2026-07-20T00:00:00Z
    sha256: "<64 lowercase hex characters>"
    media_type: application/pdf
    license: CC-BY-4.0
    availability: bundled
  - id: paper-markdown
    role: paper
    authority: derived
    path: paper/article.md
    availability: bundled
    derived_from: [paper-main]
    transform:
      tool: mineru
      version: "<version>"
      command: "<reproducible command or script path>"
  - id: cited-code
    role: code
    authority: original
    source: https://example.org/cited-repository
    availability: unavailable
    checked_at: 2026-07-20T00:00:00Z
    access_notes: Repository returned 404 during bundle review.
```

### BundleResource

| 字段 | 必需 | 说明 |
|------|------|------|
| `id` | 是 | entry bundle 内稳定且唯一的资源 ID |
| `role` | 是 | `paper` / `supplementary` / `code` / `data` / `metadata` / `environment` / `resource_page` / `questions` |
| `authority` | 是 | `original` / `derived` / `benchmark`（benchmark 自产资源如 questions.yaml，converter 确定性生成，不要求 derived_from） |
| `availability` | 是 | `bundled` / `external` / `restricted` / `unavailable` / `not_applicable` |
| `path` | bundled 时 | 相对 `input_root` 的文件路径；禁止绝对路径和 `..` |
| `source` | original 时 | DOI、accession、仓库/发布页 URL；constructed L3 使用 `urn:benchmark:<entry>:<resource>` |
| `sha256` | bundled 文件时 | 文件内容校验和 |
| `retrieved_at` | bundled original 时 | 获取时间 |
| `media_type` | bundled 文件时 | IANA media type |
| `license` | 可选 | SPDX ID 或原始许可说明 |
| `derived_from` | derived 时 | 一个或多个上游 resource ID |
| `transform` | derived 时 | 可重复的工具版本、命令或脚本路径 |
| `checked_at` | unavailable/restricted 时 | 可用性核查时间 |
| `access_notes` | unavailable/restricted 时 | 核查位置、访问条件或失败事实 |

### Level 约束

| Level | primary paper | resources |
|-------|---------------|-----------|
| L3 | constructed original，可为 Markdown/PDF | 场景需要的构造材料；虚构或不可用引用必须登记 |
| L4 | 真实发布的 original PDF/XML/HTML | 所有 cited resources 必须 bundled、restricted 或 unavailable；派生/裁剪材料必须可追溯 |
| L5 | original paper 或稳定 DOI/PMID/arXiv locator | 允许 external，运行时执行真实资源发现并记录结果 |

Bundle lock 不得包含 scientific expected values、rubric checks、score、expected verdict
或故障注入原因。它描述 benchmark maintainer 审计的材料事实；故障注入意图进入 private
oracle。Runner 必须保证 bundle lock 不出现在被测系统的工作目录、Prompt 或工具上下文中。

## FormalExecution

### Worker 与 system contract

Runner 使用按 digest 固定、由控制面管理的 immutable worker image。Worker 提供 guest
启动、control channel、I/O attach 和 VM-local runtime；不得内置 entry oracle。Adapter
将被测系统作为 opaque system artifact 注入 guest，并提供 guest 内启动命令。

System artifact 可以在内部使用 Pixi、Conda、OCI、源码安装或多 container workflow。
这些形式不得进入 entry schema 或 formal runtime enum。公共协议只记录 artifact digest
和 adapter identity。

当前 formal provider 固定为 `qemu-kvm`，使用 immutable Ubuntu base、fresh qcow2
overlay、virtio block/network、virtiofs I/O 与 QMP lifecycle。Worker image 预装 Docker；
不得在每个 run 中在线安装基础设施依赖。QEMU 无法启用 KVM 时必须失败，不得回退 TCG。

### 生命周期

1. 校验 InputBundle、worker image digest、system artifact digest 与 network policy。
2. 从 immutable base 创建 fresh writable overlay，不恢复失败 run 的 overlay。
3. Attach read-only input、独立 writable workspace/output；注入最小权限临时 secret。
4. 启动 guest 和被测系统；Runner 在 VM 外执行 wall-clock deadline。
5. 被测系统退出后停止 guest，只从 output 构造 SubmissionBundle。
6. 删除 guest process、VM-local container、overlay、attach point 和临时 secret。
7. Teardown 审计通过后，formal run 才可进入 release report 或 baseline。

### 网络策略

| `network_policy` | 语义 |
|------------------|------|
| `offline` | Guest 无外部 egress；仅保留 runner control channel |
| `controlled-egress` | Guest 可访问 entry 允许的外部资源；控制面仍不可达 |

Entry 的 `offline` interaction mode 映射为 `offline`；`discovery` 与 `tool-runtime` 映射为
`controlled-egress`。这是网络策略差异，不是 runtime backend 差异。临时凭据的值不得写入
ExecutionEnvelope、Runner-owned 日志或报告；只记录凭据名称、来源类型与失效状态。被测
系统获得凭据后仍可能主动写入 output 或经允许网络外传，控制面必须使用最小权限、独立
额度、短期有效且可撤销的凭据，不能把 VM isolation 当作 secret confinement。

### ExecutionEnvelope

```json
{
  "purpose": "formal",
  "isolation": "disposable-vm",
  "provider": "qemu-kvm",
  "worker_image": {
    "id": "bio-reproducer-worker",
    "digest": "sha256:<64 lowercase hex characters>"
  },
  "system_artifact": {
    "digest": "sha256:<64 lowercase hex characters>",
    "adapter": "loopflow-adapter@0.1.0"
  },
  "network_policy": "offline",
  "deadline_seconds": 3600,
  "duration_seconds": 42,
  "teardown": {
    "status": "completed",
    "worker_absent": true,
    "overlay_absent": true,
    "secrets_revoked": true
  },
  "stages": []
}
```

`purpose=formal` 时 `isolation`、`provider=qemu-kvm`、两个 digest、network policy、
deadline 和 completed teardown 全部必需。当前不允许 provider fallback。`purpose` 为
`validation-only` 时可以记录 Docker sandbox provenance，但不得伪装成 `disposable-vm`。

## SubmissionBundle

被测系统执行结束后，adapter 生成 `submission.json`，所有路径相对于 submission 根目录。

```json
{
  "protocol_version": "2.0",
  "submission_id": "bench-001-20260719T120000Z",
  "bench_id": "bench-001",
  "system": {"name": "bio-reproducer", "version": "0.1.0"},
  "claimed_verdict": "REPRODUCED",
  "artifacts": [
    {"role": "result_table", "id": "treatment_vs_control", "path": "artifacts/deseq2_results.csv"},
    {"role": "figure", "id": "volcano", "path": "artifacts/volcano.png"},
    {"role": "run_log", "path": "artifacts/run.log"}
  ],
  "execution": {
    "purpose": "formal",
    "isolation": "disposable-vm",
    "provider": "qemu-kvm",
    "worker_image": {"id": "bio-reproducer-worker", "digest": "sha256:<digest>"},
    "system_artifact": {"digest": "sha256:<digest>", "adapter": "loopflow-adapter@0.1.0"},
    "network_policy": "offline",
    "deadline_seconds": 3600,
    "duration_seconds": 42,
    "teardown": {"status": "completed"},
    "stages": []
  }
}
```

`claimed_verdict` 可缺省且不参与最终分数计算。Artifact role 允许扩展，但未知 role
必须被 evaluator 保留而非静默丢弃。同一 role 存在多个语义产物时必须提供稳定的 `id`
（例如 contrast 名称），oracle 可以声明正反 contrast 或合并表为等价证据，但不得改写系统原始产物。

## 被测系统标准格式产物（ADR-0011 §2，单元 02-04 落地）

被测系统（引擎无关）必须按以下标准格式持久化事实；**外部评分只读这些产物，
不读任何系统散文报告**。`06_validate/` 整目录不在证据面（FC-006）——Validate 是
系统内部自反馈路由，`claimed_verdict` 只作校准观测。

| 阶段 | 必须落下的标准格式产物 | 可核验方式 |
|------|----------------------|-----------|
| 03_provision | `digests.txt`：`docker images --digests` 原始输出 | 任何人可重算核对 |
| 04_data | 数据文件本体 + `sha256sums.txt`（sha256sum 输出）+ **每资源一份获取日志**（curl/wget 原始输出；阻塞时也必须落） | `sha256sum -c`；日志终态判定（completed/unavailable/not_attempted，§2.1） |
| 05_run | `results/` 结果 CSV/TSV + `answers.csv`（`target_id,value,unit,source_file`，表头精确白名单）+ `reports/commands.log`（命令+退出码） | 标准 csv 解析；answers 值须能在 source_file 定位（FC-005） |
| 07_package | `run.sh` + 干净环境执行日志（含退出码） | 执行日志退出码为 0（FC-008，单元 06） |

允许的自定义格式只有两类（FC-002/FC-003 键名白名单）：
- `05_run/answers.csv`：4 列 `target_id,value,unit,source_file`，无状态词/判断/理由
- `06_validate/routing.jsonl`：5 键 `ts,target,decision,route_to,reason`，追加式一行一事件，
  系统内部路由（数据不符→data、环境/版本→provision、参数/步骤→run、论文理解→reader）

**NO-EVIDENCE 语义**（FC-005）：answers 值无法在自述 source_file 中定位、产物缺失或
target 缺失 → 该 claim 记为 `no_evidence`，**不计分不扣分**（不是判错）；全部 check
均无证据 → evaluator 返回 BLOCKED，score 不构成复现率。

已存在的 protocol v1 运行仍可执行 `bench-run submit --entry <id>`，从 `repro-data/` 补建
manifest 并由 evaluator 生成历史观测；原系统生成的 `result.json` 保留为
`legacy-result.json`。由于 v1 没有 disposable VM 与 teardown provenance，这类 submission
不得进入 protocol v2 baseline，必须在 formal VM 中重新运行。

## OracleBundle

| 路径 | 必需 | 说明 |
|------|------|------|
| `claims.yaml` | 是 | 论文与数据的结构化科学事实 |
| `rubric.yaml` | 是 | 检查项、证据、比较器、容差和权重 |
| `expected-results/` | 否 | 参考表格、集合、图像特征或 checksum |
| `verify.py` | 否 | Entry 特定的纯评估逻辑 |

## EvaluationResult

Evaluator 独立生成 `result.json`：

```json
{
  "run_id": "bench-001-20260719T120000Z",
  "bench_id": "bench-001",
  "benchmark_version": "2.0.0",
  "submission_id": "bench-001-20260719T120000Z",
  "verdict": "REPRODUCED",
  "score": 87.5,
  "checks": [],
  "calibration": {"claimed_verdict": "REPRODUCED", "matches": true},
  "provenance": {"evaluator_version": "2.0.0", "oracle_version": "1.0.0"}
}
```

## 错误语义

| code | 含义 |
|------|------|
| `INVALID_INPUT` | InputBundle 不完整或损坏 |
| `INVALID_BUNDLE` | bundle schema、checksum、层级完整性、派生关系或 staged 文件集合不合法 |
| `INVALID_SUBMISSION` | manifest 缺字段、路径越界或 artifact 不存在 |
| `INVALID_ORACLE` | rubric 或 verifier 配置错误 |
| `INVALID_EXECUTION_ENVIRONMENT` | worker/system digest、execution envelope 或 attach contract 不合法 |
| `WORKER_UNAVAILABLE` | 节点不能提供 formal disposable VM，不允许回退到 host/container |
| `WORKER_BOOT_FAILED` | Guest 启动或 control channel 建立失败，属于 infrastructure error |
| `EXECUTION_BLOCKED` | 被测系统未完成执行 |
| `EXECUTION_TIMEOUT` | 被测系统超过 runner-owned deadline；仍必须 teardown |
| `ARTIFACT_COLLECTION_ERROR` | Output attach 或 submission 收集失败，属于 infrastructure error |
| `TEARDOWN_ERROR` | VM/container/overlay/secret 存在残留；结果不可发布 |
| `EVALUATION_ERROR` | evaluator 内部错误，不计为系统能力失败 |
