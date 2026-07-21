# Benchmark Baselines

This directory is intentionally empty during internal benchmark development.

A tracked baseline may be established only after all of the following are true:

1. The InputBundle and its provenance have passed human review.
2. The entry scope, oracle, and rubric are frozen.
3. The runner, adapter, and evaluator protocol are stable.
4. The benchmark version is a release candidate or published release.
5. The configured system is rerun for the required sample count on the frozen entry.

Development runs belong in the gitignored `benchmarks/results/` directory or in
an implementation report. They are observations, not release baselines. A
baseline is never benchmark truth and must identify the system, model, prompt,
tools, platform, benchmark version, and oracle version that produced it.
