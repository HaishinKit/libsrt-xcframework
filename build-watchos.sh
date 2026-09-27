#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/build-common.sh"

# Xcode 26 requires watchOS 26 for the full arm64 device ABI.
# arm64_32 and armv7k retain compatibility with watchOS 8 and later.
build_srt watchos watchOS 26.0 watchos watchos/arm64 watchos/parts/arm64/libsrt.a arm64-apple-watchos26.0 arm64
build_srt watchos watchOS 8.0 watchos watchos/arm64_32 watchos/parts/arm64_32/libsrt.a arm64_32-apple-watchos8.0 arm64_32
build_srt watchos watchOS 8.0 watchos watchos/armv7k watchos/parts/armv7k/libsrt.a armv7k-apple-watchos8.0 armv7k
mkdir -p "$ROOT/build/watchos/device"
xcrun lipo -create "$ROOT/build/watchos/parts/arm64/libsrt.a" "$ROOT/build/watchos/parts/arm64_32/libsrt.a" "$ROOT/build/watchos/parts/armv7k/libsrt.a" -output "$ROOT/build/watchos/device/libsrt.a"
build_srt watchsimulator watchOS 8.0 watchsimulator watchos/simulator-build watchos/simulator/libsrt.a arm64-apple-watchos8.0-simulator arm64
