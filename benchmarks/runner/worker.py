"""QEMU/KVM disposable worker backend for formal benchmark execution."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .execution import ExecutionError, ExecutionRequest


class WorkerError(ExecutionError):
    """Base class for stable disposable worker failures."""


class WorkerUnavailable(WorkerError):
    """QEMU/KVM cannot provide the required formal boundary."""


class WorkerIntegrityError(WorkerError):
    """A pinned worker or system artifact failed integrity validation."""


class WorkerBootError(WorkerError):
    """The guest control channel did not become ready."""


class WorkerTimeout(WorkerError):
    """The system exceeded the runner-owned deadline."""


class WorkerTeardownError(WorkerError):
    """Worker residue remained after execution."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(root: Path) -> str:
    """Hash relative paths, modes, and contents without following symlinks."""
    root = Path(root)
    if not root.is_dir():
        raise WorkerIntegrityError(f"System artifact directory does not exist: {root}")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise WorkerIntegrityError(f"System artifact contains symlink: {relative}")
        kind = "directory" if path.is_dir() else "file"
        mode = path.stat().st_mode & 0o777
        digest.update(f"{kind}\0{relative}\0{mode:o}\0".encode())
        if path.is_file():
            digest.update(bytes.fromhex(sha256_file(path)))
        elif not path.is_dir():
            raise WorkerIntegrityError(f"Unsupported system artifact entry: {relative}")
    return digest.hexdigest()


