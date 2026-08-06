"""ClaroAI-Bench → standard benchmark entry converter (BL-011 / ADR-0010 / Interface 0002).

Deterministic, replayable conversion of claroai-bench `papers/paper_XX/` into L5
audit-mode entries (scored_scope=d1_d3_audit). No paper fulltext is attached
(copyright decision); primary paper is an external DOI/PMID locator.
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


def _build_metadata(md: dict, entry_id: str, doi: str, pmid: str, modality: str) -> dict:
    return {
        "id": entry_id,
        "version": "2.0.0",
        "protocol_version": "2.0",
        "oracle_version": "1.0.0",
        "title": md.get("title", ""),
        "scenario": "mixed",
        "difficulty": "medium",
        "input_dir": "input/",
        "oracle_dir": "oracle/",
        "description": (
            f"ClaroAI-Bench audit-mode entry (BL-011). PMID {pmid}, DOI {doi}, "
            f"modality {modality}. scored_scope=d1_d3_audit."
        ),
        "scored_scope": "d1_d3_audit",
        "complexity_profile": {
            "data": {"data_size": "medium", "data_source": "public_db",
                     "data_format": "mixed", "supplementary": "complex"},
            "environment": {"tool_count": "3-5", "tool_chain": "multi_language",
                            "version_sensitivity": "moderate", "container": "custom_dockerfile"},
            "analysis": {"design": "two_group", "method_complexity": "multi_step",
                         "compute": "moderate"},
            "evaluation": {"ground_truth": "partially_known", "claim_type": "qualitative",
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
                "not bundled (audit-mode entry, system must probe from paper)"
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
                f"language={cr.get('language')}; not bundled (audit-mode entry, "
                "system must probe from paper)"
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


def _build_claims(entry_id: str, md: dict, ex: dict, scores: dict) -> dict:
    dims = scores["dimensions"]
    d1, d2, d3 = (dims[k] for k in
                  ("D1_data_findable", "D2_data_accessible", "D3_code_methods_available"))
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
    return {
        "id": entry_id,
        "paper_title": md.get("title", ""),
        "paper_doi": md.get("doi"),
        "pmid": md.get("pmid"),
        "audit_scope": "d1_d3_audit",
        "data_references": data_claims,
        "code_references": code_claims,
        "calibration": {
            "d1": d1["score"], "d2": d2["score"], "d3": d3["score"],
            "confidence": {"d1": d1.get("agent_confidence"),
                           "d2": d2.get("agent_confidence"),
                           "d3": d3.get("agent_confidence")},
        },
    }


def _build_rubric(entry_id: str) -> dict:
    return {
        "id": entry_id,
        "benchmark_version": "2.0.0",
        "oracle_version": "1.0.0",
        "expected_verdict": "REPRODUCED",
        "verdict_match_threshold": 0.6,
        "verdict_thresholds": {"reproduced": 60, "partial": 30},
        "checks": [
            {"id": "A1",
             "description": "数据引用定位/可获取判断与 ground truth 一致",
             "evidence": {"artifact_role": "data_manifest"},
             "comparison": {"comparator": "python_verify", "module": "verify.py",
                            "function": "check_data_references", "config": {}},
             "weight": 50},
            {"id": "A2",
             "description": "代码引用可用性判断与 ground truth 一致",
             "evidence": {"artifact_role": "provision_report"},
             "comparison": {"comparator": "python_verify", "module": "verify.py",
                            "function": "check_code_references", "config": {}},
             "weight": 50},
        ],
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
    locator_path = out_entry / "input" / "paper" / "locator.md"
    locator_path.parent.mkdir(parents=True, exist_ok=True)
    locator_path.write_text(locator_text)

    (out_entry / "bundle.yaml").write_text(yaml.safe_dump(
        _build_bundle(entry_id, locator_source, locator_notes, _sha256(locator_path),
                      ex.get("data_references", []), ex.get("code_references", [])),
        sort_keys=False))
    (out_entry / "metadata.yaml").write_text(yaml.safe_dump(
        _build_metadata(md, entry_id, md.get("doi") or md.get("arxiv") or "",
                        md.get("pmid") or "", md.get("modality", "")), sort_keys=False))
    oracle = out_entry / "oracle"
    oracle.mkdir(parents=True, exist_ok=True)
    (oracle / "claims.yaml").write_text(yaml.safe_dump(_build_claims(entry_id, md, ex, sc),
                                                       sort_keys=False))
    (oracle / "rubric.yaml").write_text(yaml.safe_dump(_build_rubric(entry_id), sort_keys=False))
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
        "converter": "claroai2bench@0.1.0",
        "snapshot_ref": snapshot_ref or _snapshot_fingerprint(source_dir),
        "converted_at": _now(),
        "mapping": mapping,
        "failures": failures,
        "schema": "claroai-converter-provenance/v1",
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


VERIFY_TEMPLATE = '''"""Audit-mode oracle verifier (generated by claroai2bench).

