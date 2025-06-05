#!/bin/bash
# Resolve the ref to build and decide where its images are published.
#
# Usage: set-ref.sh REF
#
# REF is a commit hash (at least 7 lowercase hex digits), a branch or a tag.
# Prints key=value lines meant for $GITHUB_OUTPUT:
#
#   ref              full hash of the commit to build
#   kind             release, rc or dev
#   version          main image tag: the tag name for release and rc, the
#                    short commit hash for dev
#   short_sha        first 7 characters of the commit hash
#   docker_registry  registry the images are pushed to
#
# Only a final release tag (vX.Y.Z) passed as REF is a release, which goes to
# Docker Hub. Everything else goes to GHCR: an RC tag (vX.Y.Z-rc.N) passed as
# REF, or a commit that carries one, is an rc (the highest RC tag when the
# commit has several); any other commit is dev.
#
# A REF that looks like a commit hash is only resolved as one, and is rejected
# when a tag or branch has the same name.
set -euo pipefail

REGISTRY_DOCKERHUB="${REGISTRY_DOCKERHUB:-docker.io}"
REGISTRY_GHCR="${REGISTRY_GHCR:-ghcr.io}"
RELEASE_RE='^v[0-9]+\.[0-9]+\.[0-9]+$'
RC_RE='^v[0-9]+\.[0-9]+\.[0-9]+-rc\.[0-9]+$'

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

INPUT_REF="${1:-}"
[ -n "$INPUT_REF" ] || fail "no ref given."
[[ "$INPUT_REF" =~ ^[A-Za-z0-9._/-]+$ ]] ||
  fail "the ref may only contain letters, digits, '.', '_', '/' and '-'."

# Resolve the input to a commit.
INPUT_TAG=""
if [[ "$INPUT_REF" =~ ^[0-9a-f]{7,40}$ ]]; then
  for NAMED_REF in "refs/tags/$INPUT_REF" "refs/remotes/origin/$INPUT_REF" "refs/heads/$INPUT_REF"; do
    if git show-ref --verify --quiet "$NAMED_REF"; then
      fail "'$INPUT_REF' looks like a commit hash, but $NAMED_REF also exists."
    fi
  done
  COMMIT=$(git rev-parse --verify --quiet "$INPUT_REF^{commit}") ||
    fail "'$INPUT_REF' is not a commit in this repository, or is ambiguous."
elif git show-ref --verify --quiet "refs/tags/$INPUT_REF"; then
  INPUT_TAG="$INPUT_REF"
  COMMIT=$(git rev-parse --verify --quiet "refs/tags/$INPUT_REF^{commit}") ||
    fail "tag '$INPUT_REF' does not point to a commit."
elif git show-ref --verify --quiet "refs/remotes/origin/$INPUT_REF"; then
  COMMIT=$(git rev-parse --verify --quiet "refs/remotes/origin/$INPUT_REF^{commit}") ||
    fail "branch '$INPUT_REF' does not point to a commit."
elif git show-ref --verify --quiet "refs/heads/$INPUT_REF"; then
  COMMIT=$(git rev-parse --verify --quiet "refs/heads/$INPUT_REF^{commit}") ||
    fail "branch '$INPUT_REF' does not point to a commit."
else
  fail "'$INPUT_REF' is not a tag, a branch or a commit hash."
fi
SHORT_SHA="${COMMIT:0:7}"

# Classify the build.
if [[ "$INPUT_TAG" =~ $RELEASE_RE ]]; then
  KIND=release
  VERSION="$INPUT_TAG"
elif [[ "$INPUT_TAG" =~ $RC_RE ]]; then
  KIND=rc
  VERSION="$INPUT_TAG"
else
  TAGS=$(git tag --points-at "$COMMIT") || fail "could not list the tags of $COMMIT."
  RC_TAG=$(grep -E "$RC_RE" <<<"$TAGS" | sort -V | tail -n 1 || true)
  if [ -n "$RC_TAG" ]; then
    KIND=rc
    VERSION="$RC_TAG"
  else
    KIND=dev
    VERSION="$SHORT_SHA"
  fi
fi

if [ "$KIND" = release ]; then
  REGISTRY="$REGISTRY_DOCKERHUB"
else
  REGISTRY="$REGISTRY_GHCR"
fi

echo "'$INPUT_REF' is commit $COMMIT: kind=$KIND, version=$VERSION, registry=$REGISTRY" >&2
printf '%s\n' \
  "ref=$COMMIT" \
  "kind=$KIND" \
  "version=$VERSION" \
  "short_sha=$SHORT_SHA" \
  "docker_registry=$REGISTRY"
