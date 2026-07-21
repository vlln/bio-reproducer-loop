"""Validate the trusted entry bundle before staging runtime input."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


RESOURCE_ROLES = {
    "paper", "supplementary", "code", "data", "metadata", "environment", "resource_page"
}
AVAILABILITIES = {"bundled", "external", "restricted", "unavailable", "not_applicable"}
FORBIDDEN_KEYS = {
    "check", "checks", "expected", "expected_result", "expected_score", "expected_verdict",
    "fault_injection", "injection_intent", "oracle", "rubric", "score", "verdict",
}
TOP_LEVEL_KEYS = {
    "schema_version", "entry_id", "level", "input_root", "primary_paper", "resources"
}
RESOURCE_KEYS = {
    "id", "role", "authority", "availability", "path", "source", "sha256", "retrieved_at",
    "media_type", "license", "derived_from", "transform", "checked_at", "access_notes",
}
TRANSFORM_KEYS = {"tool", "version", "command", "script"}
RESERVED_INPUT_PATHS = {"bundle.yaml", "metadata.yaml", "oracle"}


class BundleValidationError(ValueError):
    """An entry bundle violates the benchmark control-plane contract."""

    code = "INVALID_BUNDLE"


def validate_entry(entry_dir: str | Path) -> dict[str, Any]:
    """Validate bundle structure, provenance, hashes, and metadata consistency."""
    entry = Path(entry_dir)
    bundle_path = entry / "bundle.yaml"
    if not bundle_path.is_file():
        raise BundleValidationError(f"Missing bundle lock: {bundle_path}")
    try:
        bundle = yaml.safe_load(bundle_path.read_text())
    except yaml.YAMLError as exc:
        raise BundleValidationError(f"Invalid bundle YAML: {exc}") from exc
    if not isinstance(bundle, dict):
        raise BundleValidationError("bundle.yaml must contain a mapping")

    _reject_forbidden_keys(bundle)
    _require_exact_keys(bundle, TOP_LEVEL_KEYS, "bundle")
    _require(bundle.get("schema_version") == "1.0", "schema_version must be '1.0'")
    _require(bundle.get("entry_id") == entry.name, "entry_id must match the entry directory")
    _require(
        re.fullmatch(r"bench-[0-9]{3}", str(bundle.get("entry_id"))) is not None,
        "entry_id must match bench-NNN",
    )
    level = bundle.get("level")
    _require(level in {"L3", "L4", "L5"}, "level must be L3, L4, or L5")
    _require(bundle.get("input_root") == "input", "input_root must be 'input'")

    input_root = entry / "input"
    _require(input_root.is_dir(), f"InputBundle not found: {input_root}")
    _require(not input_root.is_symlink(), "input_root cannot be a symlink")
    resources = bundle.get("resources")
    _require(isinstance(resources, list) and resources, "resources must be a non-empty list")

    by_id: dict[str, dict[str, Any]] = {}
    declared_paths: set[str] = set()
    for index, resource in enumerate(resources):
        context = f"resources[{index}]"
        _require(isinstance(resource, dict), f"{context} must be a mapping")
        _require_exact_keys(resource, RESOURCE_KEYS, context, require_all=False)
        for key in ("id", "role", "authority", "availability"):
            _require(_nonempty_string(resource.get(key)), f"{context}.{key} is required")
        resource_id = resource["id"]
        _require(resource_id not in by_id, f"Duplicate resource id: {resource_id}")
        by_id[resource_id] = resource
        _require(resource["role"] in RESOURCE_ROLES, f"Invalid role for {resource_id}")
        _require(
            resource["authority"] in {"original", "derived"},
            f"Invalid authority for {resource_id}",
        )
        availability = resource["availability"]
        _require(availability in AVAILABILITIES, f"Invalid availability for {resource_id}")

        if resource["authority"] == "original":
            _require(
                _nonempty_string(resource.get("source")),
                f"Original resource {resource_id} requires source",
            )
        else:
            parents = resource.get("derived_from")
            _require(
                isinstance(parents, list)
                and parents
                and all(_nonempty_string(item) for item in parents),
                f"Derived resource {resource_id} requires derived_from",
            )
            _validate_transform(resource.get("transform"), resource_id)

        if availability == "bundled":
            relative = _validate_resource_path(resource.get("path"), resource_id)
            _require(relative not in declared_paths, f"Duplicate bundled path: {relative}")
            declared_paths.add(relative)
            file_path = input_root / PurePosixPath(relative)
            _require(
                file_path.is_file() and not file_path.is_symlink(),
                f"Bundled resource is not a regular file: {relative}",
            )
            digest = resource.get("sha256")
            _require(
                isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
                f"Bundled resource {resource_id} requires lowercase SHA256",
            )
            _require(_sha256(file_path) == digest, f"SHA256 mismatch: {relative}")
            _require(
                _nonempty_string(resource.get("media_type")),
                f"Bundled resource {resource_id} requires media_type",
            )
            if resource["authority"] == "original":
                _require(
                    _nonempty_string(resource.get("retrieved_at")),
                    f"Bundled original {resource_id} requires retrieved_at",
                )
                _validate_timestamp(resource["retrieved_at"], f"retrieved_at for {resource_id}")
        else:
            _require(
                "path" not in resource and "sha256" not in resource,
                f"Non-bundled resource {resource_id} cannot declare path or sha256",
            )

        if availability in {"restricted", "unavailable"}:
            _require(
                _nonempty_string(resource.get("checked_at")),
                f"{availability} resource {resource_id} requires checked_at",
            )
            _validate_timestamp(resource["checked_at"], f"checked_at for {resource_id}")
            _require(
                _nonempty_string(resource.get("access_notes")),
                f"{availability} resource {resource_id} requires access_notes",
            )

    _validate_graph(by_id)
    _validate_primary_paper(bundle, by_id)
    _validate_metadata(entry, bundle)
    _validate_level(level, by_id)

    actual_paths = set()
    for path in input_root.rglob("*"):
        _require(
            not path.is_symlink(),
            f"InputBundle cannot contain symlinks: {path.relative_to(input_root)}",
        )
        if path.is_file():
            actual_paths.add(path.relative_to(input_root).as_posix())
    _require(
        not actual_paths - declared_paths,
        f"Undeclared staged files: {sorted(actual_paths - declared_paths)}",
    )
    _require(
        not declared_paths - actual_paths,
        f"Declared staged files missing: {sorted(declared_paths - actual_paths)}",
    )
    return bundle


def _validate_resource_path(value: Any, resource_id: str) -> str:
    _require(_nonempty_string(value), f"Bundled resource {resource_id} requires path")
    path = PurePosixPath(value)
    _require(
        "\\" not in value
        and not path.is_absolute()
        and ".." not in path.parts
        and "." not in path.parts,
        f"Resource path escapes input_root: {value}",
    )
    _require(
        path.parts[0] not in RESERVED_INPUT_PATHS,
        f"Resource path uses reserved control-plane name: {value}",
    )
    return path.as_posix()


def _validate_transform(value: Any, resource_id: str) -> None:
    _require(isinstance(value, dict), f"Derived resource {resource_id} requires transform")
    _require_exact_keys(value, TRANSFORM_KEYS, f"transform for {resource_id}", require_all=False)
    _require(
        _nonempty_string(value.get("tool")) and _nonempty_string(value.get("version")),
        f"Transform for {resource_id} requires tool and version",
    )
    _require(
        _nonempty_string(value.get("command")) or _nonempty_string(value.get("script")),
        f"Transform for {resource_id} requires command or script",
    )


def _validate_graph(resources: dict[str, dict[str, Any]]) -> None:
    for resource_id, resource in resources.items():
        for parent in resource.get("derived_from", []):
            _require(parent in resources, f"Unknown derived_from resource: {parent}")
            _require(parent != resource_id, f"Resource cannot derive from itself: {resource_id}")

    def visit(resource_id: str, trail: set[str]) -> None:
        _require(resource_id not in trail, f"Cycle in derived_from graph at {resource_id}")
        for parent in resources[resource_id].get("derived_from", []):
            visit(parent, trail | {resource_id})

    for resource_id in resources:
        visit(resource_id, set())


def _validate_primary_paper(bundle: dict[str, Any], resources: dict[str, dict[str, Any]]) -> None:
    primary_id = bundle.get("primary_paper")
    _require(primary_id in resources, "primary_paper must reference a resource")
    primary = resources[primary_id]
    _require(primary["role"] == "paper", "primary_paper resource must have role paper")
    _require(primary["authority"] == "original", "primary_paper must be original")
    allowed = {"bundled"} if bundle["level"] in {"L3", "L4"} else {"bundled", "external"}
    _require(
        primary["availability"] in allowed,
        f"{bundle['level']} primary_paper has invalid availability",
    )


def _validate_level(level: str, resources: dict[str, dict[str, Any]]) -> None:
    if level == "L4":
        _require(
            all(resource["availability"] != "external" for resource in resources.values()),
            "L4 resources must be bundled, restricted, unavailable, or not_applicable",
        )


def _validate_metadata(entry: Path, bundle: dict[str, Any]) -> None:
    metadata_path = entry / "metadata.yaml"
    _require(metadata_path.is_file(), f"Missing metadata: {metadata_path}")
    try:
        metadata = yaml.safe_load(metadata_path.read_text())
    except yaml.YAMLError as exc:
        raise BundleValidationError(f"Invalid metadata YAML: {exc}") from exc
    _require(isinstance(metadata, dict), "metadata.yaml must contain a mapping")
    _require(metadata.get("id") == bundle["entry_id"], "metadata id conflicts with bundle")
    _require(metadata.get("input_dir") == "input/", "metadata input_dir must be input/")
    paper_type = metadata.get("complexity_profile", {}).get("paper", {}).get("paper_type")
    if bundle["level"] == "L3":
        _require(paper_type == "constructed", "L3 metadata paper_type must be constructed")
    else:
        _require(
            paper_type == "real_published",
            f"{bundle['level']} metadata paper_type must be real_published",
        )


def _reject_forbidden_keys(value: Any, location: str = "bundle") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _require(key not in FORBIDDEN_KEYS, f"Forbidden oracle field at {location}.{key}")
            _reject_forbidden_keys(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_keys(child, f"{location}[{index}]")


def _require_exact_keys(
    value: dict[str, Any], allowed: set[str], context: str, require_all: bool = True
) -> None:
    unknown = set(value) - allowed
    _require(not unknown, f"Unknown fields in {context}: {sorted(unknown)}")
    if require_all:
        missing = allowed - set(value)
        _require(not missing, f"Missing fields in {context}: {sorted(missing)}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_timestamp(value: str, context: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BundleValidationError(f"{context} must be an ISO-8601 timestamp") from exc
    _require(parsed.tzinfo is not None, f"{context} must include a timezone")


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BundleValidationError(message)
