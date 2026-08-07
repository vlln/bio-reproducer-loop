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
| bench-220 | SciTotalEnv epi | REPRODUCED 100（重跑） | REPRODUCED 100 | D1=2/D2=2/D3=2 | 已归档 ✓（重跑补回） | 评估一致 |
| bench-222 | TorchXRayVision | PARTIAL（重跑，图像网络限制） | REPRODUCED 100 | D1=2/D2=2/D3=2 | 已归档 ✓（重跑补回） | 元数据审计与作者一致；系统因图像数据网络限制自评 PARTIAL |
| bench-200 | HDM 多组学 | REPRODUCED（重跑；首次 BLOCKED 因参考基因组下载中断） | FAILED 0 | D1=2/D2=0/D3=1 | 已归档 ✓（重跑补回） | **校准发现**：重跑系统成功下载数据 → 与作者 D2=0 分歧（作者工具限制判不可下载，数据实际可获取——作者 D2 低估）；代码不完整判断与 D3=1 一致 |
| bench-203 | MRI diffusion | REPRODUCED 100 | REPRODUCED 100 | D1=2/D2=2/D3=2 | 已归档 ✓ | |
| bench-221 | Cancer Control | REPRODUCED 100 | REPRODUCED 100 | D1=2/D2=2/D3=2 | 已归档 ✓ | 首次 run 失败后重启 |
| bench-223 | Comm Biol | BLOCKED | — | D1=2/D2=2/D3=2 | 已归档 ✓ | scMKL alpha=1.0 代码 bug（作者 D3=2 高评 vs 实际 bug） |
| bench-229 | Genome Biol | BLOCKED | PARTIAL 50 | D1=2/D2=2/D3=2 | 已归档 ✓ | GEO 下载受阻 + KPMP 注册；GSE220289 分歧；KPMP UUID/Zenodo DOI 命名边界 |

**校准双向发现**：bench-200 重跑显示作者 D2=0 低估（数据实际可下载，作者工具链限制导致判不可下载）；bench-223 显示系统 alpha 参数路径问题（非论文 bug）——作者评分与确定性评分的差异**双向都有**，不能单向归因"作者高估"。

## 教训与规范

1. **完成即归档**：run 完成立即 `mv` 到持久区 + 登记本索引，勿事后批量移动（bench-200/220/222 产物因批量移动误操作丢失）
2. 丢失的 3 篇评估结果已保留（Report 023/024），如需完整产物需重跑
3. verify 模板（converter.py）已适配：Markdown 表格/属性-值表/URL 行、规范化模糊匹配、out-of-scope NA、状态词
