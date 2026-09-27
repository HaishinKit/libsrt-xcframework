# libsrt.xcframework

SRT **v1.5.7** for Apple platforms, using **OpenSSL 3.x** from
[OpenSSL-Package](https://github.com/krzyzanowskim/OpenSSL-Package).
This project is maintained for HaishinKit and can also be used independently.

## Platforms

| iOS | tvOS | macOS | visionOS | Mac Catalyst | watchOS |
|---|---|---|---|---|---|
| 13.0+ | 13.0+ | 11.0+ | 1.3+ | 14.0+ (macOS 11+) | 8.0+ (arm64_32 / armv7k) / 26.0+ (arm64) |

SRT includes ten slices and twelve architecture variants. watchOS devices
use a universal arm64 + arm64_32 + armv7k library; the watchOS simulator is arm64 with
an 8.0 minimum. The other platforms are arm64; iOS and tvOS simulators require
14.0+. Intel slices are not included. The visionOS minimum follows
the dependency's SwiftPM manifest. Xcode 26 requires a 26.0 deployment target
for the watchOS arm64 device ABI; arm64_32 and armv7k retain the older deployment target.
watchOS has been cross-compiled and link-tested; on-watch runtime/networking
and application archive validation remain to be performed.

## OpenSSL dependency

**OpenSSL is not bundled inside libsrt.a.** The Swift package depends on the
upstream `OpenSSL` product in the range **3.3.3001..<4.0.0**. Its signed dynamic framework, Privacy Manifest and dSYMs are supplied
by the upstream project. This repository does not build or re-sign OpenSSL.

Build headers come from the minimum supported package version **3.3.3001**
(OpenSSL **3.3.3**), pinned by SHA-256. The package allows compatible 3.x
updates so other packages can share the dependency. A fresh resolution normally
selects the newest compatible version; the consuming application controls its
resolved version. The lower bound is a compatibility allowance, not a security
recommendation to deploy an old OpenSSL release. Tests cover the lower bound
and package 3.6.3000 (OpenSSL 3.6.3). Use the canonical URL
`https://github.com/krzyzanowskim/OpenSSL-Package.git` for other consumers too.
Do not combine this package with a libsrt/libdatachannel artifact that embeds
another copy of OpenSSL. libdatachannel has not been migrated in this change.
The earlier sibling `openssl-xcframework` project is no longer required.

The upstream 3.6.3000 iOS dSYM inspected has a matching binary UUID,
but lacks OpenSSL implementation source-line information. It does not provide
the same line-level debugging as the earlier custom `-g` build. Consumers must
configure their Crashlytics upload workflow for the shipped framework's dSYM.

## Build locally

Requires Xcode with the platform SDKs, Python 3, and CMake 3.28+:

```sh
./build-clone.sh
python3 scripts/prepare-openssl.py
./build-ios.sh
./build-tvos.sh
./build-macos.sh
./build-maccatalyst.sh
./build-visionos.sh
./build-watchos.sh
./build-xcframework.sh
```

The preparation script downloads the exact upstream ZIP to `build/dependencies`,
checks its SHA-256 and code signature, and creates CMake-compatible header
copies. Only include spelling (`OpenSSL/` to `openssl/`) is adapted; the signed
framework remains unchanged. The script does not execute upstream build scripts.
SRT compilation uses those headers and the corresponding dynamic library;
OpenSSL objects are never merged into `libsrt.a`.

Set `CMAKE=/path/to/cmake` and `JOBS=8` as needed. When changing toolchains,
start with a clean `build/` directory and run the preparation step again.
Legacy `OpenSSL/`, `openssl-src/`, and `build/openssl/` directories are unused.

## Swift Package Manager

Add this directory as a local package. The `libsrt` product includes a source
wrapper that declares OpenSSL-Package and the C++ runtime. Application code
keeps using `import libsrt`.

```swift
dependencies: [.package(path: "../libsrt-xcframework")],
targets: [
    .target(name: "MyApp", dependencies: [
        .product(name: "libsrt", package: "libsrt-xcframework")
    ])
]
```

If declaring the libsrt binary target directly, add the OpenSSL product to the
consuming source target and link the C++ runtime. Binary targets cannot declare
these dependencies. For manual integration, embed and sign the selected dynamic
`OpenSSL.framework` in the application; do not merely link it. Verify the final
app archive includes its Privacy Manifest and required framework resources.

## Distribution

Outputs are `libsrt.xcframework`, `libsrt.xcframework.zip`, and its `.sha256`.
`DEPENDENCIES.json` records the OpenSSL build version and accepted package range.
Prepare a release manifest with the SRT asset URL:

```sh
./prepare-release.sh https://github.com/YOUR_OWNER/libsrt-xcframework/releases/download/v1.5.7
```

The generated `dist/Package.swift` preserves the upstream dependency and uses
the actual SRT ZIP checksum. Use it for the release commit and upload matching
assets. Keep published assets immutable; use a new tag when replacing an older
OpenSSL-bundled release. These scripts do not publish releases. No separate
OpenSSL release or signing certificate needs to be maintained here.

## Verification

`python3 tests/verify-build.py` checks all ten SRT slices (twelve architecture variants), absence of embedded
OpenSSL definitions, and Swift linking against the upstream framework. It runs
AES-256 encrypted loopback checks on macOS and Mac Catalyst, including an actual
OpenSSL runtime-version assertion. Local socket access is required. Device and
simulator runtime tests remain separate.

The SwiftPM wrapper can also be checked with Xcode for watchOS:

```sh
xcodebuild -scheme libsrt -destination 'generic/platform=watchOS' \
  -derivedDataPath build/watchos-package CODE_SIGNING_ALLOWED=NO build
```

This builds the package; it does not run an app on a Watch.

`tests/verify-package.sh` resolves the real upstream Swift package and runs a
minimal consumer, checking transitive OpenSSL and C++ linkage. To reproduce
an application with an existing lower-version constraint, run:

```sh
OPENSSL_PACKAGE_VERSION=3.3.3001 tests/verify-package.sh
```

For cross-version linkage and encrypted runtime checks against another
extracted upstream artifact, set `OPENSSL_XCFRAMEWORK` and
`EXPECTED_OPENSSL_VERSION` when running `tests/verify-build.py`.

## License

SRT is MPL-2.0; its license is included in the XCFramework. OpenSSL is separately
distributed under Apache-2.0 with its own license notices. Applications must
preserve the applicable notices for both dependencies.
