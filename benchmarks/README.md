# bio-reproducer Benchmark Suite

The benchmark suite is the engine-neutral L3-L5 evaluation surface. It does not
contain the project's L1/L2 unit, contract, or internal LLM evaluations.

## Entry layout

Release-ready `entries/bench-NNN/` directories contain exactly:

```text
bundle.yaml     runner-only input inventory and provenance lock
input/          material exposed to the system under test
oracle/         private scientific claims and evaluation rubric
metadata.yaml   entry discovery and version metadata
```

`oracle/claims.yaml` records scientific facts and known input conditions.
`oracle/rubric.yaml` owns evidence selection, comparison rules, tolerances,
weights, and verdict thresholds. The system under test never receives `oracle/`.

The InputBundle contract is active in ADR-0007 and Interface 0001. The five
constructed L3 entries pass the automated bundle gate. Bench-003 remains invalid
until it is rebuilt from real L4 materials. All entries remain internal
development inputs until their scientific review and release gate are complete.

## Results and baselines

- `results/` contains raw submissions and evaluator outputs from local runs. It is
  gitignored because these files are execution observations, not benchmark truth.
- `baselines/` is reserved for reviewed aggregate observations created after an
  entry, its oracle, and the evaluation protocol are frozen for a release.
- Internal-development runs remain in gitignored `results/` or an implementation
  report. They are not tracked as historical baselines.

A single valid submission can be evaluated. Repeated runs are used when
establishing a stochastic system baseline after benchmark freeze; the protocol
does not require every ad hoc benchmark invocation to run five times.

## Commands

```bash
bench-run validate-entry --entry bench-001
make bench-validate
bench-run run --entry bench-001 --runs 1
bench-run submit --entry bench-001
bench-run eval --entry bench-001
bench-run report
```

`submit` exists to import preserved protocol v1 run artifacts without rerunning
the system. `eval` always writes the evaluator-owned protocol v2 `result.json`.
