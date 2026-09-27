// swift-tools-version: 5.9
import PackageDescription

// Local development manifest. Release manifests are generated separately.
let package = Package(
    name: "libsrt",
    platforms: [.iOS(.v13), .tvOS(.v13), .macOS(.v11), .macCatalyst(.v14), .visionOS("1.3")],
    products: [.library(name: "libsrt", targets: ["SRT"])],
    dependencies: [.package(url: "https://github.com/krzyzanowskim/OpenSSL-Package.git", "3.3.3001"..<"4.0.0")],
    targets: [
        .binaryTarget(name: "libsrt", path: "libsrt.xcframework"),
        .target(
            name: "SRT",
            dependencies: ["libsrt", .product(name: "OpenSSL", package: "OpenSSL-Package")],
            linkerSettings: [.linkedLibrary("c++")]
        )
    ]
)
