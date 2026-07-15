"""Adapter: map benchmark entry → loopflow bio-reproducer call.

This is the ONLY engine-coupled module in the benchmark system.
"""


def run(entry_path: str) -> dict:
    """Run a benchmark entry via loopflow bio-reproducer.

    Args:
        entry_path: Path to benchmark entry directory (e.g., benchmarks/entries/bench-001)

    Returns:
        Standardized result.json dict.
    """
    # TODO: implement
    # 1. Read metadata.yaml + expected.yaml
    # 2. Construct loop run bio-reproducer args
    # 3. Execute loopflow
    # 4. Extract verdict, score, stages from repro-data/
    # 5. Return result.json
    pass