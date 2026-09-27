#!/bin/bash

# Copyright (c) shogo4405 and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause License found in the
# LICENSE file in the root directory of this source tree.

set -euo pipefail
cd "$(dirname "$0")"

rm -rf Includes
mkdir -p Includes/libsrt
# creating a directory in libsrt to address modulemap conflicts.
# seealso:
#   https://github.com/shogo4405/HaishinKit.swift/discussions/1403
#   https://github.com/jessegrosjean/swift-cargo-problem
cp -f srt/srtcore/*.h Includes/libsrt
cp support/module.modulemap Includes/libsrt/module.modulemap
cp ./build/ios/OS/version.h Includes/libsrt/version.h

rm -rf libsrt.xcframework
xcodebuild -create-xcframework \
    -library ./build/ios/_SIMULATOR64/libsrt.a -headers Includes \
    -library ./build/ios/_OS/libsrt.a -headers Includes \
    -library ./build/visionos/_SIMULATOR/libsrt.a -headers Includes \
    -library ./build/visionos/_OS/libsrt.a -headers Includes \
    -library ./build/tvos/_SIMULATOR/libsrt.a -headers Includes \
    -library ./build/tvos/_OS/libsrt.a -headers Includes \
    -library ./build/macosx/libsrt.a -headers Includes \
    -library ./build/maccatalyst/libsrt.a -headers Includes \
    -output libsrt.xcframework


mkdir -p libsrt.xcframework/Licenses
cp srt/LICENSE libsrt.xcframework/Licenses/SRT-LICENSE
cat > libsrt.xcframework/DEPENDENCIES.json <<'EOF'
{
  "srtVersion": "1.5.7",
  "opensslBuildVersion": "3.3.3",
  "opensslPackage": "https://github.com/krzyzanowskim/OpenSSL-Package.git",
  "opensslPackageRange": "3.3.3001..<4.0.0",
  "opensslBundled": false,
  "requiredArtifact": "OpenSSL.xcframework"
}
EOF
# Recreate the archive so removed files cannot survive a rebuild.
rm -f libsrt.xcframework.zip
COPYFILE_DISABLE=1 /usr/bin/zip -qry libsrt.xcframework.zip libsrt.xcframework
swift package compute-checksum libsrt.xcframework.zip > libsrt.xcframework.zip.sha256
cat libsrt.xcframework.zip.sha256
