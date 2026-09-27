#!/bin/bash

source "$(dirname "$0")/build-common.sh"

# Catalyst uses the macOS SDK with the iOS macabi target. Leave the macOS
# deployment setting empty; the target triple supplies Catalyst's minimum.
build_srt macosx Darwin "" macosx_catalyst maccatalyst/arm64 maccatalyst/libsrt.a arm64-apple-ios14.0-macabi
