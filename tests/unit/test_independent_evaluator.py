import json
from pathlib import Path

import pytest
import yaml

from benchmarks.runner.adapters.loopflow import (
    _build_submission,
    _stage_input,
    build_submission_from_existing,
)
from benchmarks.runner.independent_evaluator import (
    EvaluationError,
    _evaluate_check,
    evaluate_submission,
)


ENTRY = Path(__file__).parents[2] / "benchmarks" / "entries" / "bench-001"
ENTRIES = ENTRY.parent


def _write_submission(tmp_path: Path, correct: bool = True, **extra) -> Path:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    gene_a_lfc = 2.9 if correct else 0.1
    gene_b_lfc = -2.0 if correct else 0.1
    gene_a_padj = 0.001 if correct else 0.9
    gene_b_padj = 0.002 if correct else 0.9
    (artifacts / "results.csv").write_text(
        ',baseMean,log2FoldChange,lfcSE,pvalue,padj,significant,direction\n'
        f'Gene_A,100,{gene_a_lfc},0.1,0.001,{gene_a_padj},Yes,Upregulated\n'
        f'Gene_B,100,{gene_b_lfc},0.1,0.001,{gene_b_padj},Yes,Downregulated\n'
        + "".join(
            f"Gene_{letter},100,0.0,0.1,0.5,0.9,No,Not significant\n"
            for letter in "CDEFGHIJ"
        )
    )
    header = "," + ",".join(f"Sample_{index}" for index in range(1, 7)) + "\n"
    (artifacts / "normalized.csv").write_text(
        header + "".join(f"Gene_{index},1,1,1,1,1,1\n" for index in range(10))
    )
    (artifacts / "session.txt").write_text("R 4.3.3\nDESeq2_1.42.1\n")
    (artifacts / "volcano.png").write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00P"
    )

    submission = {
        "submission_id": "bench-001-test",
        "bench_id": "bench-001",
        "system": {"name": "test-system", "version": "1.0"},
        "claimed_verdict": "FAILED",
        "artifacts": [
            {"role": "result_table", "path": "artifacts/results.csv"},
            {"role": "normalized_counts", "path": "artifacts/normalized.csv"},
            {"role": "environment", "path": "artifacts/session.txt"},
            {"role": "figure", "id": "volcano", "path": "artifacts/volcano.png"},
        ],
        "execution": {"duration_seconds": 1, "stages": []},
        **extra,
    }
    path = tmp_path / "submission.json"
    path.write_text(json.dumps(submission))
    return path


def test_scores_actual_artifacts_not_claimed_verdict(tmp_path):
    submission = _write_submission(tmp_path, correct=True, score=0)

    result = evaluate_submission(ENTRY, submission)

    assert result["score"] == 100
    assert result["verdict"] == "REPRODUCED"
    assert result["calibration"] == {"claimed_verdict": "FAILED", "matches": False}


def test_fabricated_claim_cannot_hide_wrong_results(tmp_path):
    submission = _write_submission(
        tmp_path,
        correct=False,
        claimed_verdict="REPRODUCED",
        score=100,
    )

    result = evaluate_submission(ENTRY, submission)

    assert result["score"] == 40
    assert result["verdict"] == "FAILED"
    assert result["calibration"]["matches"] is False


def test_rejects_artifact_path_outside_submission(tmp_path):
    outside = tmp_path.parent / "outside.csv"
    outside.write_text("secret")
    submission = {
        "submission_id": "bench-001-test",
        "bench_id": "bench-001",
        "system": {"name": "test-system", "version": "1.0"},
        "artifacts": [{"role": "result_table", "path": "../outside.csv"}],
        "execution": {"duration_seconds": 1, "stages": []},
    }
    path = tmp_path / "submission.json"
    path.write_text(json.dumps(submission))

    with pytest.raises(EvaluationError, match="escapes submission") as error:
        evaluate_submission(ENTRY, path)

    assert error.value.code == "INVALID_SUBMISSION"


def test_staged_input_excludes_private_oracle(tmp_path):
    staged = _stage_input(ENTRY, tmp_path)

    assert (staged / "paper.md").is_file()
    assert (staged / "data" / "counts.csv").is_file()
    assert not (staged / "oracle").exists()
    assert {path.name for path in staged.iterdir()} == {"paper.md", "data"}


