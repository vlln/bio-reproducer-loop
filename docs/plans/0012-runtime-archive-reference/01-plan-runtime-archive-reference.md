---
title: Plan 012 - Runtime Archive Reference
description: Replace build-host image IDs with a validated Docker archive tag for disposable-VM runtime startup.
type: plan
status: done
created: 2026-07-27T00:00:00Z
---

# Context

Plan 011 proved fixed-worker readiness but its only formal `bench-001` run stopped before loopflow.
The runtime archive had `RepoTags: null`; the build host identified the image as config ID
`b5ac...`, while a fresh Docker 29/containerd store registered the loaded image as `aac9...`.
The launcher incorrectly treated a build-host image ID as a portable guest locator.

# Request

Export the runtime archive with an explicit internal tag, validate that the archive binds that tag
to the expected config identity, record both provenance and runtime reference in the system
artifact, and launch the loaded image by tag. Add deterministic rejection tests plus a real
fresh-daemon load/run probe on `gs`.

# Constraints

- Archive SHA256 and system artifact digest remain the content-integrity authorities; the tag is
  only a locator inside a fresh disposable VM.
- The builder must parse archive metadata structurally and reject a missing, ambiguous, malformed,
  or mismatched tag/config binding.
- No benchmark may run until unit, Docker, archive, artifact, and fresh-daemon load/run gates pass.
- Plan 009 and Plan 011 submissions remain immutable historical observations.
- All tests, Docker builds and real probes run on `gs`; local execution is limited to documents,
  source edits and Git checks.
- Remote work uses a Plan-specific `/tmp` root and background-task for long operations. Do not
  modify `~/bio-reproducer`, build a baseline, run other entries, or push without explicit request.

# Steps

1. Add failing tests for tagged archive export, archive metadata validation, manifest provenance,
   launcher reference use, and invalid reference rejection.
2. Change runtime export to save the configured tag and emit its reference beside image ID/digest.
3. Extend the artifact builder and CLI with an explicit validated runtime reference.
4. Run deterministic gates and a fresh-daemon `docker load` plus runtime command probe on `gs`.
5. Only after those gates pass, propose a new one-run formal smoke; do not consume it implicitly.
6. Record evidence, clean Plan-specific remote assets, and complete the Report.

# Acceptance

| ID | Condition |
|----|-----------|
| AR-001 | Runtime archive contains exactly the declared tag and expected config identity |
| AR-002 | Builder rejects missing/malformed/mismatched runtime reference or archive metadata |
| AR-003 | Manifest records archive digest, build identity and guest runtime reference |
| AR-004 | Launcher loads the pinned archive and runs only the validated tag |
| AR-005 | Fresh remote daemon loads the archive and executes runtime self-check commands |
| AR-006 | Existing deterministic, Docker, lint and bundle gates remain green |
| AR-007 | No benchmark, baseline, historical submission, remote home project or unrelated asset changes |
