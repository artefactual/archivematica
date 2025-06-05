#!/bin/bash
set -euo pipefail

INPUT_REF="$1"

# Default environment variables (can be overridden)
REGISTRY_DOCKERHUB="${REGISTRY_DOCKERHUB:-docker.io}"
REGISTRY_GHCR="${REGISTRY_GHCR:-ghcr.io}"

# Helper function to set registry outputs
set_registry_outputs() {
  local is_tagged="$1"
  if [ "$is_tagged" = "true" ]; then
    echo "DOCKER_REGISTRY=$REGISTRY_DOCKERHUB"
  else
    echo "DOCKER_REGISTRY=$REGISTRY_GHCR"
  fi
}

# Check if input is a valid tag
if git rev-parse "refs/tags/$INPUT_REF" >/dev/null 2>&1; then
  COMMIT=$(git rev-list -n 1 "refs/tags/$INPUT_REF")
  echo "REF=$COMMIT"
  echo "VERSION=$INPUT_REF"
  echo "IS_TAGGED=true"
  set_registry_outputs "true"
  exit 0
fi

# Check if input is a valid branch name
if git show-ref --verify --quiet "refs/heads/$INPUT_REF" || git show-ref --verify --quiet "refs/remotes/origin/$INPUT_REF"; then
  # Resolve branch to commit SHA
  if git show-ref --verify --quiet "refs/heads/$INPUT_REF"; then
    FULL_SHA=$(git rev-parse "refs/heads/$INPUT_REF")
  else
    FULL_SHA=$(git rev-parse "refs/remotes/origin/$INPUT_REF")
  fi

  SHORT_SHA=$(echo "$FULL_SHA" | cut -c1-7)

  # Check if this commit has a version tag
  VERSION_TAG=$(git tag --points-at "$FULL_SHA" | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+' | head -n 1 || true)

  echo "REF=$FULL_SHA"

  if [ -n "$VERSION_TAG" ]; then
    echo "VERSION=$VERSION_TAG"
    echo "IS_TAGGED=true"
    set_registry_outputs "true"
  else
    echo "VERSION=$SHORT_SHA"
    echo "IS_TAGGED=false"
    set_registry_outputs "false"
  fi
  exit 0
fi

# Check if input is a valid commit SHA
if git cat-file -e "$INPUT_REF^{commit}" 2>/dev/null; then
  FULL_SHA=$(git rev-parse "$INPUT_REF")
  SHORT_SHA=$(echo "$FULL_SHA" | cut -c1-7)

  # Check if this commit has a version tag
  VERSION_TAG=$(git tag --points-at "$FULL_SHA" | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+' | head -n 1 || true)

  echo "REF=$FULL_SHA"

  if [ -n "$VERSION_TAG" ]; then
    echo "VERSION=$VERSION_TAG"
    echo "IS_TAGGED=true"
    set_registry_outputs "true"
  else
    echo "VERSION=$SHORT_SHA"
    echo "IS_TAGGED=false"
    set_registry_outputs "false"
  fi
  exit 0
fi

echo "ERROR: '$INPUT_REF' is not a valid tag, branch, or commit SHA." >&2
exit 1
