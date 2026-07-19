"""Benchmark runner CLI.

Usage:
    bench-run run --entry bench-001 --runs 5
    bench-run eval --entry bench-001
    bench-run report [--output summary.json]
"""

import argparse
import json
import sys
from pathlib import Path

BENCHMARKS_DIR = Path(__file__).parent.parent / "entries"


def cmd_run(args: argparse.Namespace) -> None:
    """Run a benchmark entry N times."""
    from .runner import run_entry

    entry_path = BENCHMARKS_DIR / args.entry
    if not entry_path.exists():
        print(f"ERROR: Benchmark entry not found: {entry_path}", file=sys.stderr)
        sys.exit(2)

    results = run_entry(str(entry_path), runs=args.runs, output_dir=args.output)
    print(f"Completed {len(results)} runs for {args.entry}")


def cmd_eval(args: argparse.Namespace) -> None:
    """Evaluate benchmark results against expected.yaml."""
    from .evaluator import evaluate

    entry_path = BENCHMARKS_DIR / args.entry
    expected_path = entry_path / "expected.yaml"
    if not expected_path.exists():
        print(f"ERROR: expected.yaml not found for {args.entry}", file=sys.stderr)
        sys.exit(2)

    import yaml
    with open(expected_path) as f:
        expected = yaml.safe_load(f)

    results_dir = Path(args.results_dir or f"benchmarks/results/{args.entry}")
    results = []
    if results_dir.exists():
        for rf in sorted(results_dir.glob("run_*/result.json")):
            with open(rf) as f:
                results.append(json.load(f))

    if not results:
        print(f"ERROR: No result.json files found in {results_dir}", file=sys.stderr)
        sys.exit(2)

    evaluation = evaluate(expected, results, str(results_dir))

    # Write evaluation to file
    eval_path = results_dir / "evaluation.json"
    with open(eval_path, "w") as f:
        json.dump(evaluation, f, indent=2)

    print(json.dumps(evaluation, indent=2))
    print(f"\nEvaluation written to {eval_path}")


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

    # bench-run run
    run_parser = subparsers.add_parser("run", help="Run a benchmark entry")
    run_parser.add_argument("--entry", required=True, help="Benchmark entry ID (e.g., bench-001)")
    run_parser.add_argument("--runs", type=int, default=5, help="Number of runs (default: 5)")
    run_parser.add_argument("--output", default=None, help="Output directory for results")

    # bench-run eval
    eval_parser = subparsers.add_parser("eval", help="Evaluate benchmark results")
    eval_parser.add_argument("--entry", required=True, help="Benchmark entry ID")
    eval_parser.add_argument("--results-dir", default=None, help="Results directory path")

    # bench-run report
    report_parser = subparsers.add_parser("report", help="Generate summary report")
    report_parser.add_argument(
        "--output", default="benchmarks/results/summary.json",
        help="Output path for summary.json (default: benchmarks/results/summary.json)",
    )
    report_parser.add_argument("--results-dir", default=None, help="Results directory path")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "eval":
        cmd_eval(args)
    elif args.command == "report":
        cmd_report(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()