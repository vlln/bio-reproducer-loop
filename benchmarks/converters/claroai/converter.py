"""ClaroAI-Bench → standard benchmark entry converter (BL-011 / ADR-0010 / Interface 0002 v2).

Deterministic, replayable conversion of claroai-bench `papers/paper_XX/` into L5
**claims-based entries** that preserve the original ClaroAI-Bench task: reproduce
the paper's key quantitative results (D5), with D1–D3 data/code availability
states scored as auxiliary evidence checks.

- D5 quantitative claims are transcribed from `scores.json` D5 evidence
  (author agent's pub= / repr= comparison lines) into `oracle/claims.yaml`.
- No paper fulltext is attached (copyright decision); primary paper is an
  external DOI/PMID locator.
- The system-facing task is a natural-language statement (`metadata.task`);
  scoring-dimension codes (e.g. `d1_d3_audit`) are never emitted.
"""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ENTRY_ID_RE = re.compile(r"^bench-[0-9]{3}$")

# Author-truth-derived keys forbidden in oracle/rubric.yaml (CC-003 precise list).
RUBRIC_FORBIDDEN_AUTHOR_KEYS = {
    "author_score", "author_scores", "calibration", "ground_truth", "d1", "d2", "d3",
}

DATA_GROUND_TRUTH = {
    0: "invalid",
    1: "valid",
    2: "valid",
}
CODE_GROUND_TRUTH = {0: "missing", 1: "hollow", 2: "available"}

# Default relative tolerance for transcribed D5 numeric claims.
DEFAULT_CLAIM_TOLERANCE = {"type": "relative", "value": 0.05}

# D5 evidence lines are heterogeneous across papers. Supported explicit
# comparison formats (metric + published value + optional reproduced value):
#   1) pub=... repr=...            "Fig4A tumor: pub=599 repr=599 match=exact"
#   2) reproduced=..., published=  "Blood lead CVD HR: reproduced=1.6339, published=1.63"
#   3) single-line published value "REPRODUCED: fs_enet all-cause linear HR = 1.25 (1.09-1.43) -- EXACT MATCH"
_CLAIM_LINE_PUB_REPR_RE = re.compile(
    r"^(?P<metric>.+?):\s*pub=(?P<pub>[\d.]+)\s+repr=(?P<repr>[\d.]+)"
    r"(?:\s+match=(?P<match>[a-z]+))?(?:\s*\((?P<detail>[^)]*)\))?\s*$"
)
_CLAIM_LINE_REPROD_PUB_RE = re.compile(
    r"^(?P<metric>.+?):\s*reproduced=(?P<repr>[\d.]+)\s*,\s*published=(?P<pub>[\d.]+)"
    r"(?:\s*,\s*diff=[^,)]*)?\s*$"
)
_CLAIM_LINE_EQ_RE = re.compile(
    r"^(?:REPRODUCED|MATCH|VERIFIED)?\s*:?\s*(?P<metric>[^=]+?)\s*=\s*"
    r"(?P<pub>[\d.]+)\s*\([^)]*\)\s*--\s*(?P<match>EXACT MATCH|MATCH|CLOSE MATCH|PARTIAL)"
    r"\s*$"
)
# 4) "X vs pub Y"   "LME p=2.2e-8 vs pub p=1e-7"
_CLAIM_LINE_VS_PUB_RE = re.compile(
    r"^(?P<metric>.+?)(?::|\s+)\s*(?:p=)?(?P<repr>[\d.]+(?:e[+-]?\d+)?)"
    r"\s+vs\s+pub\s+(?:p=)?(?P<pub>[\d.]+(?:e[+-]?\d+)?)\s*$"
)
# 5) "match paper" lines carrying name=count tokens:
#    "Barcode counts match paper: multi=57,491, ATAC=167,772, RNA=78,738, spatial=21,611"
_MATCH_PAPER_TOKEN_RE = re.compile(r"(?P<metric>[A-Za-z_][A-Za-z0-9_]*)=(?P<pub>[\d,]+)")

