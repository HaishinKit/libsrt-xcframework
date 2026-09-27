# libsrt.xcframework

SRT **v1.5.7** for Apple platforms, using **OpenSSL 3.x** from
[OpenSSL-Package](https://github.com/krzyzanowskim/OpenSSL-Package).
This project is maintained for HaishinKit and can also be used independently.

## Platforms

| iOS | tvOS | macOS | visionOS | Mac Catalyst | watchOS |
|---|---|---|---|---|---|
| 13.0+ | 13.0+ | 11.0+ | 1.3+ | 14.0+ (macOS 11+) | 8.0+ (arm64_32 / armv7k) / 26.0+ (arm64) |

SRT includes ten slices and twelve architecture variants. Platforms other than
watchOS use arm64; iOS and tvOS simulators require 14.0+. Intel slices are not
included. The visionOS minimum follows the dependency's SwiftPM manifest.

### watchOS support

The **libsrt XCFramework itself** includes watchOS device and simulator builds,
in addition to the watchOS support provided by OpenSSL-Package.

| Target | Architecture | Minimum watchOS |
|---|---|---|
| Device | arm64_32 | 8.0 |
| Device | armv7k | 8.0 |
| Device | arm64 | 26.0 |
| Simulator | arm64 | 8.0 |

The three device architectures share one universal library. Xcode 26 requires
watchOS 26.0 for the full arm64 device ABI; arm64_32 and armv7k retain the
watchOS 8.0 deployment target. The Swift package declares watchOS 8.0 support.

After preparing the dependencies, run `./build.sh build watchos` to build all four
watchOS variants. Run `./build.sh package` after building the other
platforms to include them in the final distribution. See [Build locally](#build-locally)
for the complete sequence.

All four watchOS variants passed Swift compilation and linking with OpenSSL
3.3.3 and 3.6.3. The SwiftPM product also built successfully in Xcode for a
generic watchOS device destination with code signing disabled.
**Watch device/simulator execution, on-watch networking, and application
archive validation have not been tested.** The encrypted runtime checks in
this repository run on macOS and Mac Catalyst.

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
another copy of OpenSSL. Use the migrated libdatachannel package when sharing OpenSSL with it.
The earlier sibling `openssl-xcframework` project is no longer required.

The upstream 3.6.3000 iOS dSYM inspected has a matching binary UUID,
but lacks OpenSSL implementation source-line information. It does not provide
the same line-level debugging as the earlier custom `-g` build. Consumers must
configure their Crashlytics upload workflow for the shipped framework's dSYM.

## Build locally

Requires Xcode with the platform SDKs, Python 3, and CMake 3.28+:

```sh
./build.sh                  # Prepare, build every platform, package, select local manifest
./build.sh verify           # Link/runtime checks and SwiftPM consumer
```

The only root build entry point is `build.sh`; implementation scripts live in
`scripts/build/`. Individual steps are available as `prepare`, `build [platform]`,
`package`, and `local`. Platforms are `ios`, `tvos`, `macos`, `maccatalyst`,
`visionos`, and `watchos`. Run `./build.sh help` for the full command list.

The preparation script downloads the exact upstream ZIP to `build/dependencies`,
checks its SHA-256 and code signature, and creates CMake-compatible header
copies. Only include spelling (`OpenSSL/` to `openssl/`) is adapted; the signed
framework remains unchanged. The script does not execute upstream build scripts.
SRT compilation uses those headers and the corresponding dynamic library;
OpenSSL objects are never merged into `libsrt.a`.

Set `CMAKE=/path/to/cmake` and `JOBS=8` as needed. When changing toolchains,
start with a clean `build/` directory and run the preparation step again.
Legacy `OpenSSL/`, `openssl-src/`, and `build/openssl/` directories are unused.

## Debug symbols

Builds from this revision use `-O3 -DNDEBUG -g` for C and C++, retaining
Release optimization and embedding DWARF debug information in `libsrt.a`.
This applies to all platforms.
The release checks require DWARF compilation units with line-table references
in every architecture of the packaged XCFramework. Previously published
release assets are unchanged; this takes effect in the next release.

These static libraries do not ship a standalone dSYM. Archive the consuming
application with **Debug Information Format = DWARF with dSYM File**, preserve
its matching dSYM, and upload it to Firebase Crashlytics. The final app dSYM
must contain the linked library's debug information; merely updating the
package does not configure symbol uploads. Optimization can still affect
inlining and source-line accuracy. OpenSSL's separate upstream dSYM and its
limitations described above are unchanged.

## Swift Package Manager

After publishing with the workflow below, consumers can use this repository's
URL and version without specifying a checksum. The `libsrt` product carries
OpenSSL-Package and the C++ runtime; application code uses `import libsrt`.

```swift
dependencies: [
    .package(url: "https://github.com/HaishinKit/libsrt-xcframework.git", exact: "1.5.7")
],
targets: [
    .target(name: "MyApp", dependencies: [
        .product(name: "libsrt", package: "libsrt-xcframework")
    ])
]
```

Publish the version and its ZIP before using the example. For local development,
run `./build.sh local` after building and use `.package(path: "../libsrt-xcframework")`.

If declaring the libsrt binary target directly, add the OpenSSL product to the
consuming source target and link the C++ runtime. Binary targets cannot declare
these dependencies. For manual integration, embed and sign the selected dynamic
`OpenSSL.framework` in the application; do not merely link it. Verify the final
app archive includes its Privacy Manifest and required framework resources.

## Distribution

The same repository holds the build scripts, Swift package, version tags, and
GitHub Release assets. The build creates `libsrt.xcframework`, its ZIP,
and a `.sha256` file. Additional release assets are generated in `dist/licensing/`:

- `THIRD-PARTY-LICENSES.txt`: MPL text and original source notices, including UDT's BSD notice and MD5 notices.
- `SOURCE-NOTICE.txt`: source availability, revision URL, and modification status.
- `SOURCES.json`: source version/commit and the explicitly excluded development tool.
- `libsrt-sources.zip`: exact tracked SRT sources, original notices and upstream build files.
- `SHA256SUMS.json`: checksums linking these assets to the binary ZIP.

The first three files are also inside `libsrt.xcframework/Licenses/`, alongside
the existing `SRT-LICENSE`. Both Actions and `./build.sh publish TAG` upload all
five additional assets. The optional `abi-compliance-checker` submodule is not
used for this build and is excluded; its commit and reason are recorded.
OpenSSL is distributed separately through OpenSSL-Package.

### Release from GitHub Actions (recommended)

After this workflow is merged into `main`:

1. Open **Actions → Release XCFramework → Run workflow**.
2. Select **main** and enter a new package version, such as `1.5.7`.
3. Press **Run workflow**. A successful run publishes the tag and GitHub Release.

The workflow builds all platforms on an Apple silicon macOS 26 runner with
Xcode 26.6 and CMake 3.31.10, runs link/runtime/package checks, and generates the
remote manifest. It creates a release commit from the selected source commit,
adds the version tag to it, and publishes the ZIP in the same workflow.
Only the tag is pushed; `main` stays on its development manifest. Consumers
select the published version tag, not the `main` branch.

The input is the **package distribution version**, not a request to fetch a
different upstream version. Update the pinned libsrt version and its
metadata in a reviewed commit before releasing a new upstream version.
Only stable versions are accepted (`1.5.7` or `v1.5.7`). Existing tags and
releases (including drafts) are rejected before building. Runs are serialized.
The workflow uses the built-in `GITHUB_TOKEN` with `contents: write`; no personal
access token or signing secret is needed for this static XCFramework. Repository
or organization rules must allow Actions to create release tags and releases.

Before pushing the tag, the workflow saves a `release-vVERSION` artifact for
30 days containing the exact binary ZIP, checksum, generated manifest and
source/license assets. If publication
fails after the tag was pushed, do **not** rebuild or move the tag: download that
artifact, check out the existing tag, restore the ZIP/checksum at the repository
root, restore all five source/license assets under `dist/licensing/`, and run
`./build.sh publish TAG`. If a draft or partial Release already
exists, inspect and complete it using the saved files rather than rerunning the
whole workflow or overwriting published assets.

### Release from your Mac

1. Run `./build.sh` and `./build.sh verify`.
2. Run `./build.sh release v1.5.7` (choose a new, unused version tag).
   This computes the ZIP checksum and writes a remote binary target directly
   to the root `Package.swift`, with a copy in `dist/Package.swift`.
3. Review and commit the release changes, including `Package.swift`, and merge
   if required by your workflow. Tag that exact commit and push the commit/tag:

   ```sh
   git tag v1.5.7
   git push origin HEAD
   git push origin v1.5.7
   ```

4. From that commit, run `./build.sh publish v1.5.7` to upload the ZIP and its
   checksum file and source/license assets to this repository's GitHub Releases. This requires an
   authenticated GitHub CLI (`gh`).

`release` only prepares local files; `publish` is the explicit upload step.
Publishing checks the manifest URL/checksum, a clean working tree, and matching
local/remote tags at HEAD. It fails if a release already exists instead of
replacing its assets. Do not replace existing OpenSSL-bundled assets.

`support/Package.swift` is the development template for both modes. Keep
platforms, products, and dependencies there. `./build.sh local` restores it to
the root for local testing; that changes the working tree. Release tags must
contain the generated remote manifest, never the local one. The initial PR's
manifest remains local until an actual release is prepared. After release
preparation, do not rebuild the ZIP without regenerating the manifest and
committing its new checksum before tagging.

## Verification

```sh
./build.sh local
./build.sh verify
python3 tests/verify-release.py
python3 tests/verify-ci-release.py
python3 tests/verify-source-distribution.py
```


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

## License and app redistribution

Every architecture records its source revision before and after building.
Packaging requires a clean upstream checkout and matching records for all
architectures. After changing the source revision, rebuild all platforms before
packaging. Intentional local source changes require extending this process to
ship the modified sources with an accurate modification notice; they must not
be labeled as unmodified.

For apps distributing libsrt:

1. Preserve `THIRD-PARTY-LICENSES.txt` and `SOURCE-NOTICE.txt` in user-accessible
   app resources or accompanying documentation, such as an **Open Source
   Licenses** screen. Include the release URL for the version shipped, where
   its `libsrt-sources.zip` is available.
2. Preserve SRT's MPL source-availability notice and the original UDT/MD5 notices.
   Exact source revision URLs are in the notice, and the source ZIP retains
   the original headers and licenses.
3. Include the license and applicable notices for the actual resolved OpenSSL
   version separately. Different apps can resolve different OpenSSL 3.x
   releases; this source ZIP does not contain OpenSSL. Preserve its Privacy
   Manifest as described above.

SwiftPM does not automatically copy the top-level XCFramework `Licenses/`
folder into the final app. Verify that your app packaging includes the notices.
MPL's source requirements concern covered code and modifications, not automatic
publication of your entire application's source. See the
[Mozilla MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) and the license texts.


SRT is MPL-2.0; its license is included in the XCFramework. OpenSSL is separately
distributed under Apache-2.0 with its own license notices. Applications must
preserve the applicable notices for both dependencies.
