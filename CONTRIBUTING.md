## 一、开发环境

- [pixi](https://pixi.sh) — 环境和依赖管理
- [loopflow](https://github.com/vlln/loopflow) — workflow 运行时

**构建/配置入口：**

| 文件 | 用途 |
|------|------|
| `loops/bio-reproducer/pixi.toml` | 环境依赖声明 |
| `loops/bio-reproducer/workflow.py` | 工作流入口 |
| `pyproject.toml` | 本项目 Python 包配置 |

---

## 二、代码风格

- 格式化：遵循 PEP 8
- 命名：
  - 文件：snake_case
  - 变量/函数：snake_case
  - 类/接口：PascalCase
  - 常量：UPPER_SNAKE_CASE

---

## 三、Commit 规则

### 格式

```
<type>(<scope>): <简短描述>
```

| type | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| docs | 文档变更（必须独立提交，不与代码混合） |
| refactor | 重构 |
| test | 测试相关 |
| chore | 构建/工具/依赖 |

### devloop 约定

- 文档变更和代码变更永远分开 commit
- 阶段推进伴随独立 commit，前缀 `docs(state):`
- 文档 commit 格式：`docs(<scope>): <简述>`

---

## 四、分支策略

遵循 Gitflow：

```
main     ─────●──────────●────→  (tag: v0.1.0, v0.2.0)
              ↑          ↑
release  ──── v0.1.0 ─── v0.2.0
              ↑          ↑
develop  ────●──●──●──●──●──→  (持续集成)
              ↑  ↑  ↑
             ci/ feat/ fix/
```

| 分支 | 用途 | 从哪拉 | 合并到哪 |
|------|------|--------|---------|
| `main` | 仅含 release 节点，始终可部署 | — | — |
| `develop` | 持续集成分支 | `main` | — |
| `feat/*` `refactor/*` `perf/*` | 功能开发 | `develop` | `develop` |
| `ci/*` `test/*` `build/*` | 基建搭建 | `develop` | `develop` |
| `fix/*` | 集成修复 | `develop` | `develop` |
| `spike/*` | ADR 技术验证 | `develop` | 不合并（保留） |
| `release/*` | 版本发布 | `develop` | `main` + `develop` |
| `hotfix/*` | 生产热修复 | `main` | `main` + `develop` |

一个执行容器 = 一个分支，编号与执行容器对应。

---

## 五、版本策略

版本格式遵循 `MAJOR.MINOR.PATCH`（X.Y.Z），参考 [Semantic Versioning](https://semver.org/)：

| 段 | 何时升 | 示例 |
|----|--------|------|
| MAJOR | 不兼容的 API 变更 | `0.1.0 → 1.0.0` |
| MINOR | 新增功能，向后兼容 | `0.1.0 → 0.2.0` |
| PATCH | 向后兼容的 bug 修复 | `0.1.0 → 0.1.1` |

MAJOR=0 期间（0.x.y）：MINOR 升功能，PATCH 修 bug。

---

## 六、测试

### 测试命令

| 命令 | 用途 |
|------|------|
| `pytest tests/` | 确定性单元与契约测试；不得调用真实 LLM/网络/容器部署 |
| `make eval-component` | 单 Phase 真实 LLM 行为评测 |
| `make eval-handoff` | 跨 Phase 真实 LLM 行为评测，每个场景重复 5 次 |
| `make bench-l3` | 构造论文黑盒 benchmark |

### 测试目录

| 域 | 目录路径 | 说明 |
|----|---------|------|
| 单元测试 | `tests/unit/` | Runner、evaluator、adapter、解析和状态机 |
| 契约测试 | `tests/contract/` | Phase 协议、状态传播和错误处理 |
| Component eval | `evals/component/` | 单 Phase 真实 LLM 业务质量 |
| Handoff eval | `evals/handoff/` | 跨 Phase 语义传递与降级决策 |

真实 LLM 运行属于 eval，不属于 unit test。Eval 必须记录模型、Prompt、工具与环境版本，并通过重复运行报告分布。

内部 eval 按能力与失败模式建立 case，不要求每个 benchmark entry 跑全部 Phase。重复次数由
`evals/profiles.yaml` 控制，禁止在测试函数或 parametrization 中硬编码。上游 Phase 状态属于
fixture，不得同时作为期望完整输出使用。

---

## 七、PR 流程

- 从功能分支发起 PR 到 `develop`
- PR 描述需包含关联的 AC 编号
- CI 必须通过全部确定性 `tests/`
- 涉及 Prompt 或 Agent 行为的 PR 必须附对应 component/handoff eval 报告
- 至少一人 Review 通过后合并

---

## 八、许可证

MIT
