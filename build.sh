#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

usage() {
  cat <<'HELP'
Usage: ./build.sh [command] [argument]
  all                 Prepare, build all platforms, package, and select local manifest (default)
  prepare             Fetch pinned sources and prepare OpenSSL
  build [platform]    Build all or one of: ios tvos macos maccatalyst visionos watchos
  package             Assemble XCFramework and ZIP from built libraries
  local               Select the local development Package.swift
  verify              Check all slices and run the SwiftPM consumer test (local manifest required)
  release TAG         Write root/dist Package.swift with release URL and computed checksum
  publish TAG         Publish ZIP after committing the release manifest and pushing its tag
  help                Show this help

CMAKE and JOBS configure compilation. release does not commit, tag, or upload.
HELP
}
prepare() {
  bash scripts/build/build-clone.sh
  python3 scripts/prepare-openssl.py
}
build_platforms() {
  local platform=${1:-all}
  case "$platform" in
    all) for platform in ios tvos macos maccatalyst visionos watchos; do
           bash "scripts/build/build-$platform.sh"
         done ;;
    ios|tvos|macos|maccatalyst|visionos|watchos) bash "scripts/build/build-$platform.sh" ;;
    *) echo "Unknown platform: $platform" >&2; exit 2 ;;
  esac
}
command=${1:-all}
[ "$#" -le 2 ] || { usage >&2; exit 2; }
case "$command" in
  build|release|publish) ;;
  *) [ "$#" -le 1 ] || { usage >&2; exit 2; } ;;
esac
case "$command" in
  all) prepare; build_platforms; bash scripts/build/build-xcframework.sh; python3 scripts/release-manifest.py local ;;
  prepare) prepare ;;
  build) build_platforms "${2:-all}" ;;
  package) bash scripts/build/build-xcframework.sh ;;
  local) python3 scripts/release-manifest.py local ;;
  verify)
    python3 scripts/release-manifest.py check-local
    python3 tests/verify-build.py
    tests/verify-package.sh ;;
  release) python3 scripts/release-manifest.py release "${2:?Provide a release tag}" ;;
  publish)
    python3 scripts/source-distribution.py check
    tag=${2:?Provide a release tag}
    python3 scripts/release-manifest.py check "$tag"
    [ -z "$(git status --porcelain)" ] || { echo 'Commit changes before publishing.' >&2; exit 1; }
    head=$(git rev-parse HEAD)
    [ "$(git rev-parse "refs/tags/$tag^{commit}")" = "$head" ] || { echo 'Release tag must point to HEAD.' >&2; exit 1; }
    repository=https://github.com/HaishinKit/libsrt-xcframework.git
    remote_tag=$(git ls-remote "$repository" "refs/tags/$tag" "refs/tags/$tag^{}")
    remote_commit=$(printf '%s\n' "$remote_tag" | awk 'NR == 1 {commit=$1} /\^\{\}$/ {commit=$1} END {print commit}')
    [ "$remote_commit" = "$head" ] || { echo 'Push the release tag to GitHub before publishing.' >&2; exit 1; }
    gh release create "$tag" --repo HaishinKit/libsrt-xcframework --verify-tag \
      --title "$tag" --generate-notes libsrt.xcframework.zip libsrt.xcframework.zip.sha256 \
      dist/licensing/THIRD-PARTY-LICENSES.txt dist/licensing/SOURCE-NOTICE.txt \
      dist/licensing/SOURCES.json dist/licensing/libsrt-sources.zip dist/licensing/SHA256SUMS.json ;;
  help|-h|--help) usage ;;
  *) usage >&2; exit 2 ;;
esac
