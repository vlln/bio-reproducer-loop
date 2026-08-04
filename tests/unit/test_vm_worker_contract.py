import json
import subprocess
from pathlib import Path

import pytest

from benchmarks.runner.execution import ExecutionRequest
from benchmarks.runner import cli
from benchmarks.runner.adapters import loopflow
from benchmarks.runner.release_gate import ReleaseGateError, require_formal_submission
from benchmarks.runner.sandbox import DockerSandbox, SandboxConfig
from benchmarks.runner.worker import (
    QemuWorker,
    VmWorkerConfig,
    WorkerIntegrityError,
    WorkerTimeout,
    WorkerTeardownError,
    WorkerUnavailable,
    sha256_file,
    sha256_tree,
)


ROOT = Path(__file__).parents[2]
ENTRY = ROOT / "benchmarks" / "entries" / "bench-001"


def _request(tmp_path: Path) -> ExecutionRequest:
    directories = [
        tmp_path / "input",
        tmp_path / "workspace",
        tmp_path / "output",
    ]
    for directory in directories:
        directory.mkdir()
    return ExecutionRequest(
        command=["probe-system", "--input", "/input", "--output", "/output"],
        input_dir=directories[0],
        workspace=directories[1],
        output_dir=directories[2],
    )


def _config(tmp_path: Path, **overrides) -> VmWorkerConfig:
    tmp_path.mkdir(parents=True, exist_ok=True)
    worker_image = tmp_path / "worker.qcow2"
    worker_image.write_bytes(b"immutable worker image")
    system_dir = tmp_path / "system"
    system_dir.mkdir()
    (system_dir / "probe-system").write_text("#!/bin/sh\nexit 0\n")
    ssh_key = tmp_path / "id_ed25519"
    ssh_key.write_text("fake private key")
    values = {
        "worker_image": worker_image,
        "worker_sha256": sha256_file(worker_image),
        "system_dir": system_dir,
        "system_sha256": sha256_tree(system_dir),
        "ssh_key": ssh_key,
        "network_policy": "offline",
        "timeout_seconds": 30,
        "boot_timeout_seconds": 10,
    }
    values.update(overrides)
    return VmWorkerConfig(**values)


def test_tree_digest_is_stable_and_rejects_symlinks(tmp_path):
    system = tmp_path / "system"
    system.mkdir()
    (system / "b").write_text("two")
    (system / "a").write_text("one")

    first = sha256_tree(system)
    second = sha256_tree(system)
    assert first == second
    assert len(first) == 64

    (system / "escape").symlink_to(tmp_path / "outside")
    with pytest.raises(WorkerIntegrityError, match="symlink"):
        sha256_tree(system)


def test_digest_mismatch_is_rejected_before_worker_launch(tmp_path):
    config = _config(tmp_path, worker_sha256="0" * 64)
    worker = QemuWorker(config)

    with pytest.raises(WorkerIntegrityError, match="worker image digest"):
        worker.verify_assets()


def test_formal_secret_names_are_validated_and_values_are_required(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="environment names"):
        _config(tmp_path / "invalid", pass_env=("TOKEN=value",))

    worker = QemuWorker(_config(tmp_path / "missing", pass_env=("MODEL_API_KEY",)))
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    with pytest.raises(WorkerIntegrityError, match="Required secret environment is unavailable"):
        worker.verify_assets()


