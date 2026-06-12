#!/usr/bin/env sh
set -eu

version="${1:?usage: scripts/build_release.sh VERSION}"
dist="dist/djconnect-pi-${version}"

rm -rf "$dist" "dist/djconnect-pi-${version}.tar.gz" "dist/djconnect-pi-${version}.sha256"
mkdir -p "$dist"
cp -R pyproject.toml README.md src systemd "$dist/"
printf '%s\n' "$version" > "$dist/VERSION"
tar -C dist -czf "dist/djconnect-pi-${version}.tar.gz" "djconnect-pi-${version}"
shasum -a 256 "dist/djconnect-pi-${version}.tar.gz" > "dist/djconnect-pi-${version}.sha256"

