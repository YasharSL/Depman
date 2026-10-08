#!/bin/sh
# Build dist/depman_<version>_all.deb.
# The build runs in a temporary directory because dpkg refuses the file modes of
# Windows-mounted folders (WSL /mnt/...), and so no build output lands in the repo.
set -eu

repo=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

mkdir "$work/depman"
tar -C "$repo" --exclude=./build --exclude=./dist --exclude=./.git \
    --exclude=__pycache__ --exclude=.pytest_cache --exclude=.ruff_cache -cf - . \
    | tar -C "$work/depman" -xf -
# Windows mounts mark every file executable; debhelper would run debian/*.install as scripts.
find "$work/depman" -type d -exec chmod 755 {} +
find "$work/depman" -type f -exec chmod 644 {} +
chmod +x "$work/depman/debian/rules"

(cd "$work/depman" && dpkg-buildpackage --build=binary --unsigned-changes --no-sign)

mkdir -p "$repo/dist"
cp "$work"/depman_*_all.deb "$repo/dist/"
ls -l "$repo/dist"