Compares system audit evidence against claims.yaml ground truth.
Signature contract: function(artifact_path, config) -> {"passed": bool, "actual": ..., "note": str}
"""
from pathlib import Path
import re
import yaml

CLAIMS = yaml.safe_load((Path(__file__).parent / "claims.yaml").read_text())


_COMPLETED = {"COMPLETED", "PARTIAL", "IN_PROGRESS", "AVAILABLE", "就绪", "已下载"}


_SUFFIXES = ("原始数据", "数据", "文件", "files", "data", "mirror", "仓库", "repository", "原始", "官方")


def _normalize(name):
    """Normalize for fuzzy matching: unify dashes, drop generic suffix words."""
    s = str(name).lower().replace("\u2013", "-").replace("\u2014", "-")
    s = re.sub(r"[^0-9a-z]+", "", s)
    for suf in _SUFFIXES:
        if s.endswith(suf) and len(s) > len(suf) + 2:
            s = s[: -len(suf)]
    return s


def _keys_match(claim_acc, manifest_keys):
    """Match a claim accession against manifest keys (exact → token-overlap on original words)."""
    norm = _normalize(claim_acc)
    if norm in manifest_keys:
        return True, norm
    # 基于原始名称分词（空格/连字符/斜杠分隔），再检查每个词是否出现在规范化 key 的子串中
    claim_tokens = [t.lower() for t in re.split(r"[^a-z0-9]+", str(claim_acc), flags=re.I)
                    if len(t) >= 3]
    if not claim_tokens:
        return False, None
    for key in manifest_keys:
        hits = sum(1 for t in claim_tokens if t in key)
        if hits >= max(2, len(claim_tokens) // 2):
            return True, key
    return False, None


def _parse_data_manifest(path):
    text = Path(path).read_text()
    state = {}
    # 格式 1（行式）：- ACCESSION (REPO): downloadable=true/false
    for m in re.finditer(r"-\\s*(.+?)\\s*\\([^)]*\\):\\s*downloadable=(\\w+)", text):
        state[_normalize(m.group(1))] = m.group(2) == "true"
    # 格式 2（Markdown 表格）：| Source | ... | Status/Obtained/Notes |  —— 提取 source 名 + 状态
    # 兼容有 Status 列（bench-200 格式）与无 Status 列（bench-220 格式，状态在 Obtained/Notes）
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        # URL 行（数据来源/属性-值表）也纳入匹配：key=repo owner/name（视为数据可用）
        for col in cols:
            m = re.search(r"github\.com/([\\w.-]+/[\\w.-]+)", col, re.I)
            if m:
                state.setdefault(_normalize(m.group(1)), True)
        if len(cols) < 4 or cols[0].lower() in ("source", "srr 编号", "property", "sample id", "属性"):
            continue
        source = cols[0]
        rest = " ".join(cols[1:])
        acc = _first_accession(source) or _normalize(source.split("(")[0].strip())
        if acc is None or len(str(acc)) < 3:
            continue
        if any(k in rest for k in ("COMPLETED", "PARTIAL", "IN_PROGRESS", "AVAILABLE", "就绪",
                                    "已下载", "已获取", "已包含", "已集成", "硬编码", "已克隆", "成功", "是")):
            state[acc] = True
        elif any(k in rest for k in ("NOT_AVAILABLE", "BLOCKED", "OUT_OF_SCOPE", "MISSING",
                                     "未公开", "无法访问", "不可", "否")):
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
    # GitHub 仓库在 data_manifest 的表格中：| GitHub 代码仓库 | ... | COMPLETED | ... 仅含...无...源数据 |
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
        expected = c["downloadable"] == "true"
        if system[key] != expected:
            mismatches.append(f"{acc}: system={system[key]} expected={expected}")
    return {"passed": not mismatches, "actual": system,
            "note": "; ".join(mismatches) or "all data judgments match ground truth"}


def check_code_references(artifact, config):
    claims = [c for c in CLAIMS["code_references"] if c["ground_truth"] != "unknown"]
    system = _parse_provision_report(artifact)
    # data_manifest 的 "GitHub 代码仓库" 行：无 figure 源数据 → 主仓库 hollow
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
'''
