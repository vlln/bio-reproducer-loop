import json
import shutil
from pathlib import Path

import pytest
import yaml

from benchmarks.runner.adapters.loopflow import _stage_input
from benchmarks.runner.bundle_validator import BundleValidationError, validate_entry
from benchmarks.runner import runner


ROOT = Path(__file__).parents[2]
ENTRY = ROOT / "benchmarks" / "entries" / "bench-001"
ENTRIES = ROOT / "benchmarks" / "entries"
MIGRATED_ENTRY_IDS = ["bench-001", "bench-002", "bench-004", "bench-005", "bench-006"]


def _copy_entry(tmp_path: Path) -> Path:
    target = tmp_path / "bench-001"
    shutil.copytree(ENTRY, target)
    return target


def _read_bundle(entry: Path) -> dict:
    return yaml.safe_load((entry / "bundle.yaml").read_text())


def _write_bundle(entry: Path, bundle: dict) -> None:
    (entry / "bundle.yaml").write_text(yaml.safe_dump(bundle, sort_keys=False))


def test_pilot_entry_bundle_is_valid_and_schema_is_machine_readable():
    bundle = validate_entry(ENTRY)
    schema = json.loads((ROOT / "benchmarks" / "schemas" / "bundle.schema.json").read_text())

    assert bundle["entry_id"] == "bench-001"
    assert bundle["level"] == "L3"
    assert schema["properties"]["input_root"]["const"] == "input"


@pytest.mark.parametrize("entry_id", MIGRATED_ENTRY_IDS)
def test_all_migrated_constructed_entries_are_valid(entry_id):
    bundle = validate_entry(ENTRIES / entry_id)

    assert bundle["level"] == "L3"
    assert not (ENTRIES / entry_id / "input" / "paper.pdf").exists()


def test_unrebuilt_real_entry_remains_outside_bundle_gate():
    with pytest.raises(BundleValidationError, match="Missing bundle lock"):
        validate_entry(ENTRIES / "bench-003")


def test_missing_bundle_is_invalid(tmp_path):
    entry = _copy_entry(tmp_path)
    (entry / "bundle.yaml").unlink()

    with pytest.raises(BundleValidationError, match="Missing bundle lock") as error:
        validate_entry(entry)

    assert error.value.code == "INVALID_BUNDLE"


def test_rejects_undeclared_dotfile(tmp_path):
    entry = _copy_entry(tmp_path)
    (entry / "input" / ".answer.csv").write_text("hidden")

    with pytest.raises(BundleValidationError, match="Undeclared staged files"):
        validate_entry(entry)


def test_rejects_hash_mismatch(tmp_path):
    entry = _copy_entry(tmp_path)
    (entry / "input" / "data" / "counts.csv").write_text("changed")

    with pytest.raises(BundleValidationError, match="SHA256 mismatch"):
        validate_entry(entry)


def test_rejects_path_escape(tmp_path):
    entry = _copy_entry(tmp_path)
    bundle = _read_bundle(entry)
    bundle["resources"][0]["path"] = "../paper.md"
    _write_bundle(entry, bundle)

    with pytest.raises(BundleValidationError, match="escapes input_root"):
        validate_entry(entry)


def test_rejects_symlinked_input_root(tmp_path):
    entry = _copy_entry(tmp_path)
    real_input = entry / "real-input"
    (entry / "input").rename(real_input)
    (entry / "input").symlink_to(real_input, target_is_directory=True)

    with pytest.raises(BundleValidationError, match="input_root cannot be a symlink"):
        validate_entry(entry)


@pytest.mark.parametrize("field", ["expected_score", "rubric", "verdict"])
def test_rejects_oracle_fields_anywhere(tmp_path, field):
    entry = _copy_entry(tmp_path)
    bundle = _read_bundle(entry)
    bundle["resources"][0][field] = "private"
    _write_bundle(entry, bundle)

    with pytest.raises(BundleValidationError, match="Forbidden oracle field"):
        validate_entry(entry)


def test_rejects_missing_derived_provenance(tmp_path):
    entry = _copy_entry(tmp_path)
    bundle = _read_bundle(entry)
    resource = bundle["resources"][1]
    resource["authority"] = "derived"
    _write_bundle(entry, bundle)

    with pytest.raises(BundleValidationError, match="requires derived_from"):
        validate_entry(entry)


def test_rejects_timestamp_without_timezone(tmp_path):
    entry = _copy_entry(tmp_path)
    bundle = _read_bundle(entry)
    bundle["resources"][0]["retrieved_at"] = "2026-07-20T00:00:00"
    _write_bundle(entry, bundle)

    with pytest.raises(BundleValidationError, match="must include a timezone"):
        validate_entry(entry)


def test_rejects_level_metadata_conflict(tmp_path):
    entry = _copy_entry(tmp_path)
    bundle = _read_bundle(entry)
    bundle["level"] = "L4"
    _write_bundle(entry, bundle)

    with pytest.raises(BundleValidationError, match="L4 metadata paper_type"):
        validate_entry(entry)


def test_staging_replaces_old_tree_and_exposes_only_input(tmp_path):
    run_root = tmp_path / "run"
    stale = run_root / "input"
    stale.mkdir(parents=True)
    (stale / "bundle.yaml").write_text("leaked")
    (stale / "metadata.yaml").write_text("leaked")
    (stale / "oracle").mkdir()

    staged = _stage_input(ENTRY, run_root)

    assert {path.relative_to(staged).as_posix() for path in staged.rglob("*") if path.is_file()} == {
        "data/counts.csv",
        "paper.md",
    }
    assert not (staged / "bundle.yaml").exists()
    assert not (staged / "metadata.yaml").exists()
    assert not (staged / "oracle").exists()


def test_runner_validates_before_invoking_adapter(tmp_path, monkeypatch):
    entry = _copy_entry(tmp_path)
    (entry / "bundle.yaml").unlink()
    invoked = False

    def fake_adapter(*args, **kwargs):
        nonlocal invoked
        invoked = True

    monkeypatch.setattr(runner, "loopflow_run", fake_adapter)

    with pytest.raises(BundleValidationError, match="Missing bundle lock"):
        runner.run_entry(entry, runs=1, output_dir=tmp_path / "results")

    assert not invoked
    assert not (tmp_path / "results").exists()
