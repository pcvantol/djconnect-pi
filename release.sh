#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./release.sh <version> [--dry-run]

Examples:
  ./release.sh 0.1.0
  ./release.sh v0.1.0 --dry-run

The script updates version metadata, builds a release tarball and sha256 file,
commits, tags, pushes main and creates a GitHub release.
EOF
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 64
fi

VERSION="${1#v}"
TAG="v${VERSION}"
DRY_RUN=false

if [[ $# -eq 2 ]]; then
  if [[ "$2" != "--dry-run" ]]; then
    usage
    exit 64
  fi
  DRY_RUN=true
fi

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid version: $1. Use semantic version format, for example 0.1.0." >&2
  exit 64
fi

if [[ ! -f "pyproject.toml" || ! -d "src/djconnect_pi" ]]; then
  echo "Run this script from the djconnect-pi repository root." >&2
  exit 1
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag already exists locally: $TAG" >&2
  exit 1
fi

if [[ "$DRY_RUN" == false ]] && git ls-remote --exit-code --tags origin "refs/tags/${TAG}" >/dev/null 2>&1; then
  echo "Tag already exists on origin: $TAG" >&2
  exit 1
fi

run() {
  echo "+ $*"
  if [[ "$DRY_RUN" == false ]]; then
    "$@"
  fi
}

bump_versions() {
  echo "+ update repo version to ${VERSION}"
  VERSION="$VERSION" DRY_RUN="$DRY_RUN" python3 - <<'PY'
import os
import re
from pathlib import Path

version = os.environ["VERSION"]
dry_run = os.environ["DRY_RUN"] == "true"

replacements = {
    "pyproject.toml": [(r'^version = "[^"]+"$', f'version = "{version}"')],
    "src/djconnect_pi/__init__.py": [(r'^__version__ = "[^"]+"$', f'__version__ = "{version}"')],
    "src/djconnect_pi/config.py": [(r'^PROTOCOL_VERSION = "[^"]+"$', f'PROTOCOL_VERSION = "{version}"')],
    "scripts/install_raspberry_pi.sh": [
        (r'^DJCONNECT_VERSION="\$\{DJCONNECT_VERSION:-[^}]+\}"$', f'DJCONNECT_VERSION="${{DJCONNECT_VERSION:-{version}}}"'),
        (r'  DJCONNECT_VERSION=[0-9]+\.[0-9]+\.[0-9]+', f'  DJCONNECT_VERSION={version}'),
        (r'"version": "[^"]+"', f'"version": "{version}"'),
    ],
    "scripts/bootstrap_raspberry_pi_os.sh": [
        (r'^DJCONNECT_BOOTSTRAP_VERSION="\$\{DJCONNECT_BOOTSTRAP_VERSION:-[^}]+\}"$', f'DJCONNECT_BOOTSTRAP_VERSION="${{DJCONNECT_BOOTSTRAP_VERSION:-{version}}}"'),
    ],
    "README.md": [
        (r"^Version: `[^`]+`$", f"Version: `{version}`"),
        (r"djconnect-pi-[0-9]+\.[0-9]+\.[0-9]+\.tar\.gz", f"djconnect-pi-{version}.tar.gz"),
        (r"cd djconnect-pi-[0-9]+\.[0-9]+\.[0-9]+", f"cd djconnect-pi-{version}"),
    ],
    "CHANGELOG.md": [(r"^## .+$", f"## {version}")],
    "docs/ARCHITECTURE.md": [(r'"version": "[^"]+"', f'"version": "{version}"')],
    "docs/BOOTSTRAP.md": [
        (r"djconnect-pi-[0-9]+\.[0-9]+\.[0-9]+\.tar\.gz", f"djconnect-pi-{version}.tar.gz"),
        (r"cd djconnect-pi-[0-9]+\.[0-9]+\.[0-9]+", f"cd djconnect-pi-{version}"),
    ],
}

for file_name, rules in replacements.items():
    path = Path(file_name)
    text = path.read_text()
    updated = text
    for pattern, replacement in rules:
        updated = re.sub(pattern, replacement, updated, flags=re.MULTILINE)
    if updated == text:
        print(f"  unchanged {file_name}")
        continue
    print(f"  update {file_name}")
    if not dry_run:
        path.write_text(updated)
PY
}

build_assets() {
  echo "+ build release assets"
  local dist="dist/djconnect-pi-${VERSION}"
  run rm -rf "$dist" "dist/djconnect-pi-${VERSION}.tar.gz" "dist/djconnect-pi-${VERSION}.sha256"
  run mkdir -p "$dist"
  run cp -R pyproject.toml README.md CHANGELOG.md docs src systemd "$dist/"
  run mkdir -p "$dist/scripts"
  run cp scripts/install_raspberry_pi.sh "$dist/scripts/"
  if [[ "$DRY_RUN" == false ]]; then
    printf '%s\n' "$VERSION" > "$dist/VERSION"
  else
    echo "+ write $dist/VERSION"
  fi
  run tar -C dist -czf "dist/djconnect-pi-${VERSION}.tar.gz" "djconnect-pi-${VERSION}"
  run shasum -a 256 "dist/djconnect-pi-${VERSION}.tar.gz"
  if [[ "$DRY_RUN" == false ]]; then
    shasum -a 256 "dist/djconnect-pi-${VERSION}.tar.gz" > "dist/djconnect-pi-${VERSION}.sha256"
  else
    echo "+ write dist/djconnect-pi-${VERSION}.sha256"
  fi
}

bump_versions
build_assets
run git add .
run git commit -m "Release DJConnect Pi ${TAG}"
run git tag "$TAG"
run git push origin main
run git push origin "$TAG"
run gh release create "$TAG" \
  --title "DJConnect Pi ${TAG}" \
  --notes-file CHANGELOG.md \
  "dist/djconnect-pi-${VERSION}.tar.gz" \
  "dist/djconnect-pi-${VERSION}.sha256"

echo "Release ${TAG} complete."
