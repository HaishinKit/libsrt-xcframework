#!/bin/bash

# Copyright (c) shogo4405 and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause License found in the
# LICENSE file in the root directory of this source tree.

source "$(dirname "$0")/build-common.sh"

build_srt iphoneos iOS 13.0 iphoneos ios/OS ios/_OS/libsrt.a
build_srt iphonesimulator iOS 14.0 iphonesimulator ios/SIMULATOR64 ios/_SIMULATOR64/libsrt.a
