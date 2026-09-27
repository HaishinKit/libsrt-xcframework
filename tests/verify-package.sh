#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/integration/Sources/SplitSmoke
cat > build/integration/Package.swift <<'MANIFEST'
// swift-tools-version: 5.9
import PackageDescription
let package = Package(
    name: "SplitSmoke",
    platforms: [.macOS(.v11)],
    dependencies: [.package(path: "../..")],
    targets: [.executableTarget(name: "SplitSmoke", dependencies: [
        .product(name: "libsrt", package: "libsrt-xcframework")
    ])]
)
MANIFEST
# Model an app that already requires one particular upstream version.
if [ -n "${OPENSSL_PACKAGE_VERSION:-}" ]; then
  python3 - <<'PYTHON'
import json
import os
from pathlib import Path
p = Path('build/integration/Package.swift')
s = p.read_text().replace('.package(path: "../..")',
    '.package(path: "../.."), .package(url: "https://github.com/krzyzanowskim/OpenSSL-Package.git", exact: '
    + json.dumps(os.environ['OPENSSL_PACKAGE_VERSION']) + ')')
p.write_text(s)
PYTHON
fi
cp tests/smoke.swift build/integration/Sources/SplitSmoke/main.swift
swift run --package-path build/integration SplitSmoke
