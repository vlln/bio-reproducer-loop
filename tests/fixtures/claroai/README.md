# ClaroAI-Bench 测试 fixture

来源：ClaroAI-Bench 归档 `papers/paper_XX/`（HF `kyleaoconnell22/claroai-bench` 快照，
GitHub `kyleaoconnell22/claroai-bench`），license **CC-BY-4.0**（HF dataset card）。

用途：`benchmarks/converters/claroai/` converter 的确定性单元测试输入（AC-0009-N-5
转录正确性、golden 对比、bundle gate 校验）。仅含元数据 JSON，不含论文全文。

| 样本 | 说明 |
|------|------|
| paper_01 | 计算论文（genomics_omics，PMID 41610471，D1=2/D2=0/D3=1）：4 个数据引用（GEO/SRA）+ 5 个代码引用（GitHub，主仓库为空壳） |
| paper_10 | 湿实验论文（wet_lab，PMID 41676480，is_computational=false）：仅 D1–D3 |

数据由 converter 测试按需读取，测试不联网、不依赖 `~/Project/claroai-bench` 的存在。
