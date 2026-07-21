## 当前系统状态

| 字段 | 值 |
|------|-----|
| **当前阶段** | `TEST_INFRA`（Plan 004 已完成，分支待审查合并） |
| **设计评估** | ADR-0007 accepted；Spec v3、Interface 0001 与 AC-0003 active |
| **基建评估** | bundle schema、validator、`validate-entry`、staging contract 与六个 entry 的人工 fidelity review 已通过；强隔离进入 Plan 005 |
| **系统测试** | 确定性测试通过；现有运行仅作为迁移期观测，不建立 tracked baseline |

当前隔离保证是 Runner 不将 control-plane 文件复制或传入运行时 InputBundle。若被测系统
在宿主机上拥有不受限的文件系统权限，OS/container 级强隔离仍需单独实现和验证。

## 子目录

| 路径 | 用途 |
|------|------|
| [vision.md](vision.md) | 全局顶层愿景 |
| [spec/](spec/) | Spec 需求规格（用户故事、模块划分、数据模型、非功能指标） |
| [interface/](interface/) | 接口定义（入参/出参/错误码） |
| [adr/](adr/) | 架构决策记录 |
| [plans/](plans/) | 任务执行计划 |
| [ac/](ac/) | 验收标准 |
