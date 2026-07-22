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
    assert "/input/paper.md" in serialized
    assert "/output" in serialized
    assert str(ENTRY) not in serialized


def test_adapter_protocolizes_nonzero_sandbox_exit(tmp_path):
    class FailedSandbox:
        config = SandboxConfig(image="bio-reproducer:test", profile="offline")

        def run(self, request):
            return subprocess.CompletedProcess(request.command, 23, "partial output", "failure")

    run_root = tmp_path / "run"
    result = loopflow.run(ENTRY, run_dir=run_root, sandbox=FailedSandbox())

    assert result["artifacts"] == []
    assert result["execution"]["blocked_reason"] == "system"
    assert result["execution"]["error"] == "loopflow exited with code 23"
    assert result["execution"]["sandbox"] == {
        "runtime": "docker",
        "profile": "offline",
        "image": "bio-reproducer:test",
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


def test_cli_rejects_run_without_sandbox_image(monkeypatch, capsys):
    monkeypatch.delenv("BIO_REPRODUCER_SANDBOX_IMAGE", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        ["bench-run", "run", "--entry", "bench-001", "--runs", "0"],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    assert "INVALID_SANDBOX" in capsys.readouterr().err
