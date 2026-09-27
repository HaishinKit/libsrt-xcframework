#!/bin/bash

# Copyright (c) shogo4405 and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause License found in the
# LICENSE file in the root directory of this source tree.

set -euo pipefail
cd "$(dirname "$0")"

SRT_VERSION=v1.5.7

checkout_dependency() {
  local directory=$1 url=$2 revision=$3
  if [ ! -d "$directory" ]; then
    git clone --depth 1 "$url" "$directory"
  fi
  if [ -n "$(git -C "$directory" status --porcelain)" ]; then
    echo "Local changes in $directory; commit or stash them before updating." >&2
    exit 1
  fi
  if ! git -C "$directory" rev-parse --verify "$revision^{commit}" >/dev/null 2>&1; then
    git -C "$directory" fetch --depth 1 origin "$revision"
  fi
  git -C "$directory" checkout --detach "$revision"
}

checkout_dependency srt https://github.com/Haivision/srt.git "$SRT_VERSION"
