"""Phase 产物契约检查（ADR-0011 §2/§5，单元 02 范围：Data phase）。

事实以标准格式文件持久化；本模块只做「存在 + 可被标准工具解析」的检查，
不校验自定义字段、不含任何评分阈值（FC-001/FC-002 的检出手段）。

终态类别判定（ADR-0011 §2.1）：区分「未完成获取」「外部不可得」「已获取」
依据**终态信号**而非尝试次数——传输层失败（curl: (35)/(56)、超时、连接重置）
属未完成获取；HTTP 404/403/451 与注册墙/DUA 属外部不可得；`Download complete`
+ 文件存在属已获取。系统内不写死任何重试次数/比例常量。
"""
import re
from pathlib import Path

# ── 终态类别（ADR-0011 §2.1）──────────────────────────────────────────
COMPLETED = "completed"            # 已获取：Download complete + 文件存在
UNAVAILABLE = "unavailable"        # 外部不可得：HTTP 404/403/451、注册墙/DUA
NOT_ATTEMPTED = "not_attempted"    # 未完成获取：传输层失败、回退工具缺失

# 已获取信号（优先级最高：中间失败被续传克服后终态仍是完成）
_COMPLETE_RE = re.compile(r"Download complete")

# 外部不可得信号：HTTP 4xx 与访问墙
_UNAVAILABLE_RES = [
    re.compile(r"HTTP/[0-9.]+ 40[1345]\b"),
    re.compile(r"HTTP/[0-9.]+ 451\b"),
    re.compile(r"The requested URL returned error: 40[1345]\b"),
    re.compile(r"404 Not Found"),
    re.compile(r"403 Forbidden"),
    re.compile(r"requires?\s+(registration|a registered account)", re.I),
    re.compile(r"access\s+(denied|restricted)", re.I),
]

# 传输层失败信号：curl 错误码行、连接级错误、回退工具缺失
_TRANSPORT_RES = [
    re.compile(r"curl: \(\d+\)"),
    re.compile(r"Connection reset"),
    re.compile(r"timed\s?out", re.I),
    re.compile(r"Could not resolve host"),
    re.compile(r"command not found"),
]


def classify_download_log(text):
    """按终态类别判定一份数据获取日志（ADR-0011 §2.1）。

    优先级：已获取 > 外部不可得 > 未完成获取。
    - 含 `Download complete` → `completed`（中间传输失败不改变终态）
    - HTTP 404/403/451 或访问墙 → `unavailable`
    - 传输层失败 / 回退工具缺失 → `not_attempted`
    - 无任何信号（含空日志）→ `not_attempted`（无法证明获取，保守记未完成）

    无重试次数/比例阈值；同类判定只按终态类别。
    """
    if _COMPLETE_RE.search(text):
        return COMPLETED
    if any(r.search(text) for r in _UNAVAILABLE_RES):
        return UNAVAILABLE
    return NOT_ATTEMPTED


def checksums_parseable(path):
    """sha256sum 输出文件可被标准工具解析：至少一行 `<64hex>  <path>`。"""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    parsed = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^[0-9a-f]{64}\s+\S+", line):
            parsed += 1
    return parsed > 0


def data_phase_evidence(data_dir):
    """收集 04_data 证据（workflow 检查 / 契约测试共用，非落盘契约）。

    返回 dict：
      logs: {日志文件名: 终态类别}（按文件名排序）
      has_checksums: 是否存在可解析的 sha256sum 输出文件
      has_data_files: raw_data/ 或 reference/ 下是否有文件
    """
    data_dir = Path(data_dir)
    logs = {}
    if data_dir.is_dir():
        for p in sorted(data_dir.glob("*.log")):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            logs[p.name] = classify_download_log(text)

    has_checksums = False
    if data_dir.is_dir():
        checksum_files = sorted(data_dir.glob("*sha256*"))
        has_checksums = bool(checksum_files) and checksums_parseable(checksum_files[0])

    has_data_files = False
    if data_dir.is_dir():
        for sub in ("raw_data", "reference"):
            d = data_dir / sub
            if d.is_dir() and any(d.iterdir()):
                has_data_files = True
                break

    return {
        "logs": logs,
        "has_checksums": has_checksums,
        "has_data_files": has_data_files,
    }


def check_data_phase(workdir="."):
    """04_data 契约检查：「存在 + 可被标准工具解析」（ADR-0011 §2 契约表）。

    判据（防 Data 幻觉 complete——返回 complete 却无任何可核验产物）：
    - `04_data/` 目录存在
    - 至少有一个标准格式证据：可解析的 sha256sum 输出文件，或一份获取日志

    返回 (ok: bool, detail: str)。不要求三件套齐备（那是 prompt 契约；
    本检查只抓「声称完成但无证据」）。
    """
    data_dir = Path(workdir) / "04_data"
    if not data_dir.is_dir():
        return False, "04_data/ 目录不存在"
    evidence = data_phase_evidence(data_dir)
    if evidence["has_checksums"]:
        return True, "sha256sum 输出文件存在且可解析"
    if evidence["logs"]:
        return True, f"有获取日志 {len(evidence['logs'])} 份（逐份终态：{', '.join(f'{k}={v}' for k, v in evidence['logs'].items())}）"
    return False, "04_data/ 无任何标准格式证据（无 sha256sum 输出、无获取日志）；阻塞也须落尝试日志"
