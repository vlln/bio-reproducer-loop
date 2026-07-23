"""Opt-in real KVM smoke for the minimal worker contract."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def main() -> None:
    from benchmarks.runner.execution import ExecutionRequest
    from benchmarks.runner.worker import QemuWorker, VmWorkerConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-image", required=True, type=Path)
    parser.add_argument("--worker-sha256", required=True)
    parser.add_argument("--system-dir", required=True, type=Path)
    parser.add_argument("--system-sha256", required=True)
    parser.add_argument("--ssh-key", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--mode", choices=("success", "timeout"), default="success")
    args = parser.parse_args()

    if args.run_root.exists():
        shutil.rmtree(args.run_root)
    input_dir = args.run_root / "input"
    workspace = args.run_root / "workspace"
    output_dir = args.run_root / "output"
    for directory in (input_dir, workspace, output_dir):
        directory.mkdir(parents=True)
    (input_dir / "public.txt").write_text("public benchmark input\n")

    worker = QemuWorker(
        VmWorkerConfig(
            worker_image=args.worker_image,
            worker_sha256=args.worker_sha256,
            system_dir=args.system_dir,
            system_sha256=args.system_sha256,
            ssh_key=args.ssh_key,
            timeout_seconds=3 if args.mode == "timeout" else 120,
            boot_timeout_seconds=60,
            memory_mb=4096,
            cpus=4,
            adapter="plan008-smoke@1",
        )
    )
    request = ExecutionRequest(
        command=[f"/system/run-{'timeout' if args.mode == 'timeout' else 'smoke'}"],
        input_dir=input_dir,
        workspace=workspace,
        output_dir=output_dir,
    )
    if args.mode == "timeout":
        from benchmarks.runner.worker import WorkerTimeout

        try:
            worker.run(request)
        except WorkerTimeout:
            envelope = worker.execution_envelope()
            if envelope["teardown"]["status"] != "completed":
                raise SystemExit("timeout did not complete the teardown audit")
            print("vm_worker_timeout:PASS")
            print(json.dumps(envelope, indent=2, sort_keys=True))
            return
        raise SystemExit("timeout smoke unexpectedly completed")

    result = worker.run(request)
    if result.returncode != 0:
        raise SystemExit(
            f"smoke system failed ({result.returncode}):\n{result.stdout}\n{result.stderr}"
        )
    artifact = output_dir / "nested-artifact.txt"
    if artifact.read_text() != "nested-docker-artifact-plan008\n":
        raise SystemExit("collected artifact content does not match guest output")
    envelope = worker.execution_envelope()
    if envelope.get("boot_seconds", 60) >= 60:
        raise SystemExit(f"cold boot exceeded 60 seconds: {envelope.get('boot_seconds')}")
    print(result.stdout.strip())
    print(json.dumps(envelope, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