def test_formal_secrets_travel_over_ssh_stdin_and_provenance_has_names_only(
    tmp_path, monkeypatch
):
    secret_value = "never-serialize-this-token"
    monkeypatch.setenv("MODEL_API_KEY", secret_value)
    worker = QemuWorker(_config(tmp_path, pass_env=("MODEL_API_KEY",)))
    request = _request(tmp_path)
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["input"] = kwargs.get("input")
        return subprocess.CompletedProcess(command, 0, "ok", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = worker._execute_guest(request, 22022)

    assert result.returncode == 0
    assert json.loads(captured["input"]) == {"MODEL_API_KEY": secret_value}
    assert secret_value not in " ".join(captured["command"])
    envelope = worker.execution_envelope()
    assert envelope["secrets"] == [
        {"name": "MODEL_API_KEY", "type": "environment"}
    ]
    assert secret_value not in json.dumps(envelope)


def test_kvm_and_qemu_are_mandatory_without_fallback(tmp_path, monkeypatch):
    config = _config(tmp_path)
    worker = QemuWorker(config)
    monkeypatch.setattr("benchmarks.runner.worker.shutil.which", lambda _: None)

    with pytest.raises(WorkerUnavailable, match="qemu-system"):
        worker.preflight()

    monkeypatch.setattr(
        "benchmarks.runner.worker.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )
    monkeypatch.setattr(Path, "exists", lambda self: False if self == Path("/dev/kvm") else True)
    with pytest.raises(WorkerUnavailable, match="/dev/kvm"):
        worker.preflight()


@pytest.mark.parametrize(
    ("policy", "restrict_value"),
    [("offline", "on"), ("controlled-egress", "off")],
)
def test_qemu_command_uses_kvm_fresh_overlay_and_only_explicit_mounts(
    tmp_path, policy, restrict_value
):
    config = _config(tmp_path, network_policy=policy)
    worker = QemuWorker(config)
    request = _request(tmp_path)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    overlay = runtime / "overlay.qcow2"

    command = worker.build_launch_command(request, overlay, runtime, ssh_port=22022)
    serialized = " ".join(command)

    assert command[:3] == ["qemu-system-x86_64", "-accel", "kvm"]
    assert f"file={overlay},if=virtio,format=qcow2" in command
    assert "-qmp" in command
    assert f"restrict={restrict_value}" in serialized
    assert "hostfwd=tcp:127.0.0.1:22022-:22" in serialized
    assert f"path={request.input_dir.resolve()},mount_tag=input" in serialized
    assert f"path={request.workspace.resolve()},mount_tag=workspace" in serialized
    assert f"path={request.output_dir.resolve()},mount_tag=output" in serialized
    assert f"path={config.system_dir.resolve()},mount_tag=system" in serialized
    input_mount = next(item for item in command if "mount_tag=input" in item)
    system_mount = next(item for item in command if "mount_tag=system" in item)
    assert "readonly=on" in input_mount
    assert "readonly=on" in system_mount
    assert "oracle" not in serialized
    assert "/var/run/docker.sock" not in serialized


class _FakeVmProcess:
    def __init__(self):
        self.returncode = None
        self.terminated = False

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = 0
        return 0

    def terminate(self):
        self.terminated = True
        self.returncode = 0

    def kill(self):
        self.returncode = -9


class _QmpFallbackProcess(_FakeVmProcess):
    def __init__(self):
        super().__init__()
        self.waits = 0

    def wait(self, timeout=None):
        self.waits += 1
        if self.waits == 1:
            raise subprocess.TimeoutExpired("qemu", timeout=timeout)
        self.returncode = 0
        return 0


def test_shutdown_uses_qmp_before_forcing_the_process(tmp_path, monkeypatch):
    worker = QemuWorker(_config(tmp_path))
    process = _QmpFallbackProcess()
    qmp_calls = []
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 255, "", ""),
    )
    monkeypatch.setattr(worker, "_qmp_powerdown", lambda runtime: qmp_calls.append(runtime) or True)

    assert worker._shutdown_guest(process, 22022, tmp_path) is True
    assert qmp_calls == [tmp_path]
    assert process.terminated is False


