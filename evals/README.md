# Internal Evaluations

`evals/` measures real-LLM behavior inside bio-reproducer. It is implementation-coupled
and is not part of the public benchmark protocol.

## Coverage Unit

The coverage unit is a capability or failure mode, not a benchmark entry. A case may
reuse one benchmark InputBundle as representative input, but adding a benchmark does
not imply running every Phase against it. New cases are added only for a new behavior
branch or a demonstrated regression.

`coverage.yaml` maps capabilities to cases and lists known gaps. Each `case.yaml`
declares its Phase, representative input, upstream fixture state and behavioral checks.

## Sampling

Sampling is selected by `profiles.yaml`:

| Profile | Runs | Use |
|---------|------|-----|
| `smoke` | 1 | Fast execution and evidence check |
| `regression` | 3 | Routine Prompt/Phase regression |
| `release` | 5 | Selected release-critical stability checks |

Case code must not hardcode repetition. Run a suite with:

```bash
make eval-component EVAL_PROFILE=regression
make eval-handoff EVAL_PROFILE=release
```

Pytest is the execution transport. It writes attempt outcomes and environment metadata
to gitignored `evals/results/`; a passing single attempt is not itself a capability
baseline.

## Asset Meaning

- `cases/`: tracked evaluation definitions and behavior checks.
- `fixtures/`: tracked constructed or curated upstream Phase states.
- `runner/`: execution, profile loading and result recording.
- `schemas/`: case and result protocol schemas.
- `results/`: untracked raw observations from real-LLM runs.
- `baselines/`: reviewed, tracked distribution summaries for pinned configurations.

Fixtures are inputs, never expected full-output truth. Internal evals do not use a
multi-purpose `golden` or compare complete output text against an exemplar.
