#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./release.sh <version> [--dry-run] [--no-push-main]

Examples:
  ./release.sh 0.1.0
  ./release.sh v0.1.0 --dry-run

The script updates version metadata, builds a wheel-based release tarball and
sha256 file, commits, tags, pushes main and creates a GitHub release.

Use --no-push-main when GitHub branch protection requires the release commit to
land through a pull request. In that mode the script still pushes the tag and
creates the GitHub release from the built assets.
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 64
fi

VERSION="${1#v}"
TAG="v${VERSION}"
DRY_RUN=false
PUSH_MAIN=true

shift
for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=true
      ;;
    --no-push-main)
      PUSH_MAIN=false
      ;;
    *)
      usage
      exit 64
      ;;
  esac
done

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

verify_release_base() {
  echo "+ verify release HEAD is based on origin/main"
  run git fetch origin main
  if [[ "$DRY_RUN" == false ]] && ! git merge-base --is-ancestor origin/main HEAD; then
    echo "Current HEAD is not based on origin/main. Rebase or merge origin/main before releasing." >&2
    exit 1
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
    "scripts/install.sh": [
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

path = Path("CHANGELOG.md")
text = path.read_text()
updated = re.sub(r"^## .+$", f"## {version}", text, count=1, flags=re.MULTILINE)
if updated != text:
    print("  update CHANGELOG.md")
    if not dry_run:
        path.write_text(updated)
PY
}

build_assets() {
  echo "+ build release assets"
  local dist="dist/djconnect-pi-${VERSION}"
  run python3 -m pip install --upgrade pip setuptools wheel
  run rm -rf "$dist" "dist/djconnect-pi-${VERSION}.tar.gz" "dist/djconnect-pi-${VERSION}.sha256"
  run mkdir -p "$dist"
  run cp -R LICENSE README.md CHANGELOG.md docs examples systemd "$dist/"
  run mkdir -p "$dist/scripts"
  run cp scripts/install.sh "$dist/scripts/"
  run mkdir -p "$dist/wheels"
  run python3 -m pip wheel --no-deps --wheel-dir "$dist/wheels" .
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

write_release_notes() {
  echo "+ write release notes for ${VERSION}"
  VERSION="$VERSION" DRY_RUN="$DRY_RUN" python3 - <<'PY'
import os
from pathlib import Path

version = os.environ["VERSION"]
dry_run = os.environ["DRY_RUN"] == "true"
text = Path("CHANGELOG.md").read_text(encoding="utf-8")
heading = f"## {version}"
start = text.find(heading)
if start < 0:
    if dry_run:
        print(f"  would write dist/djconnect-pi-{version}-release-notes.md")
        raise SystemExit(0)
    raise SystemExit(f"Missing changelog section for {version}")
next_start = text.find("\n## ", start + len(heading))
section = text[start: next_start if next_start >= 0 else len(text)].strip() + "\n"
path = Path("dist") / f"djconnect-pi-{version}-release-notes.md"
print(f"  write {path}")
if not dry_run:
    path.write_text(section, encoding="utf-8")
PY
}

verify_release_base
bump_versions
build_assets
run git add .
run git commit -m "Release DJConnect Pi ${TAG}"
run git tag "$TAG"
if [[ "$PUSH_MAIN" == true ]]; then
  run git push origin HEAD:main
else
  echo "+ skip git push origin HEAD:main (--no-push-main)"
fi
run git push origin "$TAG"
write_release_notes
run gh release create "$TAG" \
  --title "DJConnect Pi ${TAG}" \
  --notes-file "dist/djconnect-pi-${VERSION}-release-notes.md" \
  "dist/djconnect-pi-${VERSION}.tar.gz" \
  "dist/djconnect-pi-${VERSION}.sha256"

echo "Release ${TAG} complete."
