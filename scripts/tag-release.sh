#!/usr/bin/env bash
# Tag what is about to be deployed to production (SAN-1626).
#
# For each repo named, tags the head of its production branch (master for
# sanchiconnect-saas-tenants and sc-saas-3rdparty-webservices, main for the
# others) as release-YYYY-MM-DD, or release-YYYY-MM-DD-2, -3 ... when that
# date is already taken in the repo, and pushes the tag. The same tag goes in
# SENTRY_RELEASE on the server and in docs/DEPLOY-LOG.md.
#
# Usage (from the workspace root, with the repos cloned next to scripts/):
#   scripts/tag-release.sh sc-saas-backend sc-saas-admin
#   scripts/tag-release.sh --dry-run sc-saas-backend
#   RELEASE_DATE=2026-10-20 scripts/tag-release.sh sanchiconnect-saas-tenants
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then DRY_RUN=1; shift; fi
[ $# -gt 0 ] || { echo "usage: $0 [--dry-run] <repo> [<repo> ...]" >&2; exit 2; }

DATE="${RELEASE_DATE:-$(TZ=Asia/Kolkata date +%Y-%m-%d)}"

prod_branch() {
  case "$1" in
    sanchiconnect-saas-tenants|sc-saas-3rdparty-webservices) echo master ;;
    *) echo main ;;
  esac
}

for repo in "$@"; do
  dir="$ROOT/$repo"
  [ -d "$dir/.git" ] || { echo "$repo: not a git checkout at $dir" >&2; exit 1; }
  branch="$(prod_branch "$repo")"
  git -C "$dir" fetch --quiet --tags origin "$branch"
  commit="$(git -C "$dir" rev-parse "origin/$branch")"

  existing="$(git -C "$dir" tag --points-at "$commit" -l 'release-*' | head -1)"
  if [ -n "$existing" ]; then
    echo "$repo: origin/$branch ($(git -C "$dir" rev-parse --short "$commit")) is already tagged $existing"
    continue
  fi

  tag="release-$DATE"
  n=2
  while git -C "$dir" rev-parse -q --verify "refs/tags/$tag" >/dev/null; do
    tag="release-$DATE-$n"; n=$((n + 1))
  done

  if [ "$DRY_RUN" = 1 ]; then
    echo "$repo: would tag origin/$branch ($(git -C "$dir" rev-parse --short "$commit")) as $tag"
    continue
  fi
  git -C "$dir" tag -a "$tag" "$commit" -m "Production release $tag ($repo, $branch)"
  git -C "$dir" push --quiet origin "refs/tags/$tag"
  echo "$repo: tagged origin/$branch ($(git -C "$dir" rev-parse --short "$commit")) as $tag and pushed it"
done
