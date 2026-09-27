"""Fetch the exact SwiftPM artifact and adapt its headers for CMake consumers."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import urllib.request

root = Path(__file__).resolve().parent.parent
base = root/'build/dependencies'
base.mkdir(parents=True, exist_ok=True)
archive = base/'OpenSSL-3.3.3001.xcframework.zip'
checksum = 'bd02bfeb7a01b63a5b210e3327b7eac3887badb73137f3ddc37de504e6555cfb'
url = 'https://github.com/krzyzanowskim/OpenSSL/releases/download/3.3.3001/OpenSSL.xcframework.zip'
if not archive.exists():
    download = archive.with_suffix('.download')
    urllib.request.urlretrieve(url, download)
    if hashlib.sha256(download.read_bytes()).hexdigest() != checksum:
        download.unlink()
        raise SystemExit('OpenSSL download checksum mismatch')
    download.rename(archive)
if hashlib.sha256(archive.read_bytes()).hexdigest() != checksum:
    raise SystemExit('OpenSSL archive checksum mismatch; remove it and retry')
framework = base/'OpenSSL.xcframework'
if framework.exists():
    shutil.rmtree(framework)
subprocess.run(['/usr/bin/ditto', '-x', '-k', str(archive), str(base)], check=True)
subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(framework)], check=True)
platforms = {
    'iphoneos': 'ios-arm64', 'iphonesimulator': 'ios-arm64_x86_64-simulator',
    'macosx': 'macos-arm64_x86_64', 'macosx_catalyst': 'ios-arm64_x86_64-maccatalyst',
    'appletvos': 'tvos-arm64', 'appletvsimulator': 'tvos-arm64_x86_64-simulator',
    'visionos': 'xros-arm64', 'visionsimulator': 'xros-arm64_x86_64-simulator',
}
for platform, identifier in platforms.items():
    source = framework/identifier/'OpenSSL.framework'
    destination = base/'sdk'/platform
    if destination.exists():
        shutil.rmtree(destination)
    headers = destination/'include/openssl'
    headers.mkdir(parents=True)
    # Upstream framework headers use <OpenSSL/...>; SRT uses <openssl/...>.
    # Adapt include spelling only in a build-local copy, preserving the signed framework.
    for header in (source/'Headers').glob('*.h'):
        (headers/header.name).write_text(header.read_text().replace('<OpenSSL/', '<openssl/'))
    (destination/'OpenSSL').symlink_to((source/'OpenSSL').resolve())
print('OpenSSL-Package 3.3.3001 / OpenSSL 3.3.3: checksum and signature verified; build headers prepared.')
