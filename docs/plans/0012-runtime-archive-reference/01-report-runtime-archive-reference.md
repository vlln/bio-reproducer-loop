---
title: Report 012 - Runtime Archive Reference
description: Record tagged archive validation, fresh-daemon load/run evidence, gates and cleanup.
type: report
status: complete
created: 2026-07-27T00:00:00Z
---

# Conclusion

Plan 012 completed successfully. It fixes the Plan 011 runtime identity defect without rerunning a
benchmark. The runtime archive now carries a fixed internal tag, the artifact builder parses and
validates the archive's tag/config binding, and a fresh Docker 29 daemon loaded and executed the
runtime through that tag.

# Changes

`build-runtime.sh` now saves the configured tag rather than the build-host image ID and emits
`.image-ref` alongside `.image-id` and `.sha256`. System artifacts use schema `1.1` and record:

```text
runtime.format: docker-archive
runtime.reference: bio-reproducer-runtime:system
runtime.image: sha256:b5ac039a6fb22a82ceea2a299904dc718d48c396adee1dbe20bf0df3b0d5aaed
runtime.archive_sha256: 9589a2da530197026e72aaccf22c0bb7c4bcf1b9ff3a14510a7580ee1fd6c703
system_artifact_digest: sha256:175691d15c920a77c1cc6090b286f9ca4c42e70e50cde6c4f969bb8ac2daa048
```

The validator structurally parses `manifest.json`, requires exactly one `RepoTags` entry equal to
the declared reference, and requires its config path to match the declared build image ID. It
rejects digest-only references, missing/multiple tags, mismatched tags, malformed archives, and
mismatched config identities. The launcher runs the validated tag after `docker load`; it never
uses the build-host ID as the guest locator.

# Gates

All execution was on `gs@172.16.209.237` from source archive SHA
`851d3db275a21d072076ad4c3be9b4d625c35a42b475b3105de757b6af0cc89a`:

```text
ordinary tests: 106 passed, 4 skipped
Docker opt-in tests: 110 passed
make lint: PASS
bundle validation: bench-001/002/004/005/006/100 VALID
artifact files: 54
```

The fresh-daemon probe used a new Docker 29 dind daemon and reported:

```text
Loaded image: bio-reproducer-runtime:system
guest_reference=bio-reproducer-runtime:system
guest_id=sha256:b5ac039a6fb22a82ceea2a299904dc718d48c396adee1dbe20bf0df3b0d5aaed
2.1.126 (Claude Code)
mip 0.2.0
Nextflow 26.04.6
fresh_daemon_runtime_probe=PASS
```

After merging `develop` at `e044128e4332901c74bbce4335b4c88c2e0e4916`, the MR gate was rerun
against the integrated tree on Python 3.12 and Docker 29.4.0:

```text
deterministic tests: 113 passed, 4 skipped
explicit Docker isolation probes: 4 passed
make lint: PASS
git diff --check: PASS
```

The first local Docker attempt timed out while the engine tried to pull `alpine:3`. The image was
then obtained through a reachable mirror, verified as
`alpine@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b`,
and retagged locally as `alpine:3`; rerunning the failed Docker layer passed without changing tests.

# Acceptance

| ID | Status | Evidence |
|----|--------|----------|
| AR-001 | PASS | Archive contains exactly the declared tag and expected config identity |
| AR-002 | PASS | 15 targeted tests cover malformed/missing/mismatched bindings |
| AR-003 | PASS | Schema 1.1 manifest records archive digest, build ID and runtime reference |
| AR-004 | PASS | Launcher uses validated tag after `docker load` |
| AR-005 | PASS | Fresh Docker 29 daemon load/run probe passed |
| AR-006 | PASS | Original remote gates and post-`develop` MR gates passed |
| AR-007 | PASS | No benchmark, baseline, historical submission or home project changes |

# Cleanup

The Plan-specific root, source archives, runtime image, dind image, containers and QEMU processes
were removed:

```text
/tmp/bio-reproducer-plan011-ea43382: absent
source archives/background scripts: absent
bio-reproducer-runtime:system: absent
docker:29-dind: absent
matching containers: 0
qemu processes: 0
remote home status hash before/after: c3797cbac763f0ed8b1387951572efe771964ec2fc6832c00afb28ddce98b4ae
```

# Boundary

This Plan did not run `bench-001` or any other benchmark. A separate formal smoke may now be
planned using a freshly built system artifact with the tagged runtime reference. Plan 009 and Plan
011 BLOCKED submissions remain unchanged.
