# Minimal Worker Image

This directory defines infrastructure for the formal QEMU/KVM backend. The worker image is a
minimal Ubuntu guest with SSH control and VM-local Docker. It does not contain bio-reproducer,
entry inputs, oracle data, scientific packages, or model credentials.

Build the trusted control image, create a dedicated control key, then build the pinned guest:

```bash
docker build -t bio-reproducer-vm-control:plan008 -f Dockerfile.control .
ssh-keygen -q -t ed25519 -N '' -f /secure/path/worker-key
docker run --rm --device /dev/kvm \
  -v "$PWD:/work" -w /work \
  bio-reproducer-vm-control:plan008 \
  ./build-worker.sh /work/worker.qcow2 /work/worker-key.pub
```

`build-worker.sh` verifies the pinned Ubuntu cloud image, installs Docker during image creation,
shuts the build guest down, and flattens its overlay. The resulting `.sha256` file is the worker
pin supplied to `bench-run`; the private SSH key stays in the trusted Runner and is not embedded
in benchmark entries or submissions.

The dated Ubuntu base is cached beside the output image. Downloads use Range resume, low-speed
timeouts, and bounded retries so a dead connection does not silently hold a worker build forever.
`BIO_REPRODUCER_UBUNTU_CLOUD_URL` may select a transport mirror; the fixed SHA256 remains the
authority regardless of download location.

`smoke-system/` is not a production system artifact. The Plan 008 smoke adds an OCI archive named
`ubuntu-22.04.tar`, hashes the resulting tree, and uses it to prove nested Docker and I/O behavior
without relying on a registry during the formal run.

Run `smoke.py` from the repository root inside the trusted control container. It creates isolated
input/workspace/output directories, invokes the same `QemuWorker` used by the adapter, checks the
guest-produced artifact, enforces the 60-second cold-boot target, and prints the formal execution
envelope. It is intentionally opt-in and is not part of ordinary `pytest` runs.
