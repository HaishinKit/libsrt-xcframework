# libsrt.xcframework
- The libsrt with xcframework project.
- This is a project to make libsrt easier to use with Swift Package Manager (SPM).
> [!NOTE]
> This is provided for use with HaishinKit. It does not prevent you from using it individually in your own environment.

## Platforms
|iOS|tvOS|macOS|visionOS|watchOS|macOS catalyst|
|:-:|:-:|:-:|:-:|:-:|:-:|
|13.0+|13.0+|10.15+|1.0+|-|-|
- [Simulator on Intel Mac not supported.](https://github.com/HaishinKit/HaishinKit.swift/issues/1571)

## Usage
You can use it from SPM as follows.
- ${version} refers to the release version v1.5.4.
- The checksum is listed in the RELEASE notes.
```Package.swift
// swift-tools-version: 5.7
import PackageDescription

let package = Package(
  dependencies: [
  ],
  targets: [
    .binaryTarget(
      name: "libsrt",
      url: "https://github.com/HaishinKit/libsrt-xcframework/releases/download/${version}/libsrt.xcframework.zip",
      checksum: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    ),
  ]
)
```

The checksum can be obtained using the following command:
```sh
$ swift package compute-checksum /path/to/libsrt.xcframework.zip
```

## License
- libsrt.xcframeworks is MPLv2.0 License
