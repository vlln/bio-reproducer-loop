"""claroai2bench CLI (Interface 0002)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import ConversionError, convert_snapshot


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(prog="claroai2bench",
                                     description="Convert ClaroAI-Bench tasks to standard entries (L5, no paper fulltext).")
    parser.add_argument("--source", required=True, help="claroai-bench snapshot dir (containing papers/)")
    parser.add_argument("--output", required=True, help="entries output dir")
    parser.add_argument("--start-id", type=int, default=200, help="first entry number (default 200)")
    parser.add_argument("--snapshot", default=None, help="explicit snapshot ref (default: git HEAD or dir)")
    parser.add_argument("--dry-run", action="store_true", help="only plan, do not write")
    parser.add_argument("--check-existing", action="store_true", help="fail on existing entry dirs")
    args = parser.parse_args(argv)

    try:
        if args.dry_run:
            papers = sorted((Path(args.source) / "papers").glob("paper_*"))
            print(f"[dry-run] would convert {len(papers)} papers -> {args.output} "
                  f"(bench-{args.start_id:03d}..bench-{args.start_id + len(papers) - 1:03d})")
            return {"status": "CONVERT_OK", "mapping": {}}
        result = convert_snapshot(Path(args.source), Path(args.output),
                                  start_id=args.start_id, snapshot_ref=args.snapshot)
        for paper, entry_id in sorted(result["mapping"].items()):
            print(f"  {paper} -> {entry_id}")
        if result["failures"]:
            print(f"WARN: {len(result['failures'])} papers failed:", file=sys.stderr)
            for f in result["failures"]:
                print(f"  {f['paper']} ({f['entry_id']}): {f['reason']}", file=sys.stderr)
        print(f"{result['status']}: {len(result['mapping'])} entries -> {args.output}")
        if result["status"] == "CONVERT_PARTIAL":
            sys.exit(1)
        return result
    except ConversionError as exc:
        print(f"ERROR [{exc.code}]: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
