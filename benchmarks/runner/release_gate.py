"""Release-time checks for formal benchmark submissions."""

from __future__ import annotations

import re
from collections.abc import Mapping


class ReleaseGateError(ValueError):
    """A submission cannot enter a formal report or baseline."""


def require_formal_submission(submission: Mapping[str, object]) -> None:
    """Reject results that do not prove the frozen formal execution boundary."""
    if submission.get("protocol_version") != "2.0":
        raise ReleaseGateError("protocol_version must be 2.0")

    execution = submission.get("execution")
    if not isinstance(execution, Mapping):
        raise ReleaseGateError("execution envelope is required")
    if execution.get("purpose") != "formal":
        raise ReleaseGateError("execution purpose must be formal")
    if execution.get("isolation") != "disposable-vm":
        raise ReleaseGateError("formal isolation must be disposable-vm")
    if execution.get("provider") != "qemu-kvm":
        raise ReleaseGateError("formal provider must be qemu-kvm")

    for field in ("worker_image", "system_artifact"):
        artifact = execution.get(field)
        digest = artifact.get("digest") if isinstance(artifact, Mapping) else None
        if not isinstance(digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", digest
        ) is None:
            raise ReleaseGateError(f"{field} sha256 digest is required")

    teardown = execution.get("teardown")
    teardown_complete = isinstance(teardown, Mapping) and all(
        teardown.get(field) is expected
        for field, expected in (
            ("status", "completed"),
            ("worker_absent", True),
            ("overlay_absent", True),
            ("secrets_revoked", True),
        )
    )
    if not teardown_complete:
        raise ReleaseGateError("completed teardown audit is required")
    if execution.get("blocked_reason") == "infrastructure":
        raise ReleaseGateError("infrastructure-blocked runs cannot be released")
