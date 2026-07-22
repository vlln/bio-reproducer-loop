## 执行容器

| 容器 | 分支 | 状态 |
|------|------|------|
| [0001-benchmark-infra](0001-benchmark-infra/) | — | done |
| [0002-l4-l5](0002-l4-l5/) | — | pending |
| [0003-evaluation-boundaries](0003-evaluation-boundaries/) | `refactor/0003-evaluation-boundaries` + stacked closeout | done |
| [0004-input-bundle-fidelity](0004-input-bundle-fidelity/) | `refactor/0004-input-bundle-fidelity` | done |
| [0005-runtime-isolation](0005-runtime-isolation/) | `refactor/0005-runtime-isolation` | done |

当前阶段：TEST_INFRA。Plan 003 已完成独立 evaluator、测试分域和 14-case 真实 LLM
smoke；Plan 004 已完成 InputBundle 契约、validator、staging、六个 entry 迁移和人工
fidelity review；Plan 005 已完成 Docker 强隔离、execution profile、timeout 清理和真实
escape probe。Plan 002 继续负责 bio-reproducer/L4 执行环境冻结；隔离验证按能力取样，
不要求对全部 benchmark entry 重复运行。
