"""Container boundary for benchmark systems under test."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PROFILE_NETWORKS = {
    "offline": "none",
    "discovery": "bridge",
    "tool-runtime": "bridge",
}


class SandboxError(RuntimeError):
    """Base class for stable sandbox failures."""


class SandboxUnavailable(SandboxError):
    """The configured container runtime or image is unavailable."""


class SandboxTimeout(SandboxError):
    """The isolated process exceeded its configured deadline."""


@dataclass(frozen=True)
class SandboxConfig:
    image: str
    profile: str = "offline"
    timeout_seconds: int = 3600
    pass_env: tuple[str, ...] = ()
    docker_bin: str = "docker"
    memory: str = "8g"
    cpus: str = "4"
    pids_limit: int = 512

    def __post_init__(self) -> None:
        if not self.image:
            raise ValueError("A sandbox image is required")
        if self.profile not in PROFILE_NETWORKS:
            raise ValueError(f"Unknown sandbox profile: {self.profile}")
        if self.timeout_seconds <= 0:
            raise ValueError("Sandbox timeout must be above zero")
        invalid = [
            name
            for name in self.pass_env
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None
        ]
        if invalid:
            raise ValueError(f"Invalid environment names: {invalid}")

    @classmethod
    def from_environment(cls) -> "SandboxConfig":
        image = os.environ.get("BIO_REPRODUCER_SANDBOX_IMAGE", "")
        if not image:
            raise SandboxUnavailable(
                "BIO_REPRODUCER_SANDBOX_IMAGE is required; host execution is disabled"
            )
        pass_env = tuple(
            filter(
                None,
                (
                    item.strip()
                    for item in os.environ.get(
                        "BIO_REPRODUCER_SANDBOX_PASS_ENV", ""
                    ).split(",")
                ),
            )
        )
        return cls(
            image=image,
            profile=os.environ.get("BIO_REPRODUCER_SANDBOX_PROFILE", "offline"),
            timeout_seconds=int(os.environ.get("BIO_REPRODUCER_SANDBOX_TIMEOUT", "3600")),
            pass_env=pass_env,
        )


@dataclass(frozen=True)
class SandboxRequest:
    command: Sequence[str]
    input_dir: Path
    workspace: Path
    output_dir: Path


class DockerSandbox:
    """Run a system in Docker without exposing the benchmark repository."""

    def __init__(self, config: SandboxConfig):
        self.config = config

    @classmethod
    def from_environment(cls) -> "DockerSandbox":
        return cls(SandboxConfig.from_environment())

    def build_command(
        self,
        request: SandboxRequest,
        container_name: str | None = None,
    ) -> list[str]:
        input_dir, workspace, output_dir = self._validate_directories(request)
        uid = os.getuid() if hasattr(os, "getuid") else 65534
        gid = os.getgid() if hasattr(os, "getgid") else 65534
        command = [
            self.config.docker_bin,
            "run",
            "--rm",
            "--read-only",
            "--network",
            PROFILE_NETWORKS[self.config.profile],
            "--user",
            f"{uid}:{gid}",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            str(self.config.pids_limit),
            "--memory",
            self.config.memory,
            "--cpus",
            self.config.cpus,
            "--workdir",
            "/workspace",
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,size=1g",
            "--tmpfs",
            f"/home/sandbox:rw,nosuid,nodev,size=256m,uid={uid},gid={gid}",
            "--mount",
            f"type=bind,src={input_dir},dst=/input,readonly",
            "--mount",
            f"type=bind,src={workspace},dst=/workspace",
            "--mount",
            f"type=bind,src={output_dir},dst=/output",
            "--env",
            "HOME=/home/sandbox",
        ]
        if container_name is not None:
            command[3:3] = ["--name", container_name]
        for name in self.config.pass_env:
            command.extend(["--env", name])
        command.extend([self.config.image, *map(str, request.command)])
        return command

    def run(self, request: SandboxRequest) -> subprocess.CompletedProcess[str]:
        container_name = f"bio-reproducer-{uuid.uuid4().hex}"
        command = self.build_command(request, container_name=container_name)
        if shutil.which(self.config.docker_bin) is None:
            raise SandboxUnavailable(f"Container runtime not found: {self.config.docker_bin}")
        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            self._remove_container(container_name)
            raise SandboxTimeout(
                f"Sandbox execution exceeded {self.config.timeout_seconds} seconds"
            ) from exc
        except OSError as exc:
            raise SandboxUnavailable(f"Could not launch sandbox: {exc}") from exc

    @staticmethod
    def _validate_directories(request: SandboxRequest) -> tuple[Path, Path, Path]:
        directories = tuple(
            Path(path).resolve()
            for path in (request.input_dir, request.workspace, request.output_dir)
        )
        for directory in directories:
            if not directory.is_dir():
                raise ValueError(f"Sandbox directory does not exist: {directory}")
        for index, directory in enumerate(directories):
            others = directories[:index] + directories[index + 1:]
            if any(
                directory == other
                or directory in other.parents
                or other in directory.parents
                for other in others
            ):
                raise ValueError(
                    "Sandbox input, workspace, and output directories must not overlap"
                )
        return directories

    def _remove_container(self, container_name: str) -> None:
        """Ensure a timed-out container cannot outlive the runner process."""
        try:
            subprocess.run(
                [self.config.docker_bin, "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
