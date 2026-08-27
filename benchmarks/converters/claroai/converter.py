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
    r"^(?P<metric>.+?):\s*pub=(?P<pub>[\d.]+)%?\s+repr=(?P<repr>[\d.]+)%?"
    r"(?:\s+match=(?P<match>[a-z]+))?(?:\s*\((?P<detail>[^)]*)\))?\s*$"
)
_CLAIM_LINE_REPROD_PUB_RE = re.compile(
    r"^(?P<metric>.+?):\s*reproduced=(?P<repr>[\d.]+)%?\s*,\s*published=(?P<pub>[\d.]+)%?"
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
# 6) "X: PR=1.09 [1.05-1.13] vs published 1.08"（bench-206 风格）
_CLAIM_LINE_VS_PUBLISHED_RE = re.compile(
    r"^(?P<metric>.+?)(?::|\s+)(?:[A-Za-z]+=\s*)?(?P<repr>[\d.]+)%?\s*\[[^]]*\]"
    r"\s+vs\s+published\s+(?P<pub>[\d.]+)%?\s*(?:\[[^]]*\])?"
    r"\s*(?:\((?P<detail>[^)]*)\))?$"
)
# 7) "nuclei: pub=2275105 verified=2275105"（bench-210 风格）
_CLAIM_LINE_PUB_VERIFIED_RE = re.compile(
    r"^(?P<metric>.+?):\s*pub=(?P<pub>[\d,]+)(?:%?)\s+verified=(?P<repr>[\d,]+)%?\s*$"
)
# 噪声行：agent 运行元数据，非论文声明
_CLAIM_NOISE_TOKENS = ("outputs=", "exit_code=")
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


def _slugify(metric: str) -> str:
    """metric → 公开 target_id（小写连字符 slug）。

    target_id 是公开问题清单（input/questions.yaml）与系统 answers.csv 的键
    （ADR-0011 §4.1）；claim id（C1/C2/…）是 oracle 私有，系统不可能知道。
    """
    slug = re.sub(r"[^a-z0-9]+", "-", str(metric).lower()).strip("-")
    return slug or "claim"


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
        if any(tok in stripped.lower() for tok in _CLAIM_NOISE_TOKENS):
            continue
        m = (_CLAIM_LINE_PUB_REPR_RE.match(stripped)
             or _CLAIM_LINE_REPROD_PUB_RE.match(stripped)
             or _CLAIM_LINE_EQ_RE.match(stripped)
             or _CLAIM_LINE_VS_PUB_RE.match(stripped)
             or _CLAIM_LINE_VS_PUBLISHED_RE.match(stripped)
             or _CLAIM_LINE_PUB_VERIFIED_RE.match(stripped))
        if m:
            metric = m.group("metric").strip()
            if metric in seen:
                continue
            seen.add(metric)
            pub = float(m.group("pub"))
            claims.append({
                "id": f"C{len(claims) + 1}",
                "target_id": _slugify(metric),
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
                    "target_id": _slugify(metric),
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
                  data_refs: list[dict], code_refs: list[dict], questions_sha: str) -> dict:
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
        {
            "id": "questions",
            "role": "questions",
            "authority": "benchmark",
            "availability": "bundled",
            "path": "questions.yaml",
            "source": f"urn:benchmark:{entry_id}:questions",
            "sha256": questions_sha,
            "media_type": "text/yaml",
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


def _build_questions(claims: list[dict]) -> dict:
    """公开问题清单（ADR-0011 §4.1）：target_id + 一句话问题 + 单位，**无期望值**。

    系统按 target_id 在 answers.csv 中填复现值；oracle 判分 = 比对 answers 的
    value 与私有期望值并交叉核对 source_file。把「自行判断该报告哪些数值」从
    测量中移除的代价在论文 limitation 声明。
    """
    return {
        "schema": "questions/v1",
        "questions": [
            {
                "target_id": c["target_id"],
                "question": f"复现论文报告的 {c['metric']} 数值",
                "unit": c.get("unit", "value"),
            }
            for c in claims
        ],
    }


def _build_rubric(entry_id: str, claims: list[dict]) -> dict:
    checks: list[dict] = [
        {"id": "A1",
         "description": "数据引用定位/可获取判断与 ground truth 一致（证据：04_data 标准格式）",
         "evidence": {"artifact_role": "data_evidence"},
         "comparison": {"comparator": "python_verify", "module": "verify.py",
                        "function": "check_data_references", "config": {}},
         "weight": 15},
        {"id": "A2",
         "description": "代码引用可用性判断与 ground truth 一致（证据：03_provision digests）",
         "evidence": {"artifact_role": "environment"},
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
                "evidence": {"artifact_role": "answers"},
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
    # 公开问题清单（ADR-0011 §4.1）：系统按 target_id 填 answers；无期望值
    (out_entry / "input" / "questions.yaml").write_text(yaml.safe_dump(
        _build_questions(claims), sort_keys=False))

    (out_entry / "bundle.yaml").write_text(yaml.safe_dump(
        _build_bundle(entry_id, locator_source, locator_notes, _sha256(locator_path),
                      ex.get("data_references", []), ex.get("code_references", []),
                      _sha256(out_entry / "input" / "questions.yaml")),
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


VERIFY_TEMPLATE = r'''"""Claims-based oracle verifier (generated by claroai2bench v0.2.1).

证据面切换（ADR-0011 §4，单元 04）：外部评分只读真实产物，不读任何系统散文——
- check_claim: 05_run/answers.csv（target_id,value,unit,source_file）+
  强制交叉核对（value 须能在 source_file 中定位，容差由书写精度导出，无魔数）；
  交叉核对失败 → no_evidence（不计分，非判错，FC-005）
- check_data_references: 04_data 标准格式（sha256sums 输出 + 获取日志终态，§2.1）
- check_code_references: 03_provision digests（docker images --digests 输出）
Signature contract: function(artifact_path, config) -> {"passed": bool, ...}
"""
import csv
import re
from decimal import Decimal
from pathlib import Path

import yaml

CLAIMS = yaml.safe_load((Path(__file__).parent / "claims.yaml").read_text())


# ── answers 交叉核对（FC-005：容差由书写精度导出，无魔数）──────────────
_NUM = re.compile(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?")


def _decimals(s):
    try:
        return max(0, -Decimal(s).as_tuple().exponent)
    except Exception:
        return 0


def _numbers_in(path):
    out = []
    for tok in _NUM.findall(Path(path).read_text(errors="replace")):
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def _locate(value, source):
    """value 须能在 source 中定位（正确舍入），否则该 claim 无证据。"""
    if not Path(source).is_file():
        return False, f"source_file 不存在: {Path(source).name}"
    try:
        a = float(value)
    except ValueError:
        return False, "value 非数值"
    tol = 0.5 * 10 ** (-_decimals(value))
    for b in _numbers_in(source):
        if abs(a - b) <= tol:
            return True, f"命中 {b}（容差 {tol:g}，由书写精度导出）"
    return False, f"在 {Path(source).name} 中找不到 {value}（容差 {tol:g}）"


# ── 获取日志终态（ADR-0011 §2.1：按终态信号判定，无阈值）──────────────
def _log_terminal(text):
    if "Download complete" in text:
        return "completed"
    if re.search(
        r"HTTP/[0-9.]+ 40[1345]\b|404 Not Found|403 Forbidden|requires\s+registration|access\s+denied",
        text, re.I,
    ):
        return "unavailable"
    return "not_attempted"


# ── D5 数值 claim（证据 = 05_run/answers.csv）────────────────────────
def check_claim(artifact, config):
    claim_id = config.get("claim_id")
    claim = next((c for c in CLAIMS.get("claims", []) if c["id"] == claim_id), None)
    if claim is None:
        return {"passed": False, "actual": None, "note": f"claim {claim_id} not in oracle"}
    target_id = claim.get("target_id")
    if not target_id:
        return {"passed": False, "actual": None,
                "note": f"claim {claim_id} 无 target_id（oracle 配置缺失）"}
    answers_path = Path(artifact)
    if not answers_path.is_file():
        return {"passed": False, "no_evidence": True, "actual": None,
                "note": f"{claim['metric']}: answers.csv 不存在（NO-EVIDENCE，不计分）"}
    row = None
    with answers_path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("target_id") == target_id:
                row = r
                break
    if row is None:
        return {"passed": False, "no_evidence": True, "actual": None,
                "note": f"{claim['metric']}: answers 无 target_id={target_id}（NO-EVIDENCE，不计分）"}
    # 强制交叉核对（FC-005）
    ok, note = _locate(row.get("value"), answers_path.parent / row.get("source_file", ""))
    if not ok:
        return {"passed": False, "no_evidence": True, "actual": row.get("value"),
                "note": f"{claim['metric']}: 交叉核对失败 — {note}（NO-EVIDENCE，不计分）"}
    # 与私有期望值比对（容差来自 claims.yaml，评分策略归 oracle）
    tol = claim.get("tolerance") or {"type": "relative", "value": 0.05}
    paper = float(claim["paper_value"])
    actual = float(row["value"])
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
    criterion = f"within tol={tol.get('value')}" if not op else f"{op} {paper:g}"
    return {"passed": ok, "actual": actual,
            "note": (f"{claim['metric']}: paper={paper:g} system={actual:g} "
                     f"{criterion} OK（交叉核对通过）" if ok else
                     f"{claim['metric']}: paper={paper:g} system={actual:g} "
                     f"{criterion} VIOLATED")}


# ── A1 数据引用（证据 = 04_data 标准格式：sha256sums 输出 + 获取日志）──
def check_data_references(artifact, config):
    """从 04_data 推导系统判断（事实 → 判断的薄映射），与 ground truth 比对。

    artifact 是 04_data 内的标准格式文件（如 sha256sums.txt），其 parent
    即 04_data 目录；日志与校验文件同目录。
    """
    # artifact 是 04_data 内的标准格式文件（evaluator 契约保证是文件），
    # parent 即 04_data 目录（sha256sums 与获取日志同目录）
    data_dir = Path(artifact).parent
    terminal = {}
    if data_dir.is_dir():
        for p in sorted(data_dir.glob("*.log")):
            try:
                terminal[p.stem.lower()] = _log_terminal(p.read_text(errors="replace"))
            except OSError:
                continue
    passed_all, actual = True, []
    for c in CLAIMS.get("data_references", []):
        acc = str(c.get("accession") or "").lower()
        gt = str(c.get("downloadable")).lower()
        if not acc or not re.match(r"(gse|gsm|prjna|sra|srr|ena)", acc):
            continue  # 无 accession 不可定位（AC-0009-B-3）
        state = next((st for stem, st in terminal.items() if acc in stem), None)
        if gt == "true":
            ok = state == "completed"
            note = "可下载数据已获取" if ok else ("系统未完成获取" if state else "系统无尝试日志")
        else:
            ok = state == "unavailable"
            note = "正确判不可获取" if ok else ("系统未判不可得" if state else "系统无尝试日志")
        actual.append({"accession": acc, "system": state, "ground_truth": gt, "note": note})
        passed_all = passed_all and ok
    if not actual:
        return {"passed": False, "no_evidence": True, "actual": None,
                "note": "无 accession 可定位（AC-0009-B-3，NO-EVIDENCE）"}
    n_ok = sum(1 for a in actual if a["system"] is not None)
    return {"passed": passed_all, "actual": actual,
            "note": f"数据引用推导 {n_ok}/{len(actual)} 有状态（0 无尝试日志）"}


# ── A2 代码引用（证据 = 03_provision digests）────────────────────────
def check_code_references(artifact, config):
    """从 03_provision digests 推导系统判断（digests 非空 = 环境构建有产出）。"""
    digests = Path(artifact)
    if not digests.is_file():
        return {"passed": False, "no_evidence": True, "actual": None,
                "note": "03_provision digests 不存在（NO-EVIDENCE，不计分）"}
    text = digests.read_text(errors="replace")
    has_digest = bool(re.search(r"sha256:[0-9a-f]{64}", text, re.I)) or bool(
        re.search(r"^[0-9a-f]{64}\s+\S+", text, re.M)
    )
    passed_all, actual = True, []
    for c in CLAIMS.get("code_references", []):
        if c.get("ground_truth") != "available":
            continue  # unknown/missing 不审计（AC-0009-B-3）
        ok = has_digest
        actual.append({"url": c.get("url"), "ground_truth": "available",
                       "system": "provisioned" if ok else "no-digest",
                       "note": "环境已构建" if ok else "无 digest 证据"})
        passed_all = passed_all and ok
    if not actual:
        return {"passed": True, "actual": None, "note": "无 available 代码引用可审计"}
    return {"passed": passed_all, "actual": actual,
            "note": f"代码可用性推导（digests {'有' if has_digest else '无'}）"}
'''
