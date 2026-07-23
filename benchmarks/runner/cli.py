"""Benchmark runner CLI.

Usage:
    bench-run validate-entry --entry bench-001
    bench-run run --entry bench-001 --runs 5
    bench-run submit --entry bench-001
    bench-run eval --entry bench-001
    bench-run report [--output summary.json]
"""

import argparse
import json
import os
import sys
from pathlib import Path

BENCHMARKS_DIR = Path(__file__).parent.parent / "entries"


def _sandbox_pass_env_default() -> list[str]:
    return [
        item.strip()
        for item in os.environ.get("BIO_REPRODUCER_SANDBOX_PASS_ENV", "").split(",")
        if item.strip()
    ]


def cmd_validate_entry(args: argparse.Namespace) -> None:
    """Validate an entry's trusted bundle lock and runtime input."""
    from .bundle_validator import BundleValidationError, validate_entry

    entry_path = BENCHMARKS_DIR / args.entry
    try:
        bundle = validate_entry(entry_path)
    except BundleValidationError as exc:
        print(f"ERROR [{exc.code}]: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"VALID: {bundle['entry_id']} ({bundle['level']})")


def cmd_run(args: argparse.Namespace) -> None:
    """Run a benchmark entry N times."""
    from .runner import run_entry

    entry_path = BENCHMARKS_DIR / args.entry
    if not entry_path.exists():
        print(f"ERROR: Benchmark entry not found: {entry_path}", file=sys.stderr)
        sys.exit(2)

    from .bundle_validator import BundleValidationError
    from .execution import ExecutionError

    try:
        executor = _build_executor(args)
        results = run_entry(
            str(entry_path),
            runs=args.runs,
            output_dir=args.output,
            sandbox=executor,
        )
    except BundleValidationError as exc:
        print(f"ERROR [{exc.code}]: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    except ExecutionError as exc:
        code = {
            "WorkerUnavailable": "WORKER_UNAVAILABLE",
            "WorkerIntegrityError": "INVALID_EXECUTION_ENVIRONMENT",
        }.get(type(exc).__name__, "EXECUTION_BLOCKED")
        print(f"ERROR [{code}]: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    except ValueError as exc:
        print(f"ERROR [INVALID_EXECUTION_ENVIRONMENT]: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"Completed {len(results)} runs for {args.entry}")


def _build_executor(args: argparse.Namespace):
    if args.backend == "docker-validation":
        from .sandbox import DockerSandbox, SandboxConfig

        return DockerSandbox(
            SandboxConfig(
                image=args.sandbox_image,
                profile=args.sandbox_profile,
                timeout_seconds=args.timeout,
                pass_env=tuple(args.pass_env or _sandbox_pass_env_default()),
            )
        )

    from .worker import QemuWorker, VmWorkerConfig, WorkerUnavailable

    required = {
        "worker image": args.worker_image,
        "worker SHA256": args.worker_sha256,
        "system directory": args.system_dir,
        "system SHA256": args.system_sha256,
        "worker SSH key": args.worker_ssh_key,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise WorkerUnavailable(
            f"Formal VM configuration is incomplete: {', '.join(missing)}"
        )
    return QemuWorker(
        VmWorkerConfig(
            worker_image=Path(args.worker_image),
            worker_sha256=args.worker_sha256,
            system_dir=Path(args.system_dir),
            system_sha256=args.system_sha256,
            ssh_key=Path(args.worker_ssh_key),
            network_policy=args.network_policy,
            timeout_seconds=args.timeout,
            boot_timeout_seconds=args.boot_timeout,
            pass_env=tuple(args.pass_env or ()),
        )
    )


def cmd_eval(args: argparse.Namespace) -> None:
    """Evaluate protocol v2 submissions with the private oracle."""
    entry_path = BENCHMARKS_DIR / args.entry
    metadata_path = entry_path / "metadata.yaml"
    if not metadata_path.exists():
        print(f"ERROR: metadata.yaml not found for {args.entry}", file=sys.stderr)
        sys.exit(2)
    results_dir = Path(args.results_dir or f"benchmarks/results/{args.entry}")
    _evaluate_submissions(entry_path, results_dir)


def cmd_submit(args: argparse.Namespace) -> None:
    """Create v2 submissions for already completed run directories."""
    from .adapters.loopflow import build_submission_from_existing

    entry_path = BENCHMARKS_DIR / args.entry
    if not entry_path.exists():
        print(f"ERROR: Benchmark entry not found: {entry_path}", file=sys.stderr)
        sys.exit(2)
    results_dir = Path(args.results_dir or f"benchmarks/results/{args.entry}")
    run_dirs = sorted(path for path in results_dir.glob("run_*") if (path / "repro-data").is_dir())
    if not run_dirs:
        print(f"ERROR: No completed run directories found in {results_dir}", file=sys.stderr)
        sys.exit(2)

    for run_dir in run_dirs:
        submission = build_submission_from_existing(entry_path, run_dir)
        submission_path = run_dir / "submission.json"
        submission_path.write_text(json.dumps(submission, indent=2))
        print(f"Wrote {submission_path}")


def cmd_release_check(args: argparse.Namespace) -> None:
    """Require formal VM provenance before a submission can be released."""
    from .release_gate import ReleaseGateError, require_formal_submission

    submission_path = Path(args.submission)
    try:
        submission = json.loads(submission_path.read_text())
        require_formal_submission(submission)
    except (OSError, json.JSONDecodeError, ReleaseGateError) as exc:
        print(f"ERROR [RELEASE_GATE]: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"FORMAL: {submission_path}")


def _named_paths(values: list[str]) -> dict[str, Path]:
    parsed = {}
    for value in values:
        name, separator, path = value.partition("=")
        if not separator or not name or not path or name in parsed:
            raise ValueError(f"Invalid or duplicate NAME=PATH value: {value}")
        parsed[name] = Path(path)
    return parsed


def cmd_build_system(args: argparse.Namespace) -> None:
    """Build an opaque system artifact from explicit pinned inputs."""
    from .system_artifact import build_system_artifact
    from .worker import sha256_tree

    manifest = build_system_artifact(
        Path(args.output),
        loop_dir=Path(args.loop_dir),
        runtime_oci=Path(args.runtime_oci),
        runtime_image=args.runtime_image,
        skills=_named_paths(args.skill),
        provenance={
            "repository_commit": args.repository_commit,
            "loopflow_commit": args.loopflow_commit,
            "loopflow_version": args.loopflow_version,
        },
        required_secrets=tuple(args.required_secret),
        skills_lock=Path(args.skills_lock) if args.skills_lock else None,
    )
    print(json.dumps({
        "artifact": str(Path(args.output).resolve()),
        "digest": f"sha256:{sha256_tree(Path(args.output))}",
        "manifest": manifest,
    }, indent=2))


def cmd_validate_system(args: argparse.Namespace) -> None:
    """Validate an already materialized opaque system artifact."""
    from .system_artifact import validate_system_artifact
    from .worker import sha256_tree

    root = Path(args.system_dir)
    manifest = validate_system_artifact(root)
    print(json.dumps({
        "artifact": str(root.resolve()),
        "digest": f"sha256:{sha256_tree(root)}",
        "manifest": manifest,
    }, indent=2))


def _evaluate_submissions(entry_path: Path, results_dir: Path) -> None:
    from .independent_evaluator import (
        EvaluationError,
        evaluate_submission,
        summarize_evaluations,
    )

    import yaml

    submission_files = sorted(results_dir.glob("run_*/submission.json"))
    if not submission_files:
        print(f"ERROR: No submission.json files found in {results_dir}", file=sys.stderr)
        sys.exit(2)

    results = []
    for submission_file in submission_files:
        try:
            result = evaluate_submission(entry_path, submission_file)
        except EvaluationError as exc:
            print(f"ERROR [{exc.code}]: {exc}", file=sys.stderr)
            sys.exit(2)
        result_path = submission_file.parent / "result.json"
        _preserve_legacy_result(result_path)
        result_path.write_text(json.dumps(result, indent=2))
        results.append(result)

    rubric = yaml.safe_load((entry_path / "oracle" / "rubric.yaml").read_text())
    evaluation = summarize_evaluations(results, rubric)
    eval_path = results_dir / "evaluation.json"
    eval_path.write_text(json.dumps(evaluation, indent=2))
    print(json.dumps(evaluation, indent=2))
    print(f"\nEvaluation written to {eval_path}")


def _preserve_legacy_result(result_path: Path) -> None:
    """Keep pre-v2 system-scored results when evaluator ownership begins."""
    if not result_path.is_file():
        return
    try:
        previous = json.loads(result_path.read_text())
    except json.JSONDecodeError:
        previous = {}
    if "provenance" in previous:
        return
    legacy_path = result_path.with_name("legacy-result.json")
    if not legacy_path.exists():
        result_path.replace(legacy_path)


def cmd_report(args: argparse.Namespace) -> None:
    """Generate summary report from all evaluation results."""
    from .reporter import generate_summary

    results_dir = Path(args.results_dir or "benchmarks/results")
    results_by_entry = {}

    if results_dir.exists():
        for entry_dir in results_dir.iterdir():
            if entry_dir.is_dir():
                eval_path = entry_dir / "evaluation.json"
                if eval_path.exists():
                    with open(eval_path) as f:
                        results_by_entry[entry_dir.name] = json.load(f)

    if not results_by_entry:
        print("No evaluation results found.", file=sys.stderr)
        sys.exit(0)

    summary = generate_summary(results_by_entry)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary written to {output_path}")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bench-run",
        description="Benchmark runner CLI for bio-reproducer",
    )
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser(
        "validate-entry", help="Validate an entry bundle without running it"
    )
    validate_parser.add_argument("--entry", required=True, help="Benchmark entry ID")

    # bench-run run
    run_parser = subparsers.add_parser("run", help="Run a benchmark entry")
    run_parser.add_argument("--entry", required=True, help="Benchmark entry ID (e.g., bench-001)")
    run_parser.add_argument("--runs", type=int, default=5, help="Number of runs (default: 5)")
    run_parser.add_argument("--output", default=None, help="Output directory for results")
    run_parser.add_argument(
        "--backend",
        choices=("formal-vm", "docker-validation"),
        default="formal-vm",
        help="Execution boundary (default: formal-vm; Docker is validation-only)",
    )
    run_parser.add_argument(
        "--worker-image",
        default=os.environ.get("BIO_REPRODUCER_WORKER_IMAGE", ""),
        help="Pinned qcow2 worker base for formal VM runs",
    )
    run_parser.add_argument(
        "--worker-sha256",
        default=os.environ.get("BIO_REPRODUCER_WORKER_SHA256", ""),
        help="Expected worker image SHA256",
    )
    run_parser.add_argument(
        "--system-dir",
        default=os.environ.get("BIO_REPRODUCER_SYSTEM_DIR", ""),
        help="Opaque system artifact directory attached read-only to the guest",
    )
    run_parser.add_argument(
        "--system-sha256",
        default=os.environ.get("BIO_REPRODUCER_SYSTEM_SHA256", ""),
        help="Expected system artifact tree SHA256",
    )
    run_parser.add_argument(
        "--worker-ssh-key",
        default=os.environ.get("BIO_REPRODUCER_WORKER_SSH_KEY", ""),
        help="Runner control key provisioned in the worker image",
    )
    run_parser.add_argument(
        "--network-policy",
        choices=("offline", "controlled-egress"),
        default=os.environ.get("BIO_REPRODUCER_WORKER_NETWORK_POLICY", "offline"),
        help="Formal guest egress policy",
    )
    run_parser.add_argument(
        "--boot-timeout",
        type=int,
        default=int(os.environ.get("BIO_REPRODUCER_WORKER_BOOT_TIMEOUT", "60")),
        help="Guest readiness deadline in seconds",
    )
    run_parser.add_argument(
        "--sandbox-image",
        default=os.environ.get("BIO_REPRODUCER_SANDBOX_IMAGE", ""),
        help="Container image containing the system under test",
    )
    run_parser.add_argument(
        "--sandbox-profile",
        choices=("offline", "discovery", "tool-runtime"),
        default=os.environ.get("BIO_REPRODUCER_SANDBOX_PROFILE", "offline"),
        help="Sandbox network/runtime profile",
    )
    run_parser.add_argument(
        "--timeout",
        type=int,
        default=int(
            os.environ.get(
                "BIO_REPRODUCER_WORKER_TIMEOUT",
                os.environ.get("BIO_REPRODUCER_SANDBOX_TIMEOUT", "3600"),
            )
        ),
        help="Per-run execution deadline in seconds",
    )
    run_parser.add_argument(
        "--pass-env",
        action="append",
        default=None,
        help="Explicit host environment variable name to pass into the sandbox",
    )

    # bench-run eval
    eval_parser = subparsers.add_parser("eval", help="Evaluate benchmark results")
    eval_parser.add_argument("--entry", required=True, help="Benchmark entry ID")
    eval_parser.add_argument("--results-dir", default=None, help="Results directory path")

    # bench-run submit
    submit_parser = subparsers.add_parser(
        "submit", help="Build submissions from existing loopflow results"
    )
    submit_parser.add_argument("--entry", required=True, help="Benchmark entry ID")
    submit_parser.add_argument("--results-dir", default=None, help="Results directory path")

    release_parser = subparsers.add_parser(
        "release-check", help="Verify that a submission may enter a release baseline"
    )
    release_parser.add_argument("--submission", required=True, help="submission.json path")

    build_system_parser = subparsers.add_parser(
        "build-system", help="Build an opaque bio-reproducer system artifact"
    )
    build_system_parser.add_argument("--output", required=True)
    build_system_parser.add_argument("--loop-dir", default="loops/bio-reproducer")
    build_system_parser.add_argument("--runtime-oci", required=True)
    build_system_parser.add_argument("--runtime-image", required=True)
    build_system_parser.add_argument(
        "--skill", action="append", default=[], metavar="NAME=PATH"
    )
    build_system_parser.add_argument("--repository-commit", required=True)
    build_system_parser.add_argument("--loopflow-commit", required=True)
    build_system_parser.add_argument("--loopflow-version", required=True)
    build_system_parser.add_argument("--skills-lock", default=None)
    build_system_parser.add_argument(
        "--required-secret", action="append", default=[]
    )

    validate_system_parser = subparsers.add_parser(
        "validate-system", help="Validate an opaque system artifact"
    )
    validate_system_parser.add_argument("--system-dir", required=True)

    # bench-run report
    report_parser = subparsers.add_parser("report", help="Generate summary report")
    report_parser.add_argument(
        "--output", default="benchmarks/results/summary.json",
        help="Output path for summary.json (default: benchmarks/results/summary.json)",
    )
    report_parser.add_argument("--results-dir", default=None, help="Results directory path")

    args = parser.parse_args()

    if args.command == "validate-entry":
        cmd_validate_entry(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "submit":
        cmd_submit(args)
    elif args.command == "eval":
        cmd_eval(args)
    elif args.command == "release-check":
        cmd_release_check(args)
    elif args.command == "build-system":
        cmd_build_system(args)
    elif args.command == "validate-system":
        cmd_validate_system(args)
    elif args.command == "report":
        cmd_report(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
