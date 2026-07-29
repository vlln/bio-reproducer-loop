"""Build and validate the opaque bio-reproducer system artifact."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tarfile
from pathlib import Path
from typing import Mapping, Sequence

import yaml


SCHEMA_VERSION = "1.1"
LOOP_NAME = "bio-reproducer"
LOOP_FILES = ("loop.md", "workflow.py", "pixi.toml", "pixi.lock")
FORBIDDEN_SOURCE_NAMES = {".git", ".local", ".pixi", ".skills", "__pycache__"}
SECRET_NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")
COMMIT_ID = re.compile(r"^[0-9a-f]{40}$")
IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
RUNTIME_REFERENCE = re.compile(
    r"^[a-z0-9]+(?:[._-][a-z0-9]+)*"
    r"(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*"
    r":[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$"
)


class SystemArtifactError(ValueError):
    """The system artifact source or materialized tree is invalid."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_source_tree(root: Path, label: str) -> None:
    if not root.is_dir():
        raise SystemArtifactError(f"{label} directory does not exist: {root}")
    for path in [root, *root.rglob("*")]:
        relative = path.relative_to(root).as_posix() or "."
        if path.is_symlink():
            raise SystemArtifactError(f"{label} contains symlink: {relative}")
        forbidden = FORBIDDEN_SOURCE_NAMES & set(path.relative_to(root).parts)
        if forbidden:
            name = sorted(forbidden)[0]
            raise SystemArtifactError(f"{label} contains generated state: {name}")
        if not path.is_dir() and not path.is_file():
            raise SystemArtifactError(f"{label} contains unsupported entry: {relative}")


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise SystemArtifactError(f"Agent definition lacks frontmatter: {path.name}")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise SystemArtifactError(f"Agent definition has invalid frontmatter: {path.name}")
    data = yaml.safe_load(parts[1])
    if not isinstance(data, dict):
        raise SystemArtifactError(f"Agent frontmatter must be an object: {path.name}")
    return data


def declared_skills(loop_dir: Path) -> set[str]:
    agents = loop_dir / "agents"
    if not agents.is_dir():
        raise SystemArtifactError("Loop source is missing agents directory")
    declared: set[str] = set()
    for agent in sorted(agents.glob("*.md")):
        skills = _frontmatter(agent).get("skills", [])
        if not isinstance(skills, list) or not all(isinstance(item, str) for item in skills):
            raise SystemArtifactError(f"Agent skills must be a string list: {agent.name}")
        declared.update(skills)
    return declared


