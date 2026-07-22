import os
import shlex
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from benchmarks.runner.sandbox import (
    DockerSandbox,
    SandboxConfig,
    SandboxRequest,
    SandboxTimeout,
)
from benchmarks.runner.adapters.loopflow import _build_submission


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DOCKER_ISOLATION_TESTS") != "1",
    reason="set RUN_DOCKER_ISOLATION_TESTS=1 to run the Docker isolation probe",
)

ROOT = Path(__file__).parents[2]


def _directories(tmp_path):
    run_root = tmp_path / "run"
    directories = (run_root / "input", run_root / "workspace", run_root / "output")
    for directory in directories:
        directory.mkdir(parents=True)
    return run_root, *directories


def test_offline_sandbox_rejects_control_plane_and_write_probes(tmp_path):
    run_root, input_dir, workspace, output_dir = _directories(tmp_path)
    control_dir = tmp_path / "control" / "oracle"
    control_dir.mkdir(parents=True)
    (input_dir / "paper.md").write_text("public input")
    secret = control_dir / "rubric.yaml"
    secret.write_text("private oracle")
    adjacent_oracle = ROOT / "benchmarks" / "entries" / "bench-002" / "oracle" / "rubric.yaml"
    git_config = ROOT / ".git" / "config"

    probe = f"""
set -eu
test "$(id -u)" != "0"
test -r /input/paper.md
test ! -e /control/oracle/rubric.yaml
test ! -e /.git/config
test ! -e /var/run/docker.sock
test ! -e {shlex.quote(str(secret))}
test ! -e {shlex.quote(str(adjacent_oracle))}
test ! -e {shlex.quote(str(git_config))}
test "$(ls /sys/class/net)" = "lo"
if touch /input/forbidden 2>/dev/null; then exit 11; fi
if touch /root-forbidden 2>/dev/null; then exit 12; fi
printf workspace-ok > /workspace/probe.txt
printf output-ok > /output/probe.txt
"""
    sandbox = DockerSandbox(SandboxConfig(
        image=os.environ.get("ISOLATION_PROBE_IMAGE", "alpine:3"),
        profile="offline",
        timeout_seconds=30,
        memory="256m",
        cpus="1",
        pids_limit=32,
    ))

    result = sandbox.run(SandboxRequest(
        command=["sh", "-c", probe],
        input_dir=input_dir,
        workspace=workspace,
        output_dir=output_dir,
    ))

    assert result.returncode == 0, result.stderr
    assert (workspace / "probe.txt").read_text() == "workspace-ok"
    assert (output_dir / "probe.txt").read_text() == "output-ok"
    assert not (input_dir / "forbidden").exists()


def test_discovery_profile_enables_container_network_without_host_runtime(tmp_path):
    _, input_dir, workspace, output_dir = _directories(tmp_path)
    (input_dir / "paper.md").write_text("public input")
    sandbox = DockerSandbox(SandboxConfig(
        image=os.environ.get("ISOLATION_PROBE_IMAGE", "alpine:3"),
        profile="discovery",
        timeout_seconds=30,
        memory="256m",
        cpus="1",
        pids_limit=32,
    ))

    result = sandbox.run(SandboxRequest(
        command=["sh", "-c", "test -e /sys/class/net/eth0; test ! -e /var/run/docker.sock"],
        input_dir=input_dir,
        workspace=workspace,
        output_dir=output_dir,
    ))

    assert result.returncode == 0, result.stderr


def test_timeout_removes_the_container(tmp_path, monkeypatch):
    _, input_dir, workspace, output_dir = _directories(tmp_path)
    container_name = "bio-reproducer-timeout-probe"
    monkeypatch.setattr(
        "benchmarks.runner.sandbox.uuid.uuid4",
        lambda: SimpleNamespace(hex="timeout-probe"),
    )
    sandbox = DockerSandbox(SandboxConfig(
        image=os.environ.get("ISOLATION_PROBE_IMAGE", "alpine:3"),
        profile="offline",
        timeout_seconds=1,
        memory="256m",
        cpus="1",
        pids_limit=32,
    ))

    with pytest.raises(SandboxTimeout):
        sandbox.run(SandboxRequest(
            command=["sleep", "30"],
            input_dir=input_dir,
            workspace=workspace,
            output_dir=output_dir,
        ))

    remaining = subprocess.run(
        [
            "docker", "ps", "-a", "--filter", f"name={container_name}",
            "--format", "{{.Names}}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert remaining.stdout.strip() == ""


def test_submission_collector_reads_only_sandbox_output(tmp_path):
    run_root, input_dir, workspace, output_dir = _directories(tmp_path)
    (input_dir / "paper.md").write_text("public input")
    sandbox = DockerSandbox(SandboxConfig(
        image=os.environ.get("ISOLATION_PROBE_IMAGE", "alpine:3"),
        profile="offline",
        timeout_seconds=30,
        memory="256m",
        cpus="1",
        pids_limit=32,
    ))
    script = """
set -eu
mkdir -p /output/05_run/results /output/05_run/figures
printf 'gene,log2FoldChange,padj\nGene_A,2.5,0.001\n' > /output/05_run/results/deseq2_results.csv
printf 'analysis complete\n' > /output/05_run/results/analysis.log
"""

    result = sandbox.run(SandboxRequest(
        command=["sh", "-c", script],
        input_dir=input_dir,
        workspace=workspace,
        output_dir=output_dir,
    ))
    submission = _build_submission(
        {"id": "bench-001"},
        run_root,
        output_dir,
        duration=1,
        sandbox={"runtime": "docker", "profile": "offline", "image": sandbox.config.image},
    )

    assert result.returncode == 0, result.stderr
    assert {artifact["role"] for artifact in submission["artifacts"]} == {
        "result_table",
        "analysis_log",
    }
    assert submission["execution"]["sandbox"]["profile"] == "offline"
