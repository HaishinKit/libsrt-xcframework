#!/bin/bash

# Copyright (c) shogo4405 and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause License found in the
# LICENSE file in the root directory of this source tree.

source "$(dirname "$0")/build-common.sh"

build_srt appletvos tvOS 13.0 appletvos tvos/OS tvos/_OS/libsrt.a
build_srt appletvsimulator tvOS 14.0 appletvsimulator tvos/SIMULATOR tvos/_SIMULATOR/libsrt.a