def _copy_file(source: Path, target: Path, mode: int = 0o644) -> None:
    if not source.is_file() or source.is_symlink():
        raise SystemArtifactError(f"Required artifact input is not a regular file: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    target.chmod(mode)


def _copy_tree(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    target.chmod(0o755)
    for path in sorted(source.rglob("*"), key=lambda item: item.relative_to(source).as_posix()):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir():
            destination.mkdir()
            destination.chmod(0o755)
        else:
            _copy_file(path, destination)


def _runtime_archive_binding(
    archive_path: Path, runtime_image: str, runtime_reference: str
) -> None:
    if IMAGE_ID.fullmatch(runtime_reference) or not RUNTIME_REFERENCE.fullmatch(
        runtime_reference
    ):
        raise SystemArtifactError("Runtime reference must be a tagged Docker image name")
    try:
        with tarfile.open(archive_path, "r:*") as archive:
            member = archive.getmember("manifest.json")
            if not member.isfile() or member.size > 1024 * 1024:
                raise SystemArtifactError("Runtime archive manifest.json is invalid")
            handle = archive.extractfile(member)
            if handle is None:
                raise SystemArtifactError("Runtime archive manifest.json is unreadable")
            archive_manifest = json.load(handle)
    except SystemArtifactError:
        raise
    except (OSError, KeyError, tarfile.TarError, json.JSONDecodeError) as exc:
        raise SystemArtifactError(f"Invalid Docker runtime archive: {exc}") from exc

    if not isinstance(archive_manifest, list) or len(archive_manifest) != 1:
        raise SystemArtifactError("Runtime archive must contain exactly one image")
    image = archive_manifest[0]
    if not isinstance(image, dict):
        raise SystemArtifactError("Runtime archive image metadata is invalid")
    tags = image.get("RepoTags")
    if tags != [runtime_reference]:
        raise SystemArtifactError(
            "Runtime archive must contain exactly the declared reference"
        )
    config = image.get("Config")
    if not isinstance(config, str):
        raise SystemArtifactError("Runtime archive config identity is missing")
    config_digest = Path(config).name.removesuffix(".json")
    if f"sha256:{config_digest}" != runtime_image:
        raise SystemArtifactError(
            "Runtime archive config identity does not match the declared image"
        )


def _launcher(runtime_reference: str, required_secrets: Sequence[str]) -> str:
    secret_args = "\n".join(
        f'    --env {name} \\' for name in sorted(required_secrets)
    )
    if secret_args:
        secret_args += "\n"
    return f"""#!/bin/sh
set -eu

RUNTIME_ARCHIVE=/system/runtime/system-image.tar
test -r "$RUNTIME_ARCHIVE"
test -d /input
test -d /workspace
test -d /output

docker load --input "$RUNTIME_ARCHIVE" >/dev/null
exec docker run --rm --network host \\
    --volume /input:/input:ro \\
    --volume /workspace:/workspace \\
    --volume /output:/output \\
    --volume /system/loop/{LOOP_NAME}:/opt/loopflow/loops/{LOOP_NAME}:ro \\
    --volume /system/skills:/opt/loopflow/loops/{LOOP_NAME}/.skills:ro \\
    --volume /var/run/docker.sock:/var/run/docker.sock \\
    --env HOME=/workspace/.system-home \\
    --env LOOPFLOW_LOOPS_DIR=/opt/loopflow/loops \\
{secret_args}    --workdir /workspace \\
    {runtime_reference} loop "$@"
"""


def _file_manifest(root: Path) -> dict[str, dict]:
    files = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file() or path.name == "manifest.json":
            continue
        relative = path.relative_to(root).as_posix()
        files[relative] = {
            "sha256": _sha256(path),
            "size": path.stat().st_size,
            "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}",
        }
    return files


def build_system_artifact(
    output_dir: Path,
    *,
    loop_dir: Path,
    runtime_oci: Path,
    runtime_image: str,
    runtime_reference: str,
    skills: Mapping[str, Path],
    provenance: Mapping[str, str],
    required_secrets: Sequence[str] = (),
    skills_lock: Path | None = None,
) -> dict:
    """Materialize a deterministic artifact tree from explicit immutable inputs."""
    output_dir = Path(output_dir)
    loop_dir = Path(loop_dir)
    runtime_oci = Path(runtime_oci)
    if output_dir.exists():
        raise SystemArtifactError(f"Output directory already exists: {output_dir}")
    if not IMAGE_ID.fullmatch(runtime_image):
        raise SystemArtifactError("Runtime image must be a sha256 Docker config ID")
    invalid_secrets = sorted(name for name in required_secrets if not SECRET_NAME.fullmatch(name))
    if invalid_secrets:
        raise SystemArtifactError(
            f"Credentials must be secret names only: {', '.join(invalid_secrets)}"
        )
    for field in ("repository_commit", "loopflow_commit"):
        if not COMMIT_ID.fullmatch(str(provenance.get(field, ""))):
            raise SystemArtifactError(f"Invalid {field} in artifact provenance")
    if not provenance.get("loopflow_version"):
        raise SystemArtifactError("Missing loopflow_version in artifact provenance")

    _assert_source_tree(loop_dir, "Loop source")
    for name in LOOP_FILES:
        if not (loop_dir / name).is_file():
            raise SystemArtifactError(f"Loop source is missing {name}")
    required_skills = declared_skills(loop_dir)
    missing = sorted(required_skills - set(skills))
    if missing:
        raise SystemArtifactError(f"Missing declared skills: {', '.join(missing)}")
    if not runtime_oci.is_file() or runtime_oci.is_symlink():
        raise SystemArtifactError(
            f"Runtime Docker archive is not a regular file: {runtime_oci}"
        )
    _runtime_archive_binding(runtime_oci, runtime_image, runtime_reference)
    locked_skills = {}
    if skills_lock is not None:
        skills_lock = Path(skills_lock)
        if not skills_lock.is_file() or skills_lock.is_symlink():
            raise SystemArtifactError(f"Skills lock is not a regular file: {skills_lock}")
        lock_data = yaml.safe_load(skills_lock.read_text(encoding="utf-8"))
        locked_skills = lock_data.get("skills", {}) if isinstance(lock_data, dict) else {}
        if (
            not isinstance(lock_data, dict)
            or lock_data.get("schema_version") != "1.0"
            or set(locked_skills) != required_skills
        ):
            raise SystemArtifactError("Skills lock does not match declared skills")

    output_dir.mkdir(parents=True)
    try:
        artifact_loop = output_dir / "loop" / LOOP_NAME
        for name in LOOP_FILES:
            _copy_file(loop_dir / name, artifact_loop / name)
        _copy_tree(loop_dir / "agents", artifact_loop / "agents")

        skill_digests = {}
        for name in sorted(required_skills):
            source = Path(skills[name])
            _assert_source_tree(source, f"Skill {name}")
            if not (source / "SKILL.md").is_file():
                raise SystemArtifactError(f"Skill {name} is missing SKILL.md")
            _copy_tree(source, output_dir / "skills" / name)

        _copy_file(runtime_oci, output_dir / "runtime" / "system-image.tar")
        if skills_lock is not None:
            _copy_file(skills_lock, output_dir / "provenance" / "skills.lock.yaml")
        launcher = output_dir / "run-system"
        launcher.write_text(
            _launcher(runtime_reference, required_secrets), encoding="utf-8"
        )
        launcher.chmod(0o755)

        for name in sorted(required_skills):
            prefix = f"skills/{name}/"
            digest = hashlib.sha256()
            for relative, metadata in _file_manifest(output_dir).items():
                if relative.startswith(prefix):
                    digest.update(relative[len(prefix):].encode())
                    digest.update(bytes.fromhex(metadata["sha256"]))
            skill_digests[name] = {
                "sha256": digest.hexdigest(),
                **(
                    {
                        "repository": locked_skills[name]["repository"],
                        "commit": locked_skills[name]["commit"],
                        "subpath": locked_skills[name]["subpath"],
                    }
                    if locked_skills
                    else {}
                ),
            }

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "system": {"name": "bio-reproducer", "version": "0.1.0"},
            "launcher": "run-system",
            "runtime": {
                "format": "docker-archive",
                "image": runtime_image,
                "reference": runtime_reference,
                "archive_sha256": _sha256(output_dir / "runtime" / "system-image.tar"),
            },
            "loop": {
                "name": LOOP_NAME,
                "pixi_lock_sha256": _sha256(artifact_loop / "pixi.lock"),
            },
            "skills": skill_digests,
            "required_secrets": sorted(set(required_secrets)),
            "provenance": dict(sorted(provenance.items())),
            "files": _file_manifest(output_dir),
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        validate_system_artifact(output_dir)
        return manifest
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise


def validate_system_artifact(root: Path) -> dict:
    """Validate the manifest and every materialized artifact file."""
    root = Path(root)
    _assert_source_tree(root, "System artifact")
    manifest_path = root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemArtifactError(f"Invalid system artifact manifest: {exc}") from exc
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise SystemArtifactError("Unsupported system artifact schema_version")
    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("format") != "docker-archive":
        raise SystemArtifactError("System artifact runtime metadata is invalid")
    runtime_image = runtime.get("image")
    runtime_reference = runtime.get("reference")
    if not isinstance(runtime_image, str) or not IMAGE_ID.fullmatch(runtime_image):
        raise SystemArtifactError("System artifact runtime image is invalid")
    if not isinstance(runtime_reference, str):
        raise SystemArtifactError("System artifact runtime reference is invalid")
    _runtime_archive_binding(
        root / "runtime" / "system-image.tar",
        runtime_image,
        runtime_reference,
    )
    expected = manifest.get("files")
    if not isinstance(expected, dict):
        raise SystemArtifactError("System artifact manifest files must be an object")
    actual = _file_manifest(root)
    if set(actual) != set(expected):
        raise SystemArtifactError("System artifact file set does not match manifest")
    for relative, metadata in expected.items():
        if actual[relative] != metadata:
            raise SystemArtifactError(f"System artifact digest mismatch: {relative}")
    if not os.access(root / str(manifest.get("launcher", "")), os.X_OK):
        raise SystemArtifactError("System artifact launcher is missing or not executable")
    return manifest
