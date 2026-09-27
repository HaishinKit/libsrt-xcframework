#!/bin/bash

# Copyright (c) shogo4405 and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause License found in the
# LICENSE file in the root directory of this source tree.

# Shared static-library build. Requires CMake 3.28+ and Xcode.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
ROOT=$(pwd)
CMAKE=${CMAKE:-cmake}
# Headers adapted from the exact, signed SwiftPM artifact.
OPENSSL_SDK_ROOT=${OPENSSL_SDK_ROOT:-$ROOT/build/dependencies/sdk}

build_srt() {
  local sdk=$1 system=$2 minimum=$3 openssl_platform=$4 output=$5 merged=$6
  local dependency="$OPENSSL_SDK_ROOT/$openssl_platform"
  if [ ! -f "$dependency/OpenSSL" ]; then
    echo "Missing OpenSSL for $openssl_platform. Run python3 scripts/prepare-openssl.py first." >&2
    return 1
  fi
  if ! grep -Eq '^[[:space:]]*#[[:space:]]*define[[:space:]]+OPENSSL_VERSION_STR[[:space:]]+"3[.]3[.]3"' "$dependency/include/openssl/opensslv.h"; then
    echo "This release requires the OpenSSL-Package 3.3.3001 SDK: $dependency" >&2
    return 1
  fi
  local build="$ROOT/build/$output"
  local target=${7:-}
  local arch=${8:-arm64}
  "$CMAKE" -S "$ROOT/srt" -B "$build" \
    -DCMAKE_SYSTEM_NAME="$system" \
    -DCMAKE_OSX_SYSROOT="$(xcrun --sdk "$sdk" --show-sdk-path)" \
    -DCMAKE_OSX_ARCHITECTURES="$arch" \
    -DCMAKE_OSX_DEPLOYMENT_TARGET="$minimum" \
    -DCMAKE_C_COMPILER_TARGET="$target" \
    -DCMAKE_CXX_COMPILER_TARGET="$target" \
    -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_APPS=OFF -DENABLE_SHARED=OFF -DENABLE_STATIC=ON \
    -DUSE_OPENSSL_PC=OFF -DSRT_USE_OPENSSL_STATIC_LIBS=OFF \
    -DOPENSSL_ROOT_DIR="$dependency" \
    -DOPENSSL_INCLUDE_DIR="$dependency/include" \
    -DOPENSSL_CRYPTO_LIBRARY="$dependency/OpenSSL" \
    -DOPENSSL_SSL_LIBRARY="$dependency/OpenSSL"
  "$CMAKE" --build "$build" --parallel "${JOBS:-8}"

  # OpenSSL remains external. Only SRT objects belong in this artifact.
  mkdir -p "$(dirname "$ROOT/build/$merged")"
  cp "$build/libsrt.a" "$ROOT/build/$merged"
}
