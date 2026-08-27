"""Phase 产物契约检查（ADR-0011 §2/§5，单元 02/03 范围：Data + Run phase）。

事实以标准格式文件持久化；本模块只做「存在 + 可被标准工具解析」的检查，
不校验自定义字段、不含任何评分阈值（FC-001/FC-002 的检出手段）。

终态类别判定（ADR-0011 §2.1）：区分「未完成获取」「外部不可得」「已获取」
依据**终态信号**而非尝试次数——传输层失败（curl: (35)/(56)、超时、连接重置）
属未完成获取；HTTP 404/403/451 与注册墙/DUA 属外部不可得；`Download complete`
+ 文件存在属已获取。系统内不写死任何重试次数/比例常量。
"""
import csv
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


# ── Run phase（05_run）契约 ──────────────────────────────────────────
# answers 表头白名单（FC-003：只记标识符与数值，无状态词/判断/理由）
ANSWERS_COLUMNS = ["target_id", "value", "unit", "source_file"]


def answers_parseable(path):
    """answers.csv 表头必须精确等于 target_id/value/unit/source_file（FC-003 白名单）。

    含额外列（状态词/判断/理由）或缺列都算违规；列顺序不限。
    """
    try:
        with open(path, newline="", encoding="utf-8") as f:
            header = next(csv.reader(f))
    except (OSError, StopIteration, csv.Error):
        return False
    cols = {h.strip().lower() for h in header}
    return cols == set(ANSWERS_COLUMNS)


def run_phase_evidence(run_dir):
    """收集 05_run 证据（workflow 检查 / 契约测试共用，非落盘契约）。

    返回 dict：
      results_csv: results/ 下非空 CSV/TSV 文件名列表（可被标准 csv 解析的前提）
      has_answers: answers.csv 存在且表头合规
    """
    run_dir = Path(run_dir)
    results_csv = []
    if run_dir.is_dir():
        results_dir = run_dir / "results"
        if results_dir.is_dir():
            for p in sorted(results_dir.iterdir()):
                if p.is_file() and p.suffix.lower() in (".csv", ".tsv") and p.stat().st_size > 0:
                    results_csv.append(p.name)
    has_answers = (run_dir / "answers.csv").is_file() and answers_parseable(run_dir / "answers.csv")
    return {"results_csv": results_csv, "has_answers": has_answers}


def check_run_phase(workdir="."):
    """05_run 契约检查：「存在 + 可被标准工具解析」（ADR-0011 §2 契约表）。

    判据（防 Run 幻觉 complete——返回 complete 却无结果文件）：
    - `05_run/` 目录存在
    - `results/` 至少一个非空 CSV/TSV（结果本体，可被标准 csv 解析）
    - `answers.csv` 存在且表头合规（target_id,value,unit,source_file）

    返回 (ok: bool, detail: str)。answers 的**值定位交叉核对**（FC-005）由
    单元 04 的 evaluator 实现，本检查只验格式。
    """
    run_dir = Path(workdir) / "05_run"
    if not run_dir.is_dir():
        return False, "05_run/ 目录不存在"
    evidence = run_phase_evidence(run_dir)
    if not evidence["results_csv"]:
        return False, "05_run/results/ 无任何非空 CSV/TSV 结果文件"
    if not evidence["has_answers"]:
        return False, "05_run/answers.csv 缺失或表头不合规（须含 target_id,value,unit,source_file）"
    return True, f"results 有 {len(evidence['results_csv'])} 个 CSV/TSV，answers 表头合规"


# ── Provision phase（03_provision）契约 ──────────────────────────────
def check_provision_phase(workdir="."):
    """03_provision 契约检查：「存在 + 可被标准工具解析」（digests 输出）。

    判据（防 Provision 幻觉 complete）：`03_provision/digests.txt` 存在且
    含可解析的 digest 行（`sha256:...` 或 64 hex 摘要）。docker images
    --digests 的输出即标准格式，任何人可重算核对。
    """
    digests = Path(workdir) / "03_provision" / "digests.txt"
    if not digests.is_file():
        return False, "03_provision/digests.txt 不存在（docker images --digests 原始输出）"
    text = digests.read_text(encoding="utf-8", errors="replace")
    has_digest = bool(re.search(r"sha256:[0-9a-f]{64}", text, re.I)) or bool(
        re.search(r"^[0-9a-f]{64}\s+\S+", text, re.M)
    )
    if not has_digest:
        return False, "03_provision/digests.txt 无可解析的 digest 行"
    return True, "digests.txt 存在且含 digest 行"


# ── routing.jsonl 键名白名单（FC-003）──────────────────────────────────
ROUTING_KEYS = {"ts", "target", "decision", "route_to", "reason"}


def routing_events_ok(events):
    """routing.jsonl 事件键名白名单（FC-003）：只允许 ts/target/decision/
    route_to/reason，不得含额外字段（状态词/评分/阈值）；缺键也算违规。
    """
    for ev in events:
        if not isinstance(ev, dict):
            return False
        if set(ev) != ROUTING_KEYS:
            return False
    return True