def test_adapter_submission_contains_evidence_not_score(tmp_path):
    repro = tmp_path / "repro-data"
    results = repro / "05_run" / "results"
    figures = repro / "05_run" / "figures"
    results.mkdir(parents=True)
    figures.mkdir(parents=True)
    (results / "de_results.csv").write_text(",padj\nGene_A,0.01\n")
    (figures / "volcano_plot.png").write_bytes(b"image")

    submission = _build_submission(
        {"id": "bench-001"},
        tmp_path,
        repro,
        duration=3,
    )

    assert "score" not in submission
    assert "verdict" not in submission
    assert submission["execution"]["duration_seconds"] == 3
    assert {item["role"] for item in submission["artifacts"]} == {"result_table", "figure"}


def test_csv_row_supports_common_gene_column_aliases(tmp_path):
    entry = tmp_path / "bench-001"
    oracle = entry / "oracle"
    oracle.mkdir(parents=True)
    rubric = (ENTRY / "oracle" / "rubric.yaml").read_text()
    (oracle / "rubric.yaml").write_text(
        rubric.replace('key_column: ""', 'key_columns: [gene, Gene, ""]')
    )
    submission_root = tmp_path / "submission"
    submission_root.mkdir()
    submission = _write_submission(submission_root, correct=True)

    result = evaluate_submission(entry, submission)

    assert result["score"] == 100


def test_bench_100_scores_published_cuffdiff_conclusions(tmp_path):
    genes = ["DUSP1", "KLF15", "PER1", "TSC22D3", "C7", "CCDC69", "CRISPLD2"]
    rows = [
        f"{gene},{2.69648 if gene == 'CRISPLD2' else 1.0},"
        f"{6.9242e-13 if gene == 'CRISPLD2' else 0.001}"
        for gene in genes
    ]
    rows.extend(f"SIGNIFICANT_{index},0.5,0.01" for index in range(309))

    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "results.csv").write_text(
        "gene,log2_fold_change_dex_vs_control,q_value\n" + "\n".join(rows) + "\n"
    )
    (artifacts / "environment.txt").write_text(
        "Taffeta workflow\nCufflinks 2.0.2\nCuffdiff 2.0.2\n"
    )
    submission = {
        "submission_id": "bench-100-cuffdiff",
        "bench_id": "bench-100",
        "system": {"name": "test-system", "version": "1.0"},
        "artifacts": [
            {"role": "result_table", "path": "artifacts/results.csv"},
            {"role": "environment", "path": "artifacts/environment.txt"},
        ],
        "execution": {"duration_seconds": 1, "stages": []},
    }
    submission_path = tmp_path / "submission.json"
    submission_path.write_text(json.dumps(submission))

    result = evaluate_submission(ENTRIES / "bench-100", submission_path)

    assert result["score"] == 100
    assert result["verdict"] == "REPRODUCED"
    assert all(check["passed"] for check in result["checks"])


@pytest.mark.parametrize(
    "entry_id",
    ["bench-001", "bench-002", "bench-004", "bench-005", "bench-006", "bench-100"],
)
def test_v2_entries_keep_oracle_outside_staged_input(tmp_path, entry_id):
    entry = ENTRIES / entry_id
    metadata = yaml.safe_load((entry / "metadata.yaml").read_text())
    rubric = yaml.safe_load((entry / "oracle" / "rubric.yaml").read_text())

    staged = _stage_input(entry, tmp_path / entry_id)

    assert metadata["protocol_version"] == "2.0"
    assert metadata["input_dir"] == "input/"
    assert "baseline" not in metadata
    assert sum(float(check["weight"]) for check in rubric["checks"]) == 100
    assert not (staged / "oracle").exists()
    bundle = yaml.safe_load((entry / "bundle.yaml").read_text())
    paper = next(
        resource for resource in bundle["resources"]
        if resource["id"] == bundle["primary_paper"]
    )
    assert (staged / paper["path"]).is_file()


def test_bench_004_rubric_uses_valid_alternative_evidence_schema():
    schema = json.loads(
        (ENTRY.parents[1] / "schemas" / "rubric.schema.json").read_text()
    )
    rubric = yaml.safe_load((ENTRIES / "bench-004" / "oracle" / "rubric.yaml").read_text())
    evidence_schema = schema["properties"]["checks"]["items"]["properties"]["evidence"]

    assert {tuple(option["required"]) for option in evidence_schema["anyOf"]} == {
        ("artifact_role",),
        ("alternatives",),
    }
    assert evidence_schema["properties"]["alternatives"]["minItems"] == 1
    assert any("alternatives" in check["evidence"] for check in rubric["checks"])


