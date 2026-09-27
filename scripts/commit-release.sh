#!/bin/bash
# Called after building and generating a remote manifest, in a detached checkout.
set -euo pipefail
tag=${1:?Provide a release tag}
python3 scripts/release-manifest.py check "$tag"
if git show-ref --verify --quiet "refs/tags/$tag"; then
  echo "Tag already exists: $tag" >&2
  exit 1
fi
# Only the generated manifest may differ from the selected source commit.
python3 - <<'PY'
import subprocess
for args in [['git','diff','--name-only','HEAD','-z'], ['git','ls-files','--others','--exclude-standard','-z']]:
    paths = set(subprocess.check_output(args).decode().rstrip('\0').split('\0')) - {''}
    if paths - {'Package.swift'}:
        raise SystemExit('Unexpected release changes: ' + ', '.join(sorted(paths)))
PY
git add Package.swift
git commit -m "Prepare package release $tag"
git tag "$tag"
