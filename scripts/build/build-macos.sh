#!/bin/bash

# Copyright (c) shogo4405 and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause License found in the
# LICENSE file in the root directory of this source tree.

source "$(dirname "$0")/build-common.sh"

build_srt macosx Darwin 11.0 macosx macosx/arm64 macosx/libsrt.a