def test_set_overlap_and_png_comparators(tmp_path):
    table = tmp_path / "genes.csv"
    table.write_text("gene\nA\nB\nC\n")
    png = tmp_path / "figure.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00P"
    )
    artifacts = {("genes", None): table, ("figure", "main"): png}

    overlap = _evaluate_check({
        "evidence": {"artifact_role": "genes"},
        "comparison": {
            "comparator": "csv_set_overlap",
            "column": "gene",
            "expected": ["A", "B", "D"],
            "min_recall": 0.6,
            "min_jaccard": 0.4,
        },
    }, artifacts, tmp_path)
    image = _evaluate_check({
        "evidence": {"artifact_role": "figure", "artifact_id": "main"},
        "comparison": {"comparator": "png_valid", "min_width": 100, "min_height": 80},
    }, artifacts, tmp_path)

    assert overlap[0] is True
    assert overlap[1]["overlap"] == ["A", "B"]
    assert image[0] is True
    assert image[1] == {"width": 100, "height": 80}


def test_trusted_python_verifier(tmp_path):
    artifact = tmp_path / "value.txt"
    artifact.write_text("42")
    verifier = tmp_path / "verify.py"
    verifier.write_text(
        "def verify(path, config):\n"
        "    actual = int(path.read_text())\n"
        "    return {'passed': actual == config['expected'], 'actual': actual}\n"
    )
    check = {
        "evidence": {"artifact_role": "value"},
        "comparison": {
            "comparator": "python_verify",
            "module": "verify.py",
            "config": {"expected": 42},
        },
    }

    passed, actual, _ = _evaluate_check(check, {("value", None): artifact}, tmp_path)

    assert passed is True
    assert actual == 42


def test_evidence_alternatives_can_express_reverse_contrasts(tmp_path):
    table = tmp_path / "thalamus_vs_cortex.csv"
    table.write_text("gene,log2FoldChange,padj\nNeurod6,-2.1,0.001\n")
    check = {
        "evidence": {
            "alternatives": [
                {
                    "artifact_role": "result_table",
                    "artifact_id": "cortex_vs_thalamus",
                    "comparison": {
                        "comparator": "csv_row",
                        "key_equals": "Neurod6",
                        "assertions": [{"column": "log2FoldChange", "operator": "greater_than", "value": 1}],
                    },
                },
                {
                    "artifact_role": "result_table",
                    "artifact_id": "thalamus_vs_cortex",
                    "comparison": {
                        "comparator": "csv_row",
                        "key_equals": "Neurod6",
                        "assertions": [{"column": "log2FoldChange", "operator": "less_than", "value": -1}],
                    },
                },
            ]
        },
        "comparison": {"comparator": "file_nonempty"},
    }

    passed, _, _ = _evaluate_check(
        check,
        {("result_table", "thalamus_vs_cortex"): table},
        tmp_path,
    )

    assert passed is True


def test_csv_row_can_filter_a_combined_contrast_table(tmp_path):
    table = tmp_path / "all.csv"
    table.write_text(
        "gene,log2FoldChange,padj,contrast\n"
        "Drd2,0.1,0.8,Cortex_vs_Thalamus\n"
        "Drd2,-2.0,0.001,Cortex_vs_Striatum\n"
    )
    check = {
        "evidence": {"artifact_role": "result_table", "artifact_id": "all"},
        "comparison": {
            "comparator": "csv_row",
            "key_equals": "Drd2",
            "where": [{"column": "contrast", "operator": "equals", "value": "Cortex_vs_Striatum"}],
            "assertions": [{"column": "log2FoldChange", "operator": "less_than", "value": -1}],
        },
    }

    passed, actual, _ = _evaluate_check(
        check,
        {("result_table", "all"): table},
        tmp_path,
    )

    assert passed is True
    assert actual["log2FoldChange"] == "-2.0"


def test_existing_run_submission_discovers_nested_benchmark_outputs(tmp_path):
    entry = tmp_path / "bench-005"
    entry.mkdir()
    (entry / "metadata.yaml").write_text("id: bench-005\nprotocol_version: '2.0'\n")
    run_dir = tmp_path / "run_01"
    nested = run_dir / "repro-data" / "05_run" / "results" / "results"
    nested.mkdir(parents=True)
    (nested / "results_DrugA_vs_DMSO.csv").write_text("gene,padj\nERBB2,0.01\n")
    (run_dir / "result.json").write_text(json.dumps({
        "verdict": "PARTIAL",
        "duration_seconds": 12,
        "stages": [{"name": "Run", "status": "completed"}],
    }))

    submission = build_submission_from_existing(entry, run_dir)

    assert submission["submission_id"] == "bench-005-run_01"
    assert submission["claimed_verdict"] == "PARTIAL"
    assert submission["execution"]["duration_seconds"] == 12
    assert submission["artifacts"][0] == {
        "role": "result_table",
        "path": "repro-data/05_run/results/results/results_DrugA_vs_DMSO.csv",
    }


