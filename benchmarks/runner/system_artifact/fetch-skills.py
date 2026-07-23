#!/usr/bin/env python3
"""Materialize skill sources at the commits in skills.lock.yaml."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} SKILLS_LOCK OUTPUT_DIR")
    lock_path = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    if output.exists():
        raise SystemExit(f"output already exists: {output}")
    data = yaml.safe_load(lock_path.read_text())
    if data.get("schema_version") != "1.0" or not isinstance(data.get("skills"), dict):
        raise SystemExit("invalid skills lock")

    output.mkdir(parents=True)
    try:
        repositories: dict[tuple[str, str], Path] = {}
        with tempfile.TemporaryDirectory(prefix="bio-reproducer-skills-") as tmp:
            for name, source in sorted(data["skills"].items()):
                key = (source["repository"], source["commit"])
                checkout = repositories.get(key)
                if checkout is None:
                    checkout = Path(tmp) / f"repository-{len(repositories)}"
                    subprocess.run(
                        ["git", "clone", "--quiet", "--no-checkout", key[0], checkout],
                        check=True,
                    )
                    subprocess.run(
                        ["git", "-C", checkout, "checkout", "--quiet", key[1]],
                        check=True,
                    )
                    repositories[key] = checkout
                skill = checkout / source["subpath"]
                if not (skill / "SKILL.md").is_file():
                    raise ValueError(f"skill source missing SKILL.md: {name}")
                shutil.copytree(skill, output / name, symlinks=False)
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise


if __name__ == "__main__":
    main()
