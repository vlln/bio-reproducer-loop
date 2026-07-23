import json
from pathlib import Path

import pytest

from benchmarks.runner.system_artifact import (
    SystemArtifactError,
    build_system_artifact,
    validate_system_artifact,
)
from benchmarks.runner.worker import sha256_tree


ROOT = Path(__file__).parents[2]
LOOP_DIR = ROOT / "loops" / "bio-reproducer"


def _skill(tmp_path: Path, name: str) -> Path:
    root = tmp_path / "skill-sources" / name
    root.mkdir(parents=True)
    (root / "SKILL.md").write_text(f"---\nname: {name}\ndescription: test\n---\n")
    return root


def _build(tmp_path: Path, **overrides):
    tmp_path.mkdir(parents=True, exist_ok=True)
    runtime = tmp_path / "bio-reproducer-runtime.tar"
    runtime.write_bytes(b"pinned OCI archive")
    skills = {
        name: _skill(tmp_path, name)
        for name in (
            "background-task",
            "biocontainers",
            "image-mirror-skill",
            "mineru-api",
            "paperutils",
            "quay",
            "zenodo",
        )
    }
    values = {
        "output_dir": tmp_path / "artifact",
        "loop_dir": LOOP_DIR,
        "runtime_oci": runtime,
        "runtime_image": "sha256:" + "a" * 64,
        "skills": skills,
        "provenance": {
            "repository_commit": "b" * 40,
            "loopflow_commit": "c" * 40,
            "loopflow_version": "0.17.2",
        },
        "required_secrets": ("DASHSCOPE_API_KEY",),
        "skills_lock": ROOT / "benchmarks" / "runner" / "system_artifact" / "skills.lock.yaml",
    }
    values.update(overrides)
    manifest = build_system_artifact(**values)
    return Path(values["output_dir"]), manifest


def test_builder_is_deterministic_and_records_pinned_inputs(tmp_path):
    first, manifest = _build(tmp_path / "first")
    second, second_manifest = _build(tmp_path / "second")

    assert manifest == second_manifest
    assert sha256_tree(first) == sha256_tree(second)
    assert manifest["schema_version"] == "1.0"
    assert manifest["launcher"] == "run-system"
    assert manifest["runtime"]["format"] == "oci-archive"
    assert manifest["runtime"]["image"].endswith("a" * 64)
    assert manifest["loop"]["pixi_lock_sha256"] == (
        "c1d0c68a88aad97a7634ec2f4399b7991115783d4445f000c5fd9cac718261e0"
    )
    assert manifest["required_secrets"] == ["DASHSCOPE_API_KEY"]
    assert sorted(manifest["skills"]) == [
        "background-task",
        "biocontainers",
        "image-mirror-skill",
        "mineru-api",
        "paperutils",
        "quay",
        "zenodo",
    ]
    assert manifest["skills"]["quay"]["commit"] == (
        "63d8622388c11a3094023c18f84586f2fcc42eed"
    )
    assert validate_system_artifact(first) == manifest


def test_builder_rejects_missing_declared_skill(tmp_path):
    with pytest.raises(SystemArtifactError, match="Missing declared skills: .*zenodo"):
        _build(tmp_path, skills={})


def test_builder_rejects_symlinks_and_generated_state(tmp_path):
    loop_copy = tmp_path / "loop"
    loop_copy.mkdir()
    for name in ("loop.md", "workflow.py", "pixi.toml", "pixi.lock"):
        (loop_copy / name).write_bytes((LOOP_DIR / name).read_bytes())
    (loop_copy / "agents").symlink_to(LOOP_DIR / "agents")

    with pytest.raises(SystemArtifactError, match="symlink"):
        _build(tmp_path / "symlink", loop_dir=loop_copy)

    generated = tmp_path / "generated-loop"
    generated.mkdir()
    for name in ("loop.md", "workflow.py", "pixi.toml", "pixi.lock"):
        (generated / name).write_bytes((LOOP_DIR / name).read_bytes())
    (generated / "agents").mkdir()
    (generated / "agents" / "reader.md").write_text(
        (LOOP_DIR / "agents" / "reader.md").read_text()
    )
    (generated / ".pixi").mkdir()

    with pytest.raises(SystemArtifactError, match="generated state.*.pixi"):
        _build(tmp_path / "generated", loop_dir=generated)


@pytest.mark.parametrize(
    "secret",
    ["TOKEN=value", "1INVALID", "WITH-DASH", "AWS_SECRET_ACCESS_KEY=plaintext"],
)
def test_builder_accepts_secret_names_only(secret, tmp_path):
    with pytest.raises(SystemArtifactError, match="secret name"):
        _build(tmp_path, required_secrets=(secret,))


def test_validator_detects_tampering(tmp_path):
    artifact, _ = _build(tmp_path)
    (artifact / "loop" / "bio-reproducer" / "workflow.py").write_text("tampered")

    with pytest.raises(SystemArtifactError, match="digest mismatch"):
        validate_system_artifact(artifact)


def test_launcher_uses_guest_local_docker_and_explicit_mounts(tmp_path):
    artifact, _ = _build(tmp_path)
    launcher = (artifact / "run-system").read_text()

    assert "/system/runtime/system-image.tar" in launcher
    assert "/input:/input:ro" in launcher
    assert "/workspace:/workspace" in launcher
    assert "/output:/output" in launcher
    assert "/system/loop/bio-reproducer" in launcher
    assert "/system/skills" in launcher
    assert "/var/run/docker.sock:/var/run/docker.sock" in launcher
    assert "DASHSCOPE_API_KEY=" not in launcher
    assert "--env DASHSCOPE_API_KEY" in launcher
    assert "eval " not in launcher


def test_manifest_contains_no_secret_values(tmp_path):
    artifact, _ = _build(tmp_path)
    serialized = json.dumps(json.loads((artifact / "manifest.json").read_text()))

    assert "plaintext" not in serialized
    assert "DASHSCOPE_API_KEY" in serialized