def test_existing_run_submission_discovers_nextflow_output_layout(tmp_path):
    entry = tmp_path / "bench-legacy"
    entry.mkdir()
    (entry / "metadata.yaml").write_text("id: bench-legacy\nprotocol_version: '2.0'\n")
    run_dir = tmp_path / "run_01"
    output = run_dir / "repro-data" / "05_run" / "output"
    (output / "deseq2").mkdir(parents=True)
    (output / "figures").mkdir()
    (output / "deseq2" / "deseq2_all_results.csv").write_text(
        "gene,log2FoldChange,padj\nDUSP1,2.0,0.01\n"
    )
    (output / "deseq2" / "versions.txt").write_text("DESeq2_1.42.0\n")
    (output / "figures" / "volcano_plot.png").write_bytes(
        b"\x89PNG\r\n\x1a\n"
    )

    submission = build_submission_from_existing(entry, run_dir)

    assert submission["artifacts"] == [
        {
            "role": "result_table",
            "path": "repro-data/05_run/output/deseq2/deseq2_all_results.csv",
        },
        {
            "role": "environment",
            "path": "repro-data/05_run/output/deseq2/versions.txt",
        },
        {
            "role": "figure",
            "path": "repro-data/05_run/output/figures/volcano_plot.png",
            "id": "volcano",
        },
    ]


def test_existing_run_submission_discovers_flat_nextflow_results(tmp_path):
    entry = tmp_path / "bench-legacy"
    entry.mkdir()
    (entry / "metadata.yaml").write_text("id: bench-legacy\nprotocol_version: '2.0'\n")
    run_dir = tmp_path / "run_04"
    run = run_dir / "repro-data" / "05_run"
    provision = run_dir / "repro-data" / "03_provision"
    provision.mkdir(parents=True)
    (run / "results").mkdir(parents=True)
    (run / "figures").mkdir()
    (provision / "provision.md").write_text("DESeq2 1.10.1 verified\n")
    (run / "results" / "full_deseq2_results.csv").write_text(
        "gene,log2FoldChange,padj\nDUSP1,1.7,0.01\n"
    )
    (run / "figures" / "volcano_plot.pdf").write_bytes(b"%PDF-1.4\n")

    submission = build_submission_from_existing(entry, run_dir)

    assert submission["artifacts"] == [
        {
            "role": "result_table",
            "path": "repro-data/05_run/results/full_deseq2_results.csv",
        },
        {
            "role": "environment",
            "path": "repro-data/03_provision/provision.md",
        },
        {
            "role": "figure",
            "path": "repro-data/05_run/figures/volcano_plot.pdf",
            "id": "volcano",
        },
    ]


def test_existing_run_submission_discovers_contrast_named_results(tmp_path):
    entry = tmp_path / "bench-legacy"
    entry.mkdir()
    (entry / "metadata.yaml").write_text("id: bench-legacy\nprotocol_version: '2.0'\n")
    run_dir = tmp_path / "run_05"
    run = run_dir / "repro-data" / "05_run"
    (run / "results").mkdir(parents=True)
    (run / "figures").mkdir()
    (run / "results" / "deseq2_dex_vs_untreated_full_results.csv").write_text(
        "gene,log2FoldChange,padj\nDUSP1,1.7,0.01\n"
    )
    (run / "results" / "deseq2_dex_vs_untreated_normalized_counts.csv").write_text(
        "gene,sample_1\nDUSP1,10\n"
    )
    (run / "figures" / "deseq2_dex_vs_untreated_volcano.pdf").write_bytes(
        b"%PDF-1.4\n"
    )

    submission = build_submission_from_existing(entry, run_dir)

    assert submission["artifacts"] == [
        {
            "role": "result_table",
            "path": "repro-data/05_run/results/deseq2_dex_vs_untreated_full_results.csv",
        },
        {
            "role": "normalized_counts",
            "path": (
                "repro-data/05_run/results/"
                "deseq2_dex_vs_untreated_normalized_counts.csv"
            ),
        },
        {
            "role": "figure",
            "path": "repro-data/05_run/figures/deseq2_dex_vs_untreated_volcano.pdf",
            "id": "volcano",
        },
    ]
