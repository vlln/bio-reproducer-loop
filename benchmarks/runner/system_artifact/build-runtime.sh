#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "usage: $0 LOOPFLOW_GIT_CHECKOUT OUTPUT_OCI_TAR" >&2
    exit 2
fi

loopflow_source=$(realpath "$1")
output=$(realpath -m "$2")
recipe_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
tmp=$(mktemp -d "${TMPDIR:-/tmp}/bio-reproducer-runtime.XXXXXX")
trap 'rm -rf "$tmp"' EXIT

test -d "$loopflow_source/.git"
test ! -e "$output"
mkdir -p "$(dirname "$output")" "$tmp/loopflow"

git -C "$loopflow_source" diff --quiet
git -C "$loopflow_source" diff --cached --quiet
git -C "$loopflow_source" archive HEAD | tar -x -C "$tmp/loopflow"
cp "$recipe_dir/Dockerfile" "$tmp/Dockerfile"
cp "$recipe_dir/../../../loops/bio-reproducer/pixi.toml" "$tmp/pixi.toml"
cp "$recipe_dir/../../../loops/bio-reproducer/pixi.lock" "$tmp/pixi.lock"

tag="bio-reproducer-runtime:plan009"
build_network=${BIO_REPRODUCER_BUILD_NETWORK:-default}
mip_url=${BIO_REPRODUCER_MIP_URL:-https://github.com/vlln/mip/releases/download/v0.2.0/mip_0.2.0_linux_amd64.tar.gz}
docker build \
    --network "$build_network" \
    --build-arg "MIP_URL=$mip_url" \
    --platform linux/amd64 \
    --tag "$tag" \
    "$tmp"
image_id=$(docker image inspect --format '{{.Id}}' "$tag")
docker save --output "$output" "$image_id"
sha256sum "$output" >"$output.sha256"
printf '%s\n' "$image_id" >"$output.image-id"
printf 'runtime_image=%s\nruntime_archive=%s\n' "$image_id" "$output"
