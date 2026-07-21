## 当前系统状态

| 字段 | 值 |
|------|-----|
| **当前阶段** | `DESIGN`（InputBundle 材料真实性修订） |
| **设计评估** | ADR-0007、Spec v3、Interface 0001 修订与 AC-0003 已 proposed，待内容审查 |
| **基建评估** | 独立评分边界已验证；manifest validator、InputBundle fidelity、内部真实 LLM eval 和强隔离仍待执行 |
| **系统测试** | 32 个确定性测试通过；现有运行仅作为迁移期观测，不建立 tracked baseline |

## 子目录

| 路径 | 用途 |
|------|------|
| [vision.md](vision.md) | 全局顶层愿景 |
| [spec/](spec/) | Spec 需求规格（用户故事、模块划分、数据模型、非功能指标） |
| [interface/](interface/) | 接口定义（入参/出参/错误码） |
| [adr/](adr/) | 架构决策记录 |
| [plans/](plans/) | 任务执行计划 |
| [ac/](ac/) | 验收标准 |
