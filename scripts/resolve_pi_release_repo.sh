#!/usr/bin/env bash
set -euo pipefail

repository="$(gh api repositories/1267500969 --jq 'select(.id == 1267500969 and .visibility == "public") | .full_name')"
case "$repository" in
  djconnect-music-dj/djconnect-pi-releases)
    printf '%s\n' "$repository"
    ;;
  *)
    echo "Unexpected DJConnect Pi release repository." >&2
    exit 1
    ;;
esac