REPRODUCTION_TARGET_VOCAB = {
    "result_verification", "derived_data_reanalysis", "raw_workflow",
    "figure_reconstruction", "reproducibility_audit",
}


class ConversionError(Exception):
    """Converter failure with a stable code (Interface 0002)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find_main_code_repo(evidence_text: str, code_refs: list[dict]) -> str | None:
    """Pick the paper's main analysis repo from evidence text (spike precision fix).

    Only URLs explicitly present in the author's justification/evidence count;
    otherwise None (per-reference state = unknown, AC-0009-B-3 — no guessing).
    """
    for ref in code_refs:
        url = ref.get("url") or ""
        if url and url in evidence_text:
            return url
    return None


def _extract_d5_claims(scores: dict) -> list[dict]:
    """Transcribe numeric D5 claims from scores.json D5 evidence.

    Each `pub=<v> repr=<v>` evidence line becomes one claim with the paper's
    published value as ground truth and a relative tolerance. Non-numeric or
    qualitative evidence lines (match_level=..., data_source=..., Root cause: ...)
    are skipped; they are recorded as calibration context, not claims.
    """
    dims = scores.get("dimensions") or {}
    d5 = dims.get("D5_results_match") or {}
    if not d5.get("applicable"):
        return []
    claims: list[dict] = []
    seen: set[str] = set()
    for line in d5.get("evidence") or []:
        stripped = line.strip()
        m = (_CLAIM_LINE_PUB_REPR_RE.match(stripped)
             or _CLAIM_LINE_REPROD_PUB_RE.match(stripped)
             or _CLAIM_LINE_EQ_RE.match(stripped)
             or _CLAIM_LINE_VS_PUB_RE.match(stripped))
        if m:
            metric = m.group("metric").strip()
            if metric in seen:
                continue
            seen.add(metric)
            pub = float(m.group("pub"))
            claims.append({
                "id": f"C{len(claims) + 1}",
                "metric": metric,
                "paper_value": pub,
                "unit": "count" if "." not in m.group("pub") else "value",
                "tolerance": dict(DEFAULT_CLAIM_TOLERANCE),
                "source": "scores.json D5 evidence",
                "author_match": (m.groupdict().get("match") or "unknown").lower(),
                "author_repr": float(m.group("repr")) if "repr" in m.groupdict() and m.group("repr") else None,
                "notes": "transcribed from scores.json D5 evidence",
            })
            continue
        # 5) name=count tokens on "match paper" lines (paper_30 barcode counts)
        if "match paper" in stripped.lower():
            for tm in _MATCH_PAPER_TOKEN_RE.finditer(stripped):
                metric = tm.group("metric").strip()
                if metric in seen:
                    continue
                seen.add(metric)
                pub = float(tm.group("pub").replace(",", ""))
                claims.append({
                    "id": f"C{len(claims) + 1}",
                    "metric": metric,
                    "paper_value": pub,
                    "unit": "count",
                    "tolerance": dict(DEFAULT_CLAIM_TOLERANCE),
                    "source": "scores.json D5 evidence",
                    "author_match": "exact",
                    "author_repr": pub,
                    "notes": "barcode count verified against paper (transcribed from D5 evidence)",
                })
    return claims


def _build_task(claims: list[dict], modality: str) -> str:
    """Natural-language, system-facing task statement (no dimension codes)."""
    if claims:
        metrics = "、".join(c["metric"] for c in claims[:5])
        more = f" 等 {len(claims)} 项" if len(claims) > 5 else ""
        return (
            f"复现该论文报告的关键定量结果（{metrics}{more}），并与论文发表的数值核对；"
            "同时核实论文引用的数据可定位、可下载，以及代码仓库是否可用。"
            "不需要复现论文的全部图表与分析。"
        )
    return (
        "核实该论文引用的数据能否定位并实际下载、代码仓库是否完整可用；"
        "复现论文报告的关键定量结果（如有）。"
    )


def _build_metadata(md: dict, entry_id: str, doi: str, pmid: str, modality: str,
                    claims: list[dict]) -> dict:
    return {
        "id": entry_id,
        "version": "2.1.0",
        "protocol_version": "2.0",
        "oracle_version": "1.1.0",
        "title": md.get("title", ""),
        "scenario": "mixed",
        "difficulty": "medium",
        "input_dir": "input/",
        "oracle_dir": "oracle/",
        "description": (
            f"ClaroAI-Bench entry (BL-011). PMID {pmid}, DOI {doi}, "
            f"modality {modality}. reproduction_target=result_verification. "
            f"Scored task: {len(claims)} quantitative claim(s) + D1-D3 evidence."
        ),
        "reproduction_target": "result_verification",
        "task": _build_task(claims, modality),
        "complexity_profile": {
            "data": {"data_size": "medium", "data_source": "public_db",
                     "data_format": "mixed", "supplementary": "complex"},
            "environment": {"tool_count": "3-5", "tool_chain": "multi_language",
                            "version_sensitivity": "moderate", "container": "custom_dockerfile"},
            "analysis": {"design": "two_group", "method_complexity": "multi_step",
                         "compute": "moderate"},
            "evaluation": {"ground_truth": "partially_known", "claim_type": "mixed",
                           "tolerance": "moderate"},
            "paper": {"paper_type": "real_published", "paper_format": "html",
                      "multi_version": "none", "missing_info": "version_gaps"},
        },
    }


def _build_bundle(entry_id: str, locator_source: str, locator_notes: str, locator_sha: str,
                  data_refs: list[dict], code_refs: list[dict]) -> dict:
    resources: list[dict] = [
        {
            "id": "paper-main",
            "role": "paper",
            "authority": "original",
            "availability": "external",
            "source": locator_source,
            "access_notes": locator_notes,
        },
        {
            "id": "paper-locator",
            "role": "metadata",
            "authority": "original",
            "availability": "bundled",
            "path": "paper/locator.md",
            "source": f"urn:benchmark:{entry_id}:paper-locator",
            "retrieved_at": "2026-08-04T00:00:00Z",
            "sha256": locator_sha,
            "media_type": "text/markdown",
            "license": "CC-BY-4.0",
        },
    ]
    for i, dr in enumerate(data_refs):
        resources.append({
            "id": f"data-ref-{i + 1}",
            "role": "data",
            "authority": "original",
            "availability": "unavailable",
            "source": dr.get("url") or f"{dr.get('repo_type')}:{dr.get('accession_id')}",
            "checked_at": "2026-08-04T00:00:00Z",
            "access_notes": (
                f"repository={dr.get('repo_type')}, primary={dr.get('is_primary')}; "
                "not bundled (system must probe from paper)"
            ),
        })
    for i, cr in enumerate(code_refs):
        if not cr.get("url"):
            continue  # no locatable URL → no bundle resource (claims keeps unknown entry)
        resources.append({
            "id": f"code-ref-{i + 1}",
            "role": "code",
            "authority": "original",
            "availability": "unavailable",
            "source": cr.get("url", ""),
            "checked_at": "2026-08-04T00:00:00Z",
            "access_notes": (
                f"language={cr.get('language')}; not bundled (system must probe from paper)"
            ),
        })
    return {
        "schema_version": "1.0",
        "entry_id": entry_id,
        "level": "L5",
        "input_root": "input",
        "primary_paper": "paper-main",
        "resources": resources,
    }


def _build_claims(entry_id: str, md: dict, ex: dict, scores: dict,
                  claims: list[dict]) -> dict:
    dims = scores["dimensions"]
    d1, d2, d3 = (dims[k] for k in
                  ("D1_data_findable", "D2_data_accessible", "D3_code_methods_available"))
    d4 = dims.get("D4_environment_reconstructable") or {}
    d5 = dims.get("D5_results_match") or {}
    data_claims = []
    for dr in ex.get("data_references", []):
        has_acc = bool(dr.get("accession_id"))
        data_claims.append({
            "accession": dr.get("accession_id"),
            "repository": dr.get("repo_type"),
            "is_primary": dr.get("is_primary"),
            # no accession → not locatable → unknown (verify skips, AC-0009-B-3)
            "ground_truth": DATA_GROUND_TRUTH.get(d1["score"], "unknown") if has_acc else "unknown",
            "downloadable": "true" if d2["score"] >= 1 else "false",
            "notes": "transcribed from scores.json evidence",
        })
    just = d3.get("justification") or ""
    ev = " ".join(d3.get("evidence") or [])
    main_repo = _find_main_code_repo(f"{just} {ev}", ex.get("code_references", []))
    code_claims = []
    for cr in ex.get("code_references", []):
        url = cr.get("url") or ""
        if main_repo and url == main_repo:
            state = CODE_GROUND_TRUTH.get(d3["score"], "unknown")
        else:
            state = "unknown"  # tool repos are not audited per-reference (AC-0009-B-3)
        code_claims.append({"url": url, "language": cr.get("language"),
                            "ground_truth": state,
                            "notes": "transcribed from scores.json evidence"})
    cal = {
        "d1": d1["score"], "d2": d2["score"], "d3": d3["score"],
        "d4": d4.get("score"), "d5": d5.get("score"),
        "confidence": {"d1": d1.get("agent_confidence"),
                       "d2": d2.get("agent_confidence"),
                       "d3": d3.get("agent_confidence")},
    }
    return {
        "id": entry_id,
        "paper_title": md.get("title", ""),
        "paper_doi": md.get("doi"),
        "pmid": md.get("pmid"),
        "reproduction_target": "result_verification",
        "task": _build_task(claims, md.get("modality", "")),
        "data_references": data_claims,
        "code_references": code_claims,
        "claims": claims,
        "calibration": cal,
    }


def _build_rubric(entry_id: str, claims: list[dict]) -> dict:
    checks: list[dict] = [
        {"id": "A1",
         "description": "数据引用定位/可获取判断与 ground truth 一致",
         "evidence": {"artifact_role": "data_manifest"},
         "comparison": {"comparator": "python_verify", "module": "verify.py",
                        "function": "check_data_references", "config": {}},
         "weight": 15},
        {"id": "A2",
         "description": "代码引用可用性判断与 ground truth 一致",
         "evidence": {"artifact_role": "provision_report"},
         "comparison": {"comparator": "python_verify", "module": "verify.py",
                        "function": "check_code_references", "config": {}},
         "weight": 15},
    ]
    if claims:
        claim_weight = 70.0 / len(claims)
        for c in claims:
            checks.append({
                "id": c["id"],
                "description": f"复现声明 {c['metric']}（论文值 {c['paper_value']:g}）",
                "evidence": {"artifact_role": "validate_report"},
                "comparison": {"comparator": "python_verify", "module": "verify.py",
                               "function": "check_claim",
                               "config": {"claim_id": c["id"]}},
                "weight": round(claim_weight, 3),
            })
    else:
        # No transcribable numeric claims: entry scores D1–D3 evidence only,
        # with the task statement reflecting that boundary.
        checks[0]["weight"] = 50
        checks[1]["weight"] = 50
    return {
        "id": entry_id,
        "benchmark_version": "2.1.0",
        "oracle_version": "1.1.0",
        "expected_verdict": "REPRODUCED",
        "verdict_match_threshold": 0.6,
        "verdict_thresholds": {"reproduced": 60, "partial": 30},
        "checks": checks,
    }


def _paper_locator(md: dict) -> tuple[str, str, str]:
    """Return (locator_source, access_notes, locator_text)."""
    doi, pmid, arxiv, pmc = md.get("doi"), md.get("pmid"), md.get("arxiv"), md.get("pmc_id")
    if doi:
        source = f"https://doi.org/{doi}"
        ids = [f"DOI: {doi}"]
    elif arxiv:
        source = f"https://arxiv.org/abs/{arxiv}"
        ids = [f"arXiv: {arxiv}"]
    elif pmid:
        source = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        ids = [f"PMID: {pmid}"]
    else:
        raise ConversionError("CONVERT_INVALID_SOURCE", "no doi/arxiv/pmid identifier")
    if pmid:
        ids.append(f"PMID: {pmid}")
    if pmc:
        ids.append(f"PMC: {pmc}")
    notes = ("paper fulltext not bundled (copyright); "
             "system must fetch at runtime (L5)")
    text = "# Paper locator\n" + "\n".join(ids) + "\n\n" + notes + "\n"
    return source, notes, text


def convert_paper(paper_dir: Path, out_entry: Path, entry_id: str) -> None:
    try:
        md = json.loads((paper_dir / "metadata.json").read_text())
        ex = json.loads((paper_dir / "extraction.json").read_text())
        sc = json.loads((paper_dir / "scores.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ConversionError("CONVERT_INVALID_SOURCE", f"{paper_dir.name}: {exc}") from exc
    try:
        locator_source, locator_notes, locator_text = _paper_locator(md)
    except ConversionError as exc:
        raise ConversionError(exc.code, f"{paper_dir.name}: {exc}") from exc
    claims = _extract_d5_claims(sc)
    locator_path = out_entry / "input" / "paper" / "locator.md"
    locator_path.parent.mkdir(parents=True, exist_ok=True)
    locator_path.write_text(locator_text)

    (out_entry / "bundle.yaml").write_text(yaml.safe_dump(
        _build_bundle(entry_id, locator_source, locator_notes, _sha256(locator_path),
                      ex.get("data_references", []), ex.get("code_references", [])),
        sort_keys=False))
    (out_entry / "metadata.yaml").write_text(yaml.safe_dump(
        _build_metadata(md, entry_id, md.get("doi") or md.get("arxiv") or "",
                        md.get("pmid") or "", md.get("modality", ""), claims),
        sort_keys=False))
    oracle = out_entry / "oracle"
    oracle.mkdir(parents=True, exist_ok=True)
    (oracle / "claims.yaml").write_text(yaml.safe_dump(
        _build_claims(entry_id, md, ex, sc, claims), sort_keys=False))
    (oracle / "rubric.yaml").write_text(yaml.safe_dump(_build_rubric(entry_id, claims),
                                                       sort_keys=False))
    (oracle / "verify.py").write_text(VERIFY_TEMPLATE)


def convert_snapshot(source_dir: Path, output_dir: Path, start_id: int = 200,
                     snapshot_ref: str | None = None) -> dict:
    """Convert all papers/paper_XX in a claroai-bench snapshot. Returns provenance dict."""
    papers_root = source_dir / "papers"
    if not papers_root.is_dir():
        raise ConversionError("CONVERT_INVALID_SOURCE", f"no papers/ dir in {source_dir}")
    paper_dirs = sorted(p for p in papers_root.iterdir() if p.is_dir())
    if not paper_dirs:
        raise ConversionError("CONVERT_INVALID_SOURCE", f"no paper dirs in {papers_root}")

    output_dir.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}
    failures: list[dict] = []
    for i, paper_dir in enumerate(paper_dirs):
        entry_id = f"bench-{start_id + i:03d}"
        out_entry = output_dir / entry_id
        if out_entry.exists():
            raise ConversionError("CONVERT_ID_CONFLICT", f"{entry_id} already exists")
        try:
            convert_paper(paper_dir, out_entry, entry_id)
            mapping[paper_dir.name] = entry_id
        except ConversionError as exc:
            failures.append({"paper": paper_dir.name, "entry_id": entry_id,
                             "reason": str(exc)})

    provenance = {
        "converter": "claroai2bench@0.2.0",
        "snapshot_ref": snapshot_ref or _snapshot_fingerprint(source_dir),
        "converted_at": _now(),
        "mapping": mapping,
        "failures": failures,
        "schema": "claroai-converter-provenance/v2",
    }
    (output_dir / "claroai-converter-provenance.json").write_text(
        json.dumps(provenance, indent=2))
    status = "CONVERT_OK" if not failures else "CONVERT_PARTIAL"
    return {"status": status, "mapping": mapping, "failures": failures,
            "provenance": provenance}


def _snapshot_fingerprint(source_dir: Path) -> str:
    try:
        import subprocess
        out = subprocess.run(["git", "-C", str(source_dir), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        if out.returncode == 0:
            return f"git:{out.stdout.strip()}"
    except Exception:
        pass
    return f"dir:{source_dir}"


VERIFY_TEMPLATE = '''"""Claims-based oracle verifier (generated by claroai2bench v0.2.0).