def test_successful_worker_run_records_formal_envelope_and_teardown(tmp_path, monkeypatch):
    worker = QemuWorker(_config(tmp_path))
    request = _request(tmp_path)
    process = _FakeVmProcess()
    runtime_paths = []

    monkeypatch.setattr(worker, "preflight", lambda: None)
    monkeypatch.setattr(worker, "verify_assets", lambda: None)

    def prepare(runtime):
        runtime_paths.append(runtime)
        overlay = runtime / "overlay.qcow2"
        overlay.write_bytes(b"overlay")
        return overlay

    monkeypatch.setattr(worker, "_prepare_overlay", prepare)
    monkeypatch.setattr(worker, "_start_vm", lambda *args, **kwargs: process)
    monkeypatch.setattr(worker, "_wait_for_guest", lambda *args, **kwargs: 12.5)
    monkeypatch.setattr(
        worker,
        "_execute_guest",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            request.command, 0, "probe ok", ""
        ),
    )
    monkeypatch.setattr(worker, "_shutdown_guest", lambda *args, **kwargs: True)

    result = worker.run(request)
    envelope = worker.execution_envelope()

    assert result.returncode == 0
    assert envelope["purpose"] == "formal"
    assert envelope["isolation"] == "disposable-vm"
    assert envelope["provider"] == "qemu-kvm"
    assert envelope["worker_image"]["digest"] == f"sha256:{worker.config.worker_sha256}"
    assert envelope["system_artifact"]["digest"] == f"sha256:{worker.config.system_sha256}"
    assert envelope["boot_seconds"] == 12.5
    assert envelope["teardown"] == {
        "status": "completed",
        "worker_absent": True,
        "overlay_absent": True,
        "secrets_revoked": True,
    }
    assert runtime_paths and not runtime_paths[0].exists()


def test_timeout_still_tears_down_and_preserves_provenance(tmp_path, monkeypatch):
    worker = QemuWorker(_config(tmp_path, timeout_seconds=7))
    request = _request(tmp_path)
    process = _FakeVmProcess()

    monkeypatch.setattr(worker, "preflight", lambda: None)
    monkeypatch.setattr(worker, "verify_assets", lambda: None)
    monkeypatch.setattr(
        worker,
        "_prepare_overlay",
        lambda runtime: runtime / "overlay.qcow2",
    )
    monkeypatch.setattr(worker, "_start_vm", lambda *args, **kwargs: process)
    monkeypatch.setattr(worker, "_wait_for_guest", lambda *args, **kwargs: 1.0)
    monkeypatch.setattr(
        worker,
        "_execute_guest",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            subprocess.TimeoutExpired(request.command, timeout=7)
        ),
    )
    monkeypatch.setattr(worker, "_shutdown_guest", lambda *args, **kwargs: True)

    with pytest.raises(WorkerTimeout, match="7 seconds"):
        worker.run(request)

    assert worker.execution_envelope()["teardown"]["status"] == "completed"


def test_teardown_failure_invalidates_an_otherwise_successful_run(tmp_path, monkeypatch):
    worker = QemuWorker(_config(tmp_path))
    request = _request(tmp_path)
    process = _FakeVmProcess()

    monkeypatch.setattr(worker, "preflight", lambda: None)
    monkeypatch.setattr(worker, "verify_assets", lambda: None)
    monkeypatch.setattr(worker, "_prepare_overlay", lambda runtime: runtime / "overlay.qcow2")
    monkeypatch.setattr(worker, "_start_vm", lambda *args, **kwargs: process)
    monkeypatch.setattr(worker, "_wait_for_guest", lambda *args, **kwargs: 1.0)
    monkeypatch.setattr(
        worker,
        "_execute_guest",
        lambda *args, **kwargs: subprocess.CompletedProcess(request.command, 0, "ok", ""),
    )
    monkeypatch.setattr(worker, "_shutdown_guest", lambda *args, **kwargs: False)

    with pytest.raises(WorkerTeardownError, match="teardown audit failed"):
        worker.run(request)

    assert worker.execution_envelope()["teardown"]["status"] == "failed"


