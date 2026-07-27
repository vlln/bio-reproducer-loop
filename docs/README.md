## 当前系统状态

| 字段 | 值 |
|------|-----|
| **当前阶段** | `DEVELOP`（Plan 010 正在执行 fixed-worker formal smoke） |
| **设计评估** | ADR-0009 accepted；Spec v4、Interface 0001 与 AC-0004 active |
| **基建评估** | Plan 008 已实现 QEMU/KVM worker、ExecutionEnvelope、release gate 与 pinned worker recipe；`gs` success/timeout smoke 通过 |
| **系统测试** | 102 个确定性测试与 4 个显式 Docker probe 通过；Plan 008 的 2 个真实 KVM smoke 通过；Plan 009 唯一 formal run 因原 worker 缺少 Docker 被阻塞，修复 worker 已独立验证；开发期不建立 tracked baseline |

正式契约要求 Runner/Curator 在可信控制面校验并 stage InputBundle，被测系统在每次
新建的 QEMU/KVM disposable VM 中读取只读 `/input` 并写入 `/workspace`、`/output`。Guest 可以
使用 root 与 VM-local Docker，但仓库、oracle、其他 entry、历史结果和 host runtime
socket 不进入 VM。Worker 使用预构建最小 image 与 fresh qcow2 overlay，实测 cold boot
约 10-11 秒。Opaque system artifact 已按 digest 构建并接入 adapter；下一步在新的执行容器
中使用修复后的 worker 做一次最小 formal smoke。完整 MinerU/R 等依赖不进入 worker base。

## 子目录

| 路径 | 用途 |
|------|------|
| [vision.md](vision.md) | 全局顶层愿景 |
| [spec/](spec/) | Spec 需求规格（用户故事、模块划分、数据模型、非功能指标） |
| [interface/](interface/) | 接口定义（入参/出参/错误码） |
| [adr/](adr/) | 架构决策记录 |
| [plans/](plans/) | 任务执行计划 |
| [ac/](ac/) | 验收标准 |
