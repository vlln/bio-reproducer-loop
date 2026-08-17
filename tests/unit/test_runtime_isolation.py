import json
import subprocess
from pathlib import Path

import pytest

from benchmarks.runner import cli, runner
from benchmarks.runner.adapters import loopflow
from benchmarks.runner.sandbox import (
    DockerSandbox,
    SandboxConfig,
    SandboxRequest,
    SandboxTimeout,
    SandboxUnavailable,
)


ROOT = Path(__file__).parents[2]
ENTRY = ROOT / "benchmarks" / "entries" / "bench-001"


def _request(tmp_path: Path, profile: str = "offline") -> SandboxRequest:
    run_root = tmp_path / "run"
    input_dir = run_root / "input"
    workspace = run_root / "workspace"
    output_dir = run_root / "repro-data"
    for directory in (input_dir, workspace, output_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return SandboxRequest(
        command=["loop", "run", "bio-reproducer"],
        input_dir=input_dir,
        workspace=workspace,
        output_dir=output_dir,
    )


def test_docker_command_exposes_only_explicit_run_directories(tmp_path):
    sandbox = DockerSandbox(SandboxConfig(image="bio-reproducer:test", profile="offline"))

    command = sandbox.build_command(_request(tmp_path))

    assert command[:3] == ["docker", "run", "--rm"]
    assert "--read-only" in command
    assert command[command.index("--user") + 1] != "0:0"
    assert ["--cap-drop", "ALL"] == command[
        command.index("--cap-drop"):command.index("--cap-drop") + 2
    ]
    assert ["--security-opt", "no-new-privileges"] == command[
        command.index("--security-opt"):command.index("--security-opt") + 2
    ]
    assert ["--network", "none"] == command[
        command.index("--network"):command.index("--network") + 2
    ]
    assert command[command.index("--pids-limit") + 1] == "512"
    assert command[command.index("--memory") + 1] == "8g"
    assert command[command.index("--cpus") + 1] == "4"
    mounts = [command[index + 1] for index, value in enumerate(command) if value == "--mount"]
    assert any("dst=/input" in mount and "readonly" in mount for mount in mounts)
    assert any("dst=/workspace" in mount and "readonly" not in mount for mount in mounts)
    assert any("dst=/output" in mount and "readonly" not in mount for mount in mounts)
    assert all("oracle" not in mount and "/.git" not in mount for mount in mounts)
    assert str(ROOT) not in " ".join(command)


@pytest.mark.parametrize(
    ("profile", "network"),
    [("offline", "none"), ("discovery", "bridge"), ("tool-runtime", "bridge")],
)
def test_execution_profiles_select_network_without_host_runtime_mount(
    tmp_path, profile, network
):
    sandbox = DockerSandbox(SandboxConfig(image="bio-reproducer:test", profile=profile))

    command = sandbox.build_command(_request(tmp_path, profile))

    assert command[command.index("--network") + 1] == network
    assert "/var/run/docker.sock" not in " ".join(command)


def test_sandbox_passes_only_allowlisted_environment_names(tmp_path):
    sandbox = DockerSandbox(SandboxConfig(
        image="bio-reproducer:test",
        profile="discovery",
        pass_env=("MODEL_API_KEY",),
    ))

    command = sandbox.build_command(_request(tmp_path))
    environment = [command[index + 1] for index, value in enumerate(command) if value == "--env"]

    assert environment == ["HOME=/home/sandbox", "MODEL_API_KEY"]
    assert "SHOULD_NOT_LEAK" not in environment


def test_sandbox_timeout_has_stable_error(tmp_path, monkeypatch):
    commands = []

    def timeout_then_remove(command, **kwargs):
        commands.append(command)
        if command[1:3] == ["rm", "-f"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise subprocess.TimeoutExpired(command, timeout=kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", timeout_then_remove)
    sandbox = DockerSandbox(SandboxConfig(image="bio-reproducer:test", timeout_seconds=7))

    with pytest.raises(SandboxTimeout, match="7 seconds"):
        sandbox.run(_request(tmp_path))

    container_name = commands[0][commands[0].index("--name") + 1]
    assert commands[1] == ["docker", "rm", "-f", container_name]


def test_sandbox_rejects_overlapping_mount_directories(tmp_path):
    request = _request(tmp_path)
    nested = SandboxRequest(
        command=request.command,
        input_dir=request.input_dir,
        workspace=request.input_dir / "nested",
        output_dir=request.output_dir,
    )
    nested.workspace.mkdir()
    sandbox = DockerSandbox(SandboxConfig(image="bio-reproducer:test"))

    with pytest.raises(ValueError, match="must not overlap"):
        sandbox.build_command(nested)


@pytest.mark.parametrize("name", ["WITH-DASH", "WITH.DOT", "1STARTS_WITH_DIGIT", "A=B"])
def test_sandbox_rejects_invalid_environment_names(name):
    with pytest.raises(ValueError, match="Invalid environment names"):
        SandboxConfig(image="bio-reproducer:test", pass_env=(name,))


def test_host_execution_is_disabled_without_sandbox_image(monkeypatch):
    monkeypatch.delenv("BIO_REPRODUCER_SANDBOX_IMAGE", raising=False)

    with pytest.raises(SandboxUnavailable, match="host execution is disabled"):
        DockerSandbox.from_environment()


def test_adapter_uses_container_paths_and_never_passes_entry_path(tmp_path):
    captured = None

    class FakeSandbox:
        def run(self, request):
            nonlocal captured
            captured = request
            (request.output_dir / "01_plan").mkdir(parents=True)
            (request.output_dir / "01_plan" / "plan.md").write_text("plan")
            return subprocess.CompletedProcess(request.command, 0, "", "")

    result = loopflow.run(ENTRY, run_dir=tmp_path / "run", sandbox=FakeSandbox())

    assert result["bench_id"] == "bench-001"
    assert captured is not None
    serialized = json.dumps(captured.command)
    assert captured.command[0] == "/system/run-system"
    assert "/input/paper.md" in serialized
    assert "/output" in serialized
    assert str(ENTRY) not in serialized
    # loop 已移除 output_dir arg（agent 产物写当前工作目录）；适配器用
    # loopflow ≥0.23 的 --work-dir 把统一工作目录指向 /output，使产物落在 repro-data。
    assert captured.command[captured.command.index("--work-dir") + 1] == "/output"
    run_args = json.loads(captured.command[captured.command.index("--args") + 1])
    assert "output_dir" not in run_args
    assert run_args["paper_path"] == "/input/paper.md"
    assert run_args["confirm_plan"] is False
    assert run_args["consent"] == "auto"


def test_adapter_passes_declared_task_to_loop_args(tmp_path, monkeypatch):
    captured = None

    class FakeSandbox:
        def run(self, request):
            nonlocal captured
            captured = request
            return subprocess.CompletedProcess(request.command, 0, "", "")

    metadata = {
        "id": "bench-001",
        "protocol_version": "2.0",
        "input_dir": "input/",
        "complexity_profile": {"paper": {"paper_type": "constructed"}},
        "task": "仅复现 RNA-seq 差异表达与通路富集",
    }
    monkeypatch.setattr(loopflow, "_read_metadata", lambda entry_dir: metadata)

    loopflow.run(ENTRY, run_dir=tmp_path / "run", sandbox=FakeSandbox())

    run_args = json.loads(captured.command[captured.command.index("--args") + 1])
    assert run_args["scope"] == "仅复现 RNA-seq 差异表达与通路富集"


def test_adapter_omits_task_when_metadata_undeclared(tmp_path, monkeypatch):
    captured = None

    class FakeSandbox:
        def run(self, request):
            nonlocal captured
            captured = request
            return subprocess.CompletedProcess(request.command, 0, "", "")

    metadata = {
        "id": "bench-001",
        "protocol_version": "2.0",
        "input_dir": "input/",
        "complexity_profile": {"paper": {"paper_type": "constructed"}},
    }
    monkeypatch.setattr(loopflow, "_read_metadata", lambda entry_dir: metadata)

    loopflow.run(ENTRY, run_dir=tmp_path / "run", sandbox=FakeSandbox())

    run_args = json.loads(captured.command[captured.command.index("--args") + 1])
    assert "scope" not in run_args


def test_adapter_never_passes_scored_scope_into_loop_args(tmp_path, monkeypatch):
    # Plan 0025 泄漏回归：即使 metadata 残留 scored_scope（validator 会拒绝），
    # adapter 也不得把它翻译进系统侧 scope 参数。
    captured = None

    class FakeSandbox:
        def run(self, request):
            nonlocal captured
            captured = request
            return subprocess.CompletedProcess(request.command, 0, "", "")

    metadata = {
        "id": "bench-001",
        "protocol_version": "2.0",
        "input_dir": "input/",
        "complexity_profile": {"paper": {"paper_type": "constructed"}},
        "scored_scope": "d1_d3_audit",
    }
    monkeypatch.setattr(loopflow, "_read_metadata", lambda entry_dir: metadata)

    loopflow.run(ENTRY, run_dir=tmp_path / "run", sandbox=FakeSandbox())

    run_args = json.loads(captured.command[captured.command.index("--args") + 1])
    assert "scope" not in run_args


def test_adapter_keeps_legacy_docker_validation_image_entrypoint(tmp_path):
    captured = None

    class FakeDockerValidation:
        system_launcher = "loop"

        def run(self, request):
            nonlocal captured
            captured = request
            return subprocess.CompletedProcess(request.command, 0, "", "")

    loopflow.run(ENTRY, run_dir=tmp_path / "run", sandbox=FakeDockerValidation())

    assert captured.command[:3] == ["loop", "run", "bio-reproducer"]


def test_adapter_protocolizes_nonzero_sandbox_exit(tmp_path):
    class FailedSandbox:
        config = SandboxConfig(image="bio-reproducer:test", profile="offline")

        def run(self, request):
            results = request.output_dir / "05_run" / "results"
            results.mkdir(parents=True)
            (results / "deseq_results.csv").write_text("gene,log2FoldChange\nA,1\n")
            return subprocess.CompletedProcess(request.command, 23, "partial output", "failure")

    run_root = tmp_path / "run"
    result = loopflow.run(ENTRY, run_dir=run_root, sandbox=FailedSandbox())

    assert result["artifacts"] == [
        {
            "role": "result_table",
            "path": "repro-data/05_run/results/deseq_results.csv",
        }
    ]
    assert result["execution"]["blocked_reason"] == "system"
    assert result["execution"]["error"] == "loopflow exited with code 23"
    assert result["protocol_version"] == "2.0"
    assert {
        key: result["execution"][key]
        for key in (
            "purpose",
            "isolation",
            "provider",
            "network_policy",
            "deadline_seconds",
            "worker_image",
            "teardown",
        )
    } == {
        "purpose": "validation-only",
        "isolation": "container",
        "provider": "docker",
        "network_policy": "offline",
        "deadline_seconds": 3600,
        "worker_image": {"id": "bio-reproducer:test"},
        "teardown": {"status": "unknown"},
    }
    assert (run_root / "execution.stdout.log").read_text() == "partial output"
    assert (run_root / "execution.stderr.log").read_text() == "failure"


def test_runner_injects_sandbox_into_adapter(tmp_path, monkeypatch):
    expected = object()
    captured = None

    def fake_adapter(entry_path, run_dir, sandbox):
        nonlocal captured
        captured = sandbox
        return {
            "submission_id": "bench-001-test",
            "bench_id": "bench-001",
            "system": {"name": "test", "version": "1"},
            "artifacts": [],
            "execution": {"duration_seconds": 0, "stages": []},
        }

    monkeypatch.setattr(runner, "loopflow_run", fake_adapter)

    runner.run_entry(ENTRY, runs=1, output_dir=tmp_path / "results", sandbox=expected)

    assert captured is expected


def test_cli_defaults_to_formal_vm_and_rejects_missing_pins(monkeypatch, capsys):
    monkeypatch.delenv("BIO_REPRODUCER_SANDBOX_IMAGE", raising=False)
    for name in (
        "BIO_REPRODUCER_WORKER_IMAGE",
        "BIO_REPRODUCER_WORKER_SHA256",
        "BIO_REPRODUCER_SYSTEM_DIR",
        "BIO_REPRODUCER_SYSTEM_SHA256",
        "BIO_REPRODUCER_WORKER_SSH_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        "sys.argv",
        ["bench-run", "run", "--entry", "bench-001", "--runs", "0"],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    assert "WORKER_UNAVAILABLE" in capsys.readouterr().err


def test_cli_requires_explicit_docker_validation_backend(monkeypatch):
    args = cli.argparse.Namespace(
        backend="docker-validation",
        sandbox_image="bio-reproducer:test",
        sandbox_profile="offline",
        timeout=10,
        pass_env=[],
    )

    executor = cli._build_executor(args)

    assert isinstance(executor, DockerSandbox)
    assert executor.execution_envelope()["purpose"] == "validation-only"
