// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "libsrt",
    platforms: [.iOS(.v13), .tvOS(.v13), .macOS(.v11), .macCatalyst(.v14), .visionOS("1.3"), .watchOS(.v8)],
    products: [.library(name: "libsrt", targets: ["SRT"])],
    dependencies: [.package(url: "https://github.com/krzyzanowskim/OpenSSL-Package.git", "3.3.3001"..<"4.0.0")],
    targets: [
        .binaryTarget(name: "libsrt", url: "https://github.com/HaishinKit/libsrt-xcframework/releases/download/v1.5.7/libsrt.xcframework.zip", checksum: "1761d2c2dcb94014af68417b0ed254dfc5af730df985beb7b681ba202fb5af8d"),
        .target(
            name: "SRT",
            dependencies: ["libsrt", .product(name: "OpenSSL", package: "OpenSSL-Package")],
            linkerSettings: [.linkedLibrary("c++")]
        )
    ]
)