Checks D5 quantitative claims (tolerance-based numeric comparison against the
paper's published values) plus D1-D3 data/code availability evidence.
Signature contract: function(artifact_path, config) -> {"passed": bool, "actual": ..., "note": str}
"""
from pathlib import Path
import json
import re
import yaml

CLAIMS = yaml.safe_load((Path(__file__).parent / "claims.yaml").read_text())


_COMPLETED = {"COMPLETED", "PARTIAL", "IN_PROGRESS", "AVAILABLE", "就绪", "已下载"}


_SUFFIXES = ("原始数据", "数据", "文件", "files", "data", "mirror", "仓库", "repository", "原始", "官方")


def _normalize(name):
    """Normalize for fuzzy matching: unify dashes, drop generic suffix words."""
    s = str(name).lower().replace("\\u2013", "-").replace("\\u2014", "-")
    s = re.sub(r"[^0-9a-z]+", "", s)
    for suf in _SUFFIXES:
        if s.endswith(suf) and len(s) > len(suf) + 2:
            s = s[: -len(suf)]
    return s


def _keys_match(claim_acc, manifest_keys):
    """Match a claim accession against manifest keys (exact → token-overlap on original words)."""
    norm = _normalize(claim_acc)
    norm_keys = {_normalize(k): k for k in manifest_keys}
    if norm in norm_keys:
        return True, norm_keys[norm]
    claim_tokens = [t.lower() for t in re.split(r"[^a-z0-9]+", str(claim_acc), flags=re.I)
                    if len(t) >= 3]
    if not claim_tokens:
        return False, None
    for nkey, orig in norm_keys.items():
        hits = sum(1 for t in claim_tokens if t in nkey)
        if hits >= max(2, len(claim_tokens) // 2):
            return True, orig
    return False, None


def _parse_data_manifest(path):
    text = Path(path).read_text()
    state = {}
    for m in re.finditer(r"-\\s*(.+?)\\s*\\([^)]*\\):\\s*downloadable=(\\w+)", text):
        state[_normalize(m.group(1))] = m.group(2) == "true"
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        for col in cols:
            m = re.search(r"github\\.com/([\\w.-]+/[\\w.-]+)", col, re.I)
            if m:
                state.setdefault(_normalize(m.group(1)), True)
        if len(cols) < 4 or cols[0].lower() in ("source", "srr 编号", "property", "sample id", "属性"):
            continue
        row_text = " ".join(cols)
        acc = _first_accession(row_text)
        if acc is None:
            source = cols[0]
            acc = _normalize(source.split("(")[0].strip())
        if acc is None or len(str(acc)) < 3:
            continue
        rest = row_text
        if any(k in rest for k in ("COMPLETED", "PARTIAL", "IN_PROGRESS", "AVAILABLE", "就绪",
                                    "已下载", "已获取", "已包含", "已集成", "硬编码", "已克隆", "成功",
                                    "下载中", "是")):
            state[acc] = True
        elif "OUT_OF_SCOPE" in rest or "out-of-scope" in rest.lower():
            state[acc] = None
        elif any(k in rest for k in ("NOT_AVAILABLE", "BLOCKED", "MISSING",
                                     "未公开", "无法访问", "不可", "未获取", "否")):
            state[acc] = False
    return state


def _first_accession(text):
    m = re.search(r"(GSE\\d+|PRJNA\\d+|SRR\\d+|GSM\\d+|SRA:\\S+)", text)
    return m.group(1) if m else None


def _parse_provision_report(path):
    text = Path(path).read_text()
    state = {}
    for m in re.finditer(r"-\\s*(\\S+)\\s*:\\s*(available|hollow|missing)", text):
        state[m.group(1)] = m.group(2)
    manifest = Path(path).parent / "data_manifest.md"
    if manifest.is_file():
        for line in manifest.read_text().splitlines():
            if "GitHub" in line and line.strip().startswith("|"):
                cols = [c.strip() for c in line.strip().strip("|").split("|")]
                url = _first_url(" ".join(cols))
                if url:
                    notes = " ".join(cols)
                    if any(k in notes for k in ("无", "仅含", "没有", "empty", "no source")):
                        state[url] = "hollow"
                    elif "COMPLETED" in notes:
                        state[url] = "available"
                    else:
                        state[url] = "missing"
    return state


def _first_url(text):
    m = re.search(r"https?://\\S+", text)
    return m.group(0).rstrip("|,.;") if m else None


def check_data_references(artifact, config):
    claims = [c for c in CLAIMS["data_references"]
              if c.get("accession") and len(str(c["accession"])) >= 3
              and c.get("ground_truth") != "unknown"]
    system = _parse_data_manifest(artifact)
    mismatches = []
    for c in claims:
        acc = c["accession"]
        matched, key = _keys_match(acc, set(system))
        if not matched:
            mismatches.append(f"{acc}: no system judgment")
            continue
        if system[key] is None:
            continue
        expected = c["downloadable"] == "true"
        if system[key] != expected:
            mismatches.append(f"{acc}: system={system[key]} expected={expected}")
    return {"passed": not mismatches, "actual": system,
            "note": "; ".join(mismatches) or "all data judgments match ground truth"}


def check_code_references(artifact, config):
    claims = [c for c in CLAIMS["code_references"] if c["ground_truth"] != "unknown"]
    system = _parse_provision_report(artifact)
    manifest = Path(artifact).parent / "data_manifest.md"
    if manifest.is_file() and not system:
        for line in manifest.read_text().splitlines():
            if "GitHub" in line and line.strip().startswith("|"):
                notes = " ".join(c.strip() for c in line.strip().strip("|").split("|"))
                if any(k in notes for k in ("无", "仅含", "没有", "no source", "empty")):
                    for c in claims:
                        if c["url"] and (c["url"].split("/")[-1] in notes or "GitHub" in notes):
                            system[c["url"]] = "hollow"
                break
    mismatches = []
    for c in claims:
        url = c["url"]
        if url not in system:
            mismatches.append(f"{url}: no system judgment")
            continue
        if system[url] != c["ground_truth"]:
            mismatches.append(f"{url}: system={system[url]} expected={c['ground_truth']}")
    return {"passed": not mismatches, "actual": system,
            "note": "; ".join(mismatches) or "all code judgments match ground truth"}


# ── D5 quantitative claim checks ─────────────────────────────────────────────


def _parse_claims_evidence(path):
    """Parse a claims evidence artifact into {metric_norm: {"expected": v, "actual": v}}.

    Accepts two formats:
    1. JSON {"claims": [{"id": "...", "metric": "...", "expected": v, "actual": v}, ...]}
       (structured submission artifact, role=validate_report).
    2. A validate report markdown table with Expected/Actual columns
       (bio-reproducer 06_validate/report.md format).
    """
    p = Path(path)
    text = p.read_text()
    rows = {}
    stripped = text.lstrip()
    if stripped.startswith("{"):
        try:
            data = json.loads(text)
            for c in data.get("claims", []):
                if "metric" in c and ("actual" in c or "value" in c):
                    rows[_normalize(c["metric"])] = {
                        "expected": c.get("expected"),
                        "actual": c.get("actual", c.get("value")),
                        "metric": c["metric"],
                    }
            return rows
        except json.JSONDecodeError:
            pass
    lines = text.splitlines()
    # locate header row with Expected/Actual columns
    expected_idx = actual_idx = metric_idx = None
    data_start = 0
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        if any(h in cols for h in ("expected", "actual", "论文值", "复现值", "值")):
            expected_idx = next((j for j, c in enumerate(cols)
                                 if c in ("expected", "论文值") or c.startswith("expected")), None)
            actual_idx = next((j for j, c in enumerate(cols)
                               if c in ("actual", "复现值", "系统值") or c.startswith("actual")), None)
            metric_idx = next((j for j, c in enumerate(cols)
                               if c in ("metric", "指标", "声明")), None)
            data_start = i + 1
            break
    if expected_idx is None or actual_idx is None:
        return rows
    for line in lines[data_start:]:
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) <= max(expected_idx, actual_idx):
            continue
        if cols[0].lower() in ("check id", "check", "----"):
            continue
        metric = cols[metric_idx] if metric_idx is not None and metric_idx < len(cols) else (
            cols[1] if len(cols) >= 4 else cols[0])
        exp = _first_number(cols[expected_idx])
        act = _first_number(cols[actual_idx])
        if exp is None or act is None:
            continue
        rows[_normalize(metric)] = {"expected": float(exp), "actual": float(act),
                                    "metric": metric}
    return rows


def _first_number(text):
    m = re.search(r"-?\\d+(?:\\.\\d+)?", str(text))
    return float(m.group(0)) if m else None


def _match_row(claim, rows):
    """Find the evidence row for a claim: exact normalized metric, then token overlap."""
    norm = _normalize(claim["metric"])
    if norm in rows:
        return rows[norm]
    tokens = [t for t in re.split(r"[^a-z0-9]+", claim["metric"].lower()) if len(t) >= 3]
    best, best_hits = None, 0
    for nkey, row in rows.items():
        hits = sum(1 for t in tokens if t in nkey)
        if hits > best_hits:
            best, best_hits = row, hits
    if best is not None and best_hits >= max(1, len(tokens) // 2):
        return best
    return None


def check_claim(artifact, config):
    claim_id = config.get("claim_id")
    claim = next((c for c in CLAIMS.get("claims", []) if c["id"] == claim_id), None)
    if claim is None:
        return {"passed": False, "actual": None, "note": f"claim {claim_id} not in oracle"}
    rows = _parse_claims_evidence(artifact)
    row = _match_row(claim, rows)
    if row is None:
        return {"passed": False, "actual": None,
                "note": f"{claim['metric']}: no reproduced value in evidence artifact"}
    tol = claim.get("tolerance") or {"type": "relative", "value": 0.05}
    paper = float(claim["paper_value"])
    actual = float(row["actual"])
    # Threshold claims: claim.comparison.op in {"gte", "lte"} — compare against
    # the paper's stated bound (e.g. paper claim "AUROC > 0.95" → op=gte, value=0.95).
    op = (claim.get("comparison") or {}).get("op")
    if op == "gte":
        ok = actual >= paper
    elif op == "lte":
        ok = actual <= paper
    elif paper == 0:
        ok = abs(actual) <= (tol.get("value", 0.05) if tol.get("type") == "absolute" else 0.05)
    elif tol.get("type") == "absolute":
        ok = abs(actual - paper) <= float(tol.get("value", 0.05))
    else:
        ok = abs(actual - paper) / abs(paper) <= float(tol.get("value", 0.05))
    criterion = (f"within tol={tol.get('value')}" if not op else f"{op} {paper:g}")
    return {"passed": ok, "actual": actual,
            "note": (f"{claim['metric']}: paper={paper:g} system={actual:g} "
                     f"{criterion} OK" if ok else
                     f"{claim['metric']}: paper={paper:g} system={actual:g} "
                     f"{criterion} VIOLATED")}
'''
