"""Executor-neutral request contract for benchmark systems under test."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class ExecutionError(RuntimeError):
    """Base class for stable executor failures."""


@dataclass(frozen=True)
class ExecutionRequest:
    """The only host directories and command exposed to an executor."""

    command: Sequence[str]
    input_dir: Path
    workspace: Path
    output_dir: Path

    def __post_init__(self) -> None:
        if not self.command or any(not str(item) for item in self.command):
            raise ValueError("Execution command must contain non-empty arguments")

    def validated_directories(self) -> tuple[Path, Path, Path]:
        directories = tuple(
            Path(path).resolve()
            for path in (self.input_dir, self.workspace, self.output_dir)
        )
        for directory in directories:
            if not directory.is_dir():
                raise ValueError(f"Execution directory does not exist: {directory}")
        for index, directory in enumerate(directories):
            others = directories[:index] + directories[index + 1 :]
            if any(
                directory == other
                or directory in other.parents
                or other in directory.parents
                for other in others
            ):
                raise ValueError(
                    "Execution input, workspace, and output directories must not overlap"
                )
        return directories
