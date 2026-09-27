#!/bin/bash

# Copyright (c) shogo4405 and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause License found in the
# LICENSE file in the root directory of this source tree.

source "$(dirname "$0")/build-common.sh"

build_srt xros visionOS 1.3 visionos visionos/OS visionos/_OS/libsrt.a
build_srt xrsimulator visionOS 1.3 visionsimulator visionos/SIMULATOR visionos/_SIMULATOR/libsrt.a
