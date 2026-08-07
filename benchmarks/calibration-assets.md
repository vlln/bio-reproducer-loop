# ClaroAI 校准资产索引（BL-013）

> 防遗忘与无法复用：远端/本地产出必须落在固定位置并登记索引。
> 远端持久资产区：`/storeData/gs/claroai-calibration/`（runs/{bench-NNN}/、scripts/、system/）。
> 临时运行区：`/tmp/bl012/`（重启即失，完成后必须移出）。

## 批量校准脚本（远端）

- `bench-v3.sh`：docker 模拟 VM 边界跑 loopflow 全链路（时间戳目录，`bash bench-v3.sh <entry>`）
- `watch.sh`：run 完成检测（写 run-done.txt）
- `evaluate_run.py`（本文件所在仓库）：评估已完成 run

## 已完成校准（第一批，D2=2&D3=2 六篇）

| entry | 论文 | 系统 verdict | evaluator | 作者 cal | 完整产物 | 备注 |
|-------|------|-------------|-----------|----------|----------|------|
| bench-220 | SciTotalEnv epi | REPRODUCED 100 | REPRODUCED 100 | D1=2/D2=2/D3=2 | **丢失**（归档误操作） | 评估结果在 Report 024 |
| bench-222 | TorchXRayVision | REPRODUCED 100 | REPRODUCED 100 | D1=2/D2=2/D3=2 | **丢失**（归档误操作） | 同上 |
| bench-203 | MRI diffusion | REPRODUCED 100 | REPRODUCED 100 | D1=2/D2=2/D3=2 | 已归档 ✓ | |
| bench-221 | Cancer Control | REPRODUCED 100 | REPRODUCED 100 | D1=2/D2=2/D3=2 | 已归档 ✓ | 首次 run 失败后重启 |
| bench-223 | Comm Biol | BLOCKED | — | D1=2/D2=2/D3=2 | 已归档 ✓ | scMKL alpha=1.0 代码 bug（作者 D3=2 高评 vs 实际 bug） |
| bench-229 | Genome Biol | BLOCKED | PARTIAL 50 | D1=2/D2=2/D3=2 | 已归档 ✓ | GEO 下载受阻 + KPMP 注册；GSE220289 分歧；KPMP UUID/Zenodo DOI 命名边界 |

## 教训与规范

1. **完成即归档**：run 完成立即 `mv` 到持久区 + 登记本索引，勿事后批量移动（bench-200/220/222 产物因批量移动误操作丢失）
2. 丢失的 3 篇评估结果已保留（Report 023/024），如需完整产物需重跑
3. verify 模板（converter.py）已适配：Markdown 表格/属性-值表/URL 行、规范化模糊匹配、out-of-scope NA、状态词