def test_adapter_embeds_formal_worker_envelope_at_execution_root(tmp_path):
    class FakeFormalWorker:
        def run(self, request):
            result_dir = request.output_dir / "05_run" / "results"
            result_dir.mkdir(parents=True)
            (result_dir / "deseq_results.csv").write_text("gene,log2FoldChange\nA,1\n")
            return subprocess.CompletedProcess(request.command, 0, "ok", "")

        def execution_envelope(self):
            return _formal_submission()["execution"]

    submission = loopflow.run(
        ENTRY,
        run_dir=tmp_path / "run",
        sandbox=FakeFormalWorker(),
    )

    require_formal_submission(submission)
    assert submission["protocol_version"] == "2.0"
    assert submission["execution"]["provider"] == "qemu-kvm"
    assert "sandbox" not in submission["execution"]
    assert submission["artifacts"][0]["role"] == "result_table"


def test_docker_backend_is_explicitly_validation_only():
    sandbox = DockerSandbox(SandboxConfig(image="bio-reproducer:test"))

    assert sandbox.execution_envelope() == {
        "purpose": "validation-only",
        "isolation": "container",
        "provider": "docker",
        "network_policy": "offline",
        "deadline_seconds": 3600,
        "worker_image": {"id": "bio-reproducer:test"},
        "teardown": {"status": "not-run"},
    }


def _formal_submission() -> dict:
    return {
        "protocol_version": "2.0",
        "submission_id": "bench-001-test",
        "bench_id": "bench-001",
        "system": {"name": "fake", "version": "1"},
        "artifacts": [],
        "execution": {
            "purpose": "formal",
            "isolation": "disposable-vm",
            "provider": "qemu-kvm",
            "worker_image": {"digest": f"sha256:{'1' * 64}"},
            "system_artifact": {"digest": f"sha256:{'2' * 64}", "adapter": "fake@1"},
            "network_policy": "offline",
            "deadline_seconds": 60,
            "teardown": {
                "status": "completed",
                "worker_absent": True,
                "overlay_absent": True,
                "secrets_revoked": True,
            },
            "stages": [],
        },
    }


def test_release_gate_accepts_only_completed_qemu_vm_runs():
    require_formal_submission(_formal_submission())
    require_formal_submission(json.loads(json.dumps(_formal_submission())))

    validation = _formal_submission()
    validation["execution"]["purpose"] = "validation-only"
    with pytest.raises(ReleaseGateError, match="purpose"):
        require_formal_submission(validation)

    incomplete = _formal_submission()
    incomplete["execution"]["teardown"]["overlay_absent"] = False
    with pytest.raises(ReleaseGateError, match="teardown"):
        require_formal_submission(incomplete)

    fallback = _formal_submission()
    fallback["execution"]["provider"] = "tcg"
    with pytest.raises(ReleaseGateError, match="provider"):
        require_formal_submission(fallback)

    infrastructure_failure = _formal_submission()
    infrastructure_failure["execution"]["blocked_reason"] = "infrastructure"
    with pytest.raises(ReleaseGateError, match="infrastructure"):
        require_formal_submission(infrastructure_failure)


def test_worker_recipe_requires_docker_before_marking_image_ready():
    recipe = (
        ROOT / "benchmarks" / "runner" / "worker_image" / "build-worker.sh"
    ).read_text()

    assert "nameserver 223.5.5.5" in recipe
    assert "command -v docker" in recipe
    assert "systemctl is-active --quiet docker" in recipe
    assert "dpkg-query -W docker.io" in recipe
    assert "touch /var/lib/bio-reproducer-worker-ready" in recipe
    assert "condition: test -f /var/lib/bio-reproducer-worker-ready" in recipe
    assert "condition: true" not in recipe


def test_release_check_cli_returns_nonzero_for_validation_submission(tmp_path, capsys):
    submission = _formal_submission()
    submission["execution"]["purpose"] = "validation-only"
    path = tmp_path / "submission.json"
    path.write_text(json.dumps(submission))

    with pytest.raises(SystemExit) as error:
        cli.cmd_release_check(cli.argparse.Namespace(submission=str(path)))

    assert error.value.code == 2
    assert "RELEASE_GATE" in capsys.readouterr().err
