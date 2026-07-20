## 当前系统状态

| 字段 | 值 |
|------|-----|
| **当前阶段** | `TEST_INFRA`（评估信任边界重构） |
| **设计评估** | Spec v2、Interface 0001、ADR-0005/0006 已确认并冻结 |
| **基建评估** | Benchmark 协议 v2、六个 baseline 与确定性测试已完成；内部真实 LLM eval 和强隔离仍待执行 |
| **系统测试** | 32 个确定性测试通过；bench-001 至 bench-006 均已建立 v2 独立评估 baseline |

## 子目录

| 路径 | 用途 |
|------|------|
| [vision.md](vision.md) | 全局顶层愿景 |
| [spec/](spec/) | Spec 需求规格（用户故事、模块划分、数据模型、非功能指标） |
| [interface/](interface/) | 接口定义（入参/出参/错误码） |
| [adr/](adr/) | 架构决策记录 |
| [plans/](plans/) | 任务执行计划 |
| [ac/](ac/) | 验收标准 |
