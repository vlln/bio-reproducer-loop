# Bio-Reproducer System Artifact

The formal worker attaches this opaque artifact read-only at `/system`. The artifact contains a
digest-pinned Docker archive, tracked loop source, commit-pinned skills, a file manifest, and the
`run-system` launcher. The image is loaded only into the disposable VM's Docker daemon.

Build inputs are explicit:

```bash
python3 benchmarks/runner/system_artifact/fetch-skills.py \
  benchmarks/runner/system_artifact/skills.lock.yaml /tmp/plan009-skills

benchmarks/runner/system_artifact/build-runtime.sh \
  /path/to/loopflow /tmp/bio-reproducer-runtime.tar
```

`build-runtime.sh` refuses a dirty loopflow checkout and uses `git archive HEAD`, so mutable source
and `.git` state do not enter the image. The runtime pins the Linux/amd64 Pixi base, Python base,
Claude Code version, loopflow commit, and this repository's `pixi.lock`.
It exports the configured image tag into the archive and writes both `.image-id` provenance and the
`.image-ref` guest locator. The artifact builder structurally verifies that the archive contains
exactly that tag bound to the expected config identity. The archive and artifact digests remain the
integrity authorities; the tag is only a stable locator inside a fresh disposable VM.

The launcher forwards only environment names declared in `manifest.json`. Values arrive from the
trusted Runner over SSH stdin, exist only in the disposable guest process/container, and are never
written to the artifact or execution provenance.