@dataclass(frozen=True)
class VmWorkerConfig:
    worker_image: Path
    worker_sha256: str
    system_dir: Path
    system_sha256: str
    ssh_key: Path
    network_policy: str = "offline"
    timeout_seconds: int = 3600
    boot_timeout_seconds: int = 60
    qemu_bin: str = "qemu-system-x86_64"
    qemu_img_bin: str = "qemu-img"
    ssh_bin: str = "ssh"
    ssh_user: str = "benchmark"
    memory_mb: int = 8192
    cpus: int = 4
    worker_image_id: str = "bio-reproducer-worker"
    adapter: str = "loopflow-adapter@0.1.0"
    pass_env: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.network_policy not in {"offline", "controlled-egress"}:
            raise ValueError(f"Unknown VM network policy: {self.network_policy}")
        if self.timeout_seconds <= 0 or self.boot_timeout_seconds <= 0:
            raise ValueError("VM deadlines must be above zero")
        if self.memory_mb <= 0 or self.cpus <= 0:
            raise ValueError("VM memory and CPU counts must be above zero")
        invalid_env = [
            name
            for name in self.pass_env
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None
        ]
        if invalid_env:
            raise ValueError(f"Invalid environment names: {invalid_env}")
        for name, digest in (
            ("worker_sha256", self.worker_sha256),
            ("system_sha256", self.system_sha256),
        ):
            if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
                raise ValueError(f"{name} must be 64 lowercase hexadecimal characters")

    @classmethod
    def from_environment(cls) -> "VmWorkerConfig":
        required = {
            "worker_image": os.environ.get("BIO_REPRODUCER_WORKER_IMAGE"),
            "worker_sha256": os.environ.get("BIO_REPRODUCER_WORKER_SHA256"),
            "system_dir": os.environ.get("BIO_REPRODUCER_SYSTEM_DIR"),
            "system_sha256": os.environ.get("BIO_REPRODUCER_SYSTEM_SHA256"),
            "ssh_key": os.environ.get("BIO_REPRODUCER_WORKER_SSH_KEY"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise WorkerUnavailable(
                f"Formal VM configuration is incomplete: {', '.join(missing)}"
            )
        return cls(
            worker_image=Path(required["worker_image"]),
            worker_sha256=str(required["worker_sha256"]),
            system_dir=Path(required["system_dir"]),
            system_sha256=str(required["system_sha256"]),
            ssh_key=Path(required["ssh_key"]),
            network_policy=os.environ.get(
                "BIO_REPRODUCER_WORKER_NETWORK_POLICY", "offline"
            ),
            timeout_seconds=int(
                os.environ.get("BIO_REPRODUCER_WORKER_TIMEOUT", "3600")
            ),
            boot_timeout_seconds=int(
                os.environ.get("BIO_REPRODUCER_WORKER_BOOT_TIMEOUT", "60")
            ),
            pass_env=tuple(
                item.strip()
                for item in os.environ.get(
                    "BIO_REPRODUCER_WORKER_PASS_ENV", ""
                ).split(",")
                if item.strip()
            ),
        )


class QemuWorker:
    """Execute one request in one fresh QEMU/KVM overlay."""

    system_launcher = "/system/run-system"

    def __init__(self, config: VmWorkerConfig):
        self.config = config
        self._boot_seconds: float | None = None
        self._teardown = {"status": "not-run"}

    def verify_assets(self) -> None:
        if not self.config.worker_image.is_file():
            raise WorkerIntegrityError(
                f"Worker image does not exist: {self.config.worker_image}"
            )
        actual_worker = sha256_file(self.config.worker_image)
        if actual_worker != self.config.worker_sha256:
            raise WorkerIntegrityError("worker image digest does not match configured digest")
        actual_system = sha256_tree(self.config.system_dir)
        if actual_system != self.config.system_sha256:
            raise WorkerIntegrityError("system artifact digest does not match configured digest")
        manifest_path = self.config.system_dir / "manifest.json"
        if manifest_path.is_file():
            from .system_artifact import SystemArtifactError, validate_system_artifact

            try:
                manifest = validate_system_artifact(self.config.system_dir)
            except SystemArtifactError as exc:
                raise WorkerIntegrityError(str(exc)) from exc
            declared_env = tuple(manifest.get("required_secrets", ()))
            if tuple(sorted(self.config.pass_env)) != tuple(sorted(declared_env)):
                raise WorkerIntegrityError(
                    "Configured secret environment does not match system artifact manifest"
                )
        if not self.config.ssh_key.is_file():
            raise WorkerIntegrityError(f"SSH key does not exist: {self.config.ssh_key}")
        missing_env = [name for name in self.config.pass_env if name not in os.environ]
        if missing_env:
            raise WorkerIntegrityError(
                "Required secret environment is unavailable: "
                + ", ".join(missing_env)
            )

    def preflight(self) -> None:
        for binary in (self.config.qemu_bin, self.config.qemu_img_bin, self.config.ssh_bin):
            if shutil.which(binary) is None:
                raise WorkerUnavailable(f"Required executable not found: {binary}")
        if not Path("/dev/kvm").exists():
            raise WorkerUnavailable("Required KVM device is unavailable: /dev/kvm")
        if not os.access("/dev/kvm", os.R_OK | os.W_OK):
            raise WorkerUnavailable("Required KVM device is not readable and writable: /dev/kvm")

    def build_launch_command(
        self,
        request: ExecutionRequest,
        overlay: Path,
        runtime: Path,
        ssh_port: int,
    ) -> list[str]:
        input_dir, workspace, output_dir = request.validated_directories()
        restrict = "on" if self.config.network_policy == "offline" else "off"
        command = [
            self.config.qemu_bin,
            "-accel",
            "kvm",
            "-machine",
            "q35",
            "-cpu",
            "host",
            "-m",
            str(self.config.memory_mb),
            "-smp",
            str(self.config.cpus),
            "-drive",
            f"file={overlay},if=virtio,format=qcow2",
            "-qmp",
            f"unix:{runtime / 'qmp.sock'},server=on,wait=off",
            "-netdev",
            f"user,id=net0,restrict={restrict},hostfwd=tcp:127.0.0.1:{ssh_port}-:22",
            "-device",
            "virtio-net-pci,netdev=net0",
        ]
        for tag, path, readonly in (
            ("input", input_dir, True),
            ("workspace", workspace, False),
            ("output", output_dir, False),
            ("system", self.config.system_dir.resolve(), True),
        ):
            option = f"local,path={path},mount_tag={tag},security_model=none"
            if readonly:
                option += ",readonly=on"
            command.extend(["-virtfs", option])
        command.extend(["-display", "none", "-serial", f"file:{runtime / 'serial.log'}"])
        return command

    def _prepare_overlay(self, runtime: Path) -> Path:
        overlay = runtime / "overlay.qcow2"
        command = [
            self.config.qemu_img_bin,
            "create",
            "-f",
            "qcow2",
            "-F",
            "qcow2",
            "-b",
            str(self.config.worker_image.resolve()),
            str(overlay),
        ]
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise WorkerIntegrityError(f"Could not create fresh worker overlay: {exc}") from exc
        return overlay

    @staticmethod
    def _reserve_ssh_port() -> int:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            return int(listener.getsockname()[1])

    def _start_vm(self, command: list[str]) -> subprocess.Popen[str]:
        try:
            return subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
        except OSError as exc:
            raise WorkerUnavailable(f"Could not launch QEMU/KVM worker: {exc}") from exc

    def _ssh_command(self, ssh_port: int, remote_command: str) -> list[str]:
        return [
            self.config.ssh_bin,
            "-i",
            str(self.config.ssh_key),
            "-p",
            str(ssh_port),
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "ConnectTimeout=2",
            f"{self.config.ssh_user}@127.0.0.1",
            remote_command,
        ]

    def _wait_for_guest(self, process: subprocess.Popen[str], ssh_port: int) -> float:
        started = time.monotonic()
        deadline = started + self.config.boot_timeout_seconds
        while time.monotonic() < deadline:
            returncode = process.poll()
            if returncode is not None:
                stderr = process.stderr.read() if process.stderr else ""
                raise WorkerBootError(
                    f"QEMU worker exited during boot with code {returncode}: {stderr.strip()}"
                )
            probe = subprocess.run(
                self._ssh_command(ssh_port, "true"),
                capture_output=True,
                text=True,
                check=False,
            )
            if probe.returncode == 0:
                return round(time.monotonic() - started, 3)
            time.sleep(1)
        raise WorkerBootError(
            f"Worker guest did not become ready within {self.config.boot_timeout_seconds} seconds"
        )

    def _execute_guest(
        self, request: ExecutionRequest, ssh_port: int
    ) -> subprocess.CompletedProcess[str]:
        mounts = " && ".join(
            f"sudo mountpoint -q /{tag} || sudo mount -t 9p -o trans=virtio,version=9p2000.L {tag} /{tag}"
            for tag in ("input", "workspace", "output", "system")
        )
        guest_exec = (
            "import json,os,sys; "
            "secrets=json.load(sys.stdin); "
            "env=os.environ.copy(); env.update(secrets); "
            "os.chdir('/workspace'); "
            "os.execvpe(sys.argv[1],sys.argv[1:],env)"
        )
        root_command = shlex.join([
            "env",
            "PATH=/system:/system/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "python3",
            "-c",
            guest_exec,
            *[str(item) for item in request.command],
        ])
        remote = (
            "set -eu; "
            "sudo mkdir -p /input /workspace /output /system; "
            f"{mounts}; "
            f"exec sudo {root_command}"
        )
        return subprocess.run(
            self._ssh_command(ssh_port, remote),
            capture_output=True,
            text=True,
            input=json.dumps(
                {name: os.environ[name] for name in self.config.pass_env}
            ),
            timeout=self.config.timeout_seconds,
            check=False,
        )

    @staticmethod
    def _qmp_powerdown(runtime: Path) -> bool:
        qmp_socket = runtime / "qmp.sock"
        if not qmp_socket.exists():
            return False
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(3)
                client.connect(str(qmp_socket))
                client.recv(4096)
                for command in ("qmp_capabilities", "system_powerdown"):
                    payload = json.dumps({"execute": command}).encode() + b"\r\n"
                    client.sendall(payload)
                    client.recv(4096)
            return True
        except OSError:
            return False

    def _shutdown_guest(
        self, process: subprocess.Popen[str], ssh_port: int, runtime: Path
    ) -> bool:
        if process.poll() is None:
            try:
                subprocess.run(
                    self._ssh_command(ssh_port, "sudo poweroff"),
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                process.wait(timeout=20)
            except (OSError, subprocess.TimeoutExpired):
                self._qmp_powerdown(runtime)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
        return process.poll() is not None

    def run(self, request: ExecutionRequest) -> subprocess.CompletedProcess[str]:
        request.validated_directories()
        self.verify_assets()
        self.preflight()
        runtime = Path(tempfile.mkdtemp(prefix="bio-reproducer-worker-"))
        overlay: Path | None = None
        process: subprocess.Popen[str] | None = None
        ssh_port = self._reserve_ssh_port()
        execution_error: BaseException | None = None
        result: subprocess.CompletedProcess[str] | None = None
        worker_absent = True
        try:
            overlay = self._prepare_overlay(runtime)
            command = self.build_launch_command(request, overlay, runtime, ssh_port)
            process = self._start_vm(command)
            self._boot_seconds = self._wait_for_guest(process, ssh_port)
            result = self._execute_guest(request, ssh_port)
        except subprocess.TimeoutExpired as exc:
            execution_error = WorkerTimeout(
                f"Worker execution exceeded {self.config.timeout_seconds} seconds"
            )
            execution_error.__cause__ = exc
        except Exception as exc:
            execution_error = exc
        finally:
            if process is not None:
                try:
                    worker_absent = self._shutdown_guest(process, ssh_port, runtime)
                except Exception:
                    worker_absent = False
                    try:
                        if process.poll() is None:
                            process.terminate()
                            process.wait(timeout=10)
                        worker_absent = process.poll() is not None
                    except (OSError, subprocess.TimeoutExpired):
                        try:
                            process.kill()
                            process.wait(timeout=10)
                            worker_absent = process.poll() is not None
                        except (OSError, subprocess.TimeoutExpired):
                            worker_absent = False
            shutil.rmtree(runtime, ignore_errors=True)
            overlay_absent = overlay is None or not overlay.exists()
            self._teardown = {
                "status": "completed" if worker_absent and overlay_absent else "failed",
                "worker_absent": worker_absent,
                "overlay_absent": overlay_absent,
                "secrets_revoked": True,
            }

        if self._teardown["status"] != "completed":
            raise WorkerTeardownError("Disposable worker teardown audit failed") from execution_error
        if execution_error is not None:
            raise execution_error
        assert result is not None
        return result

    def execution_envelope(self) -> dict:
        envelope = {
            "purpose": "formal",
            "isolation": "disposable-vm",
            "provider": "qemu-kvm",
            "network_policy": self.config.network_policy,
            "deadline_seconds": self.config.timeout_seconds,
            "worker_image": {
                "id": self.config.worker_image_id,
                "digest": f"sha256:{self.config.worker_sha256}",
            },
            "system_artifact": {
                "digest": f"sha256:{self.config.system_sha256}",
                "adapter": self.config.adapter,
            },
            "teardown": dict(self._teardown),
        }
        if self._boot_seconds is not None:
            envelope["boot_seconds"] = self._boot_seconds
        if self.config.pass_env:
            envelope["secrets"] = [
                {"name": name, "type": "environment"}
                for name in sorted(self.config.pass_env)
            ]
        return envelope
