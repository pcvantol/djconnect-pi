#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./cleanup_old_releases.sh [--keep N] [--execute] [--skip-actions]

Examples:
  ./cleanup_old_releases.sh
  ./cleanup_old_releases.sh --keep 2 --execute

By default this is a dry-run. It keeps the newest semantic-version tags/releases
and deletes older matching vX.Y.Z GitHub releases, remote tags, local tags and
completed GitHub Actions runs for those tags only when --execute is passed.
EOF
}

KEEP=1
EXECUTE=false
CLEAN_ACTIONS=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep)
      if [[ $# -lt 2 || ! "$2" =~ ^[0-9]+$ || "$2" -lt 1 ]]; then
        echo "--keep requires a positive number." >&2
        exit 64
      fi
      KEEP="$2"
      shift 2
      ;;
    --execute)
      EXECUTE=true
      shift
      ;;
    --skip-actions)
      CLEAN_ACTIONS=false
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 64
      ;;
  esac
done

if [[ ! -d ".git" || ! -f "pyproject.toml" || ! -d "src/djconnect_pi" ]]; then
  echo "Run this script from the djconnect-pi repository root." >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI 'gh' is required." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated. Run 'gh auth login' first." >&2
  exit 1
fi

run() {
  echo "+ $*"
  if [[ "$EXECUTE" == true ]]; then
    "$@"
  fi
}

delete_action_runs_for_tag() {
  local tag="$1"

  if [[ "$CLEAN_ACTIONS" != true ]]; then
    return
  fi

  mapfile -t run_ids < <(
    gh run list \
      --branch "$tag" \
      --status completed \
      --limit 100 \
      --json databaseId \
      --jq '.[].databaseId'
  )

  if [[ "${#run_ids[@]}" -eq 0 ]]; then
    echo "+ skip missing completed GitHub Actions runs for $tag"
    return
  fi

  for run_id in "${run_ids[@]}"; do
    run gh run delete "$run_id"
  done
}

mapfile -t TAGS < <(
  git ls-remote --tags --refs origin 'v*' \
    | awk '{print $2}' \
    | sed 's#refs/tags/##' \
    | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' \
    | sort -V -r
)

if [[ "${#TAGS[@]}" -eq 0 ]]; then
  echo "No semantic version tags found on origin."
  exit 0
fi

echo "Newest tags/releases to keep:"
printf '  %s\n' "${TAGS[@]:0:KEEP}"

if [[ "${#TAGS[@]}" -le "$KEEP" ]]; then
  echo "Nothing to delete."
  exit 0
fi

DELETE_TAGS=("${TAGS[@]:KEEP}")

echo
if [[ "$EXECUTE" == true ]]; then
  echo "Deleting old releases/tags and completed Actions runs:"
else
  echo "Dry-run. Would delete old releases/tags and completed Actions runs:"
fi
printf '  %s\n' "${DELETE_TAGS[@]}"
echo

for tag in "${DELETE_TAGS[@]}"; do
  delete_action_runs_for_tag "$tag"
  if gh release view "$tag" >/dev/null 2>&1; then
    run gh release delete "$tag" --yes
  else
    echo "+ skip missing GitHub release $tag"
  fi
  run git push --delete origin "$tag"
  if git rev-parse "$tag" >/dev/null 2>&1; then
    run git tag -d "$tag"
  else
    echo "+ skip missing local tag $tag"
  fi
done

if [[ "$EXECUTE" == false ]]; then
  echo
  echo "Dry-run complete. Re-run with --execute to delete the old releases/tags and completed Actions runs."
fi
