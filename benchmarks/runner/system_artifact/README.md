# Bio-Reproducer System Artifact

The formal worker attaches this opaque artifact read-only at `/system`. The artifact contains a
content-addressed OCI archive, tracked loop source, commit-pinned skills, a file manifest, and the
`run-system` launcher. The OCI image is loaded only into the disposable VM's Docker daemon.

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

The launcher forwards only environment names declared in `manifest.json`. Values arrive from the
trusted Runner over SSH stdin, exist only in the disposable guest process/container, and are never
written to the artifact or execution provenance.
