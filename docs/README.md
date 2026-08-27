## 当前系统状态

| 字段 | 值 |
|------|-----|
| **当前阶段** | `DESIGN`（**设计缺陷退回，2026-08-22**：发布就绪审计定级为契约缺陷——46 个 rubric check 读系统自评违反 BR-002、Package run.sh smoke 写入 Spec 但从未实现、phase 间事实载体为自由散文。ADR-0011 已 accepted，执行容器 0026 落地；受影响的 Spec 001 / Interface 0001+0002 / AC 需退回 proposed 修订并经人类再次 promote，之后回 SYSTEM_TEST 从失败层重跑）（历史：`SYSTEM_TEST` 完成，待发布决策（v0.2.0 已发布；本轮迭代 BL-011 ClaroAI-Bench 接入 + **Plan 0025 claims 模式修正**：35 个 L5 claims entry 落地（D5 数值声明 + 容差评分，D1–D3 为辅助证据）、`scored_scope` 机制删除（评分维度代码不再进入被测系统）、141 测试全绿、42 entry 全过 bundle gate；**系统能力验证完成（BL-012/BL-013 第一批）**：6 篇真实校准跑通全链路，claims 模式离线重评修正审计模式高估（bench-220 REPRODUCED 100 / bench-221 65 / bench-203 PARTIAL 30 / bench-200/223/229 FAILED）；校准方法论与独立验证原则已固化；RELEASE 门禁需人类批准） |
| **发布就绪审计** | **2026-08-22：35 篇批量完成后审计，结论为当前数据不足以支撑 benchmark/系统两篇论文**。已核实缺陷记入 backlog BL-014~BL-020：评分器为 301 行正则解析散文（BL-014，方向改 CORE-Bench 式 `report.json`）、19/35 entry 无数值 claims 且真值来自另一 LLM 审计（BL-015）、workflow 硬编码 RNA-seq goal 且无动态路由（BL-016）、校准 harness 挂 docker.sock 违反 ADR-0009 隔离契约（BL-018）、5 run 技能发现失败致配置不一致（BL-019）、与原作者 NeurIPS 投稿的定位切分（BL-020）。**人类决策与防返工排序见 [backlog.md](backlog.md) 末节**：S0（BL-017 失败分类学）→ S1（协议 v3）→ S2（claim 冻结）→ S3（系统修复+ablation）→ S4（baseline）→ S5（正式批次+formal VM），前三步零算力 |
| **设计评估** | ADR-0009/0010/0011 accepted；Spec 001、Interface 0001/0002、AC-0002/0005 **active**（单元 05 修订后经人类 promote，2026-08-27） |
| **基建评估** | Plan 008 已实现 QEMU/KVM worker、ExecutionEnvelope、release gate 与 pinned worker recipe；`gs` success/timeout smoke 通过；Plan 013 修复 launcher 三处缺陷（skills 挂载、非 root 运行、HOME 权限） |
| **系统测试** | Plan 013 正式 smoke：`bench-001` 在 QEMU/KVM disposable VM 中全 7 阶段真实跑通，claimed_verdict REPRODUCED、93/100，release-check FORMAL，teardown 完整；合并态 125 个确定性测试与 4 个显式 Docker probe 通过；不建立 tracked baseline（按 Plan 013 约定） |

正式契约要求 Runner/Curator 在可信控制面校验并 stage InputBundle，被测系统在每次
新建的 QEMU/KVM disposable VM 中读取只读 `/input` 并写入 `/workspace`、`/output`。Guest 可以
使用 root 与 VM-local Docker，但仓库、oracle、其他 entry、历史结果和 host runtime
socket 不进入 VM。Worker 使用预构建最小 image 与 fresh qcow2 overlay，实测 cold boot
约 10-11 秒。Opaque system artifact 现在同时记录构建侧 config ID 和 archive 内部 tag；
launcher 使用经结构校验的 tag，fresh daemon load/run gate 已通过。完整 MinerU/R 等依赖不
进入 worker base。

## 子目录

| 路径 | 用途 |
|------|------|
| [vision.md](vision.md) | 全局顶层愿景 |
| [spec/](spec/) | Spec 需求规格（用户故事、模块划分、数据模型、非功能指标） |
| [interface/](interface/) | 接口定义（入参/出参/错误码） |
| [adr/](adr/) | 架构决策记录 |
| [plans/](plans/) | 任务执行计划 |
| [ac/](ac/) | 验收标准 |
