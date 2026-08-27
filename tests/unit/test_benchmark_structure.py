import json
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
BENCHMARKS = ROOT / "benchmarks"
ENTRIES = BENCHMARKS / "entries"
ENTRY_IDS = ["bench-001", "bench-002", "bench-003", "bench-004", "bench-005", "bench-006", "bench-100"]
CLAIM_SECTIONS = {
    "experimental_design",
    "methods",
    "quantitative_results",
    "figures",
    "conclusions",
    "data_availability",
    "input_conditions",
}
FORBIDDEN_CLAIM_KEYS = {
    "checks",
    "check_id",
    "expected",
    "expected_verdict",
    "min_score",
    "runs_required",
    "type",
    "verdict_match_threshold",
    "verdict_thresholds",
    "weight",
}


def test_protocol_v2_entry_layout_is_minimal():
    entry_ids = sorted(
        e.name for e in ENTRIES.iterdir() if (e / "bundle.yaml").is_file()
    )
    assert len(entry_ids) == len(set(entry_ids))
    for entry_id in entry_ids:
        entry = ENTRIES / entry_id
        names = {path.name for path in entry.iterdir()}
        assert names >= {
            "input",
            "metadata.yaml",
            "oracle",
        }
        assert names <= {"bundle.yaml", "input", "metadata.yaml", "oracle"}
        # Interface 0001 OracleBundle allows optional verify.py alongside the two
        # required oracle files (used by the python_verify comparator).
        # __pycache__ 是运行 verify.py 测试的副作用，不属于 entry 结构。
        oracle_names = {path.name for path in (entry / "oracle").iterdir()
                        if path.name != "__pycache__"}
        assert oracle_names >= {"claims.yaml", "rubric.yaml"}
        assert oracle_names <= {"claims.yaml", "rubric.yaml", "verify.py"}


def test_all_entries_declare_protocol_v2():
    for entry_id in ENTRY_IDS:
        metadata = yaml.safe_load((ENTRIES / entry_id / "metadata.yaml").read_text())
        assert metadata["id"] == entry_id
        assert metadata["version"] == "2.0.0"
        assert metadata["protocol_version"] == "2.0"
        assert metadata["input_dir"] == "input/"
        assert metadata["oracle_dir"] == "oracle/"


def test_claims_are_scientific_facts_not_scoring_rules():
    schema = json.loads((BENCHMARKS / "schemas" / "claims.schema.json").read_text())
    required = set(schema["required"])
    allowed = set(schema["properties"])

    for entry_id in ENTRY_IDS:
        claims = yaml.safe_load(
            (ENTRIES / entry_id / "oracle" / "claims.yaml").read_text()
        )
        assert claims["id"] == entry_id
        assert required <= set(claims)
        assert set(claims) <= allowed
        assert not (set(claims) & FORBIDDEN_CLAIM_KEYS)

        claim_ids = []
        for section in CLAIM_SECTIONS & set(claims):
            assert claims[section]
            for claim in claims[section]:
                assert set(claim) <= {"claim_id", "description", "source", "details"}
                assert {"claim_id", "description", "source"} <= set(claim)
                assert not (set(claim) & FORBIDDEN_CLAIM_KEYS)
                claim_ids.append(claim["claim_id"])
        assert len(claim_ids) == len(set(claim_ids))


def test_protocol_v1_evaluator_is_not_runtime_code():
    assert not (BENCHMARKS / "runner" / "evaluator.py").exists()
