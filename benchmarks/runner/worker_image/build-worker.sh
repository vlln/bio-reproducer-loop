#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 OUTPUT_QCOW2 SSH_PUBLIC_KEY" >&2
  exit 2
fi

output=$(realpath -m "$1")
public_key=$(realpath "$2")
work=$(mktemp -d "${TMPDIR:-/tmp}/bio-reproducer-worker-build.XXXXXX")
cleanup() {
  status=$?
  if [[ $status -ne 0 && -f "$work/serial.log" ]]; then
    mkdir -p "$(dirname "$output")"
    cp "$work/serial.log" "$output.build.log"
  fi
  rm -rf "$work"
  exit "$status"
}
trap cleanup EXIT

cloud_url=${BIO_REPRODUCER_UBUNTU_CLOUD_URL:-https://cloud-images.ubuntu.com/jammy/20260722/jammy-server-cloudimg-amd64.img}
cloud_sha256=757908b2fd6d5b1431bb45070fc1f56cbf017d4025568d292ece37d9cc75e812
cache_dir=$(dirname "$output")
cloud_image="$cache_dir/ubuntu-jammy-20260722.qcow2"
overlay="$work/worker-build.qcow2"
seed="$work/seed.img"

mkdir -p "$cache_dir"
if [[ -f "$cloud_image.partial" && ! -f "$cloud_image" ]]; then
  mv "$cloud_image.partial" "$cloud_image"
fi
if echo "$cloud_sha256  $cloud_image" | sha256sum --check --status 2>/dev/null; then
  echo "Using verified cached Ubuntu worker base"
else
  curl --fail --location --continue-at - \
    --connect-timeout 30 --speed-limit 1024 --speed-time 60 \
    --retry 10 --retry-all-errors \
    --output "$cloud_image" "$cloud_url"
  if ! echo "$cloud_sha256  $cloud_image" | sha256sum --check --status; then
    rm -f "$cloud_image"
    echo "downloaded Ubuntu worker base failed its pinned SHA256" >&2
    exit 1
  fi
fi
qemu-img create -q -f qcow2 -F qcow2 -b "$cloud_image" "$overlay" 12G

cat >"$work/meta-data" <<'EOF'
instance-id: bio-reproducer-worker-build-v1
local-hostname: bio-reproducer-worker
EOF

cat >"$work/user-data" <<EOF
#cloud-config
users:
  - name: benchmark
    groups: [adm]
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - $(cat "$public_key")
ssh_pwauth: false
bootcmd:
  - [sh, -c, 'rm -f /etc/resolv.conf && printf "nameserver 223.5.5.5\noptions timeout:5 attempts:5\n" > /etc/resolv.conf']
package_update: true
packages:
  - docker.io
runcmd:
  - [usermod, -aG, docker, benchmark]
  - [systemctl, enable, --now, docker]
  - [sh, -c, 'command -v docker >/dev/null && systemctl is-active --quiet docker && dpkg-query -W docker.io >/dev/null && docker --version > /var/lib/bio-reproducer-worker-validation.txt && touch /var/lib/bio-reproducer-worker-ready']
power_state:
  mode: poweroff
  timeout: 2400
  condition: test -f /var/lib/bio-reproducer-worker-ready
EOF

cloud-localds "$seed" "$work/user-data" "$work/meta-data"
timeout 2400 qemu-system-x86_64 \
  -accel kvm \
  -machine q35 \
  -cpu host \
  -m 4096 \
  -smp 4 \
  -drive "file=$overlay,if=virtio,format=qcow2" \
  -drive "file=$seed,if=virtio,format=raw,readonly=on" \
  -netdev user,id=net0 \
  -device virtio-net-pci,netdev=net0 \
  -display none \
  -serial "file:$work/serial.log"

mkdir -p "$(dirname "$output")"
qemu-img convert -q -O qcow2 "$overlay" "$output"
qemu-img check "$output"
sha256sum "$output" | tee "$output.sha256"
