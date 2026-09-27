#!/usr/bin/env python3
"""Verify all XCFramework slices, then run encrypted loopback on this Mac."""
from pathlib import Path
import concurrent.futures
import plistlib
import os
import re
import subprocess
root = Path(__file__).resolve().parent.parent
(root/'build/validation').mkdir(parents=True, exist_ok=True)
framework = root/'libsrt.xcframework'
openssl = Path(os.environ.get('OPENSSL_XCFRAMEWORK', str(root/'build/dependencies/OpenSSL.xcframework')))
slices = plistlib.loads((framework/'Info.plist').read_bytes())['AvailableLibraries']
targets = {
    'ios-arm64-maccatalyst': ('macosx', 'arm64-apple-ios14.0-macabi'),
    'ios-arm64': ('iphoneos', 'arm64-apple-ios13.0'),
    'ios-arm64-simulator': ('iphonesimulator', 'arm64-apple-ios14.0-simulator'),
    'tvos-arm64': ('appletvos', 'arm64-apple-tvos13.0'),
    'tvos-arm64-simulator': ('appletvsimulator', 'arm64-apple-tvos14.0-simulator'),
    'macos-arm64': ('macosx', 'arm64-apple-macos11.0'),
    'xros-arm64': ('xros', 'arm64-apple-xros1.3'),
    'xros-arm64-simulator': ('xrsimulator', 'arm64-apple-xros1.3-simulator'),
}
assert len(slices) == 8
platforms = {
    'macos-arm64': 1, 'ios-arm64': 2, 'tvos-arm64': 3,
    'ios-arm64-maccatalyst': 6, 'ios-arm64-simulator': 7,
    'tvos-arm64-simulator': 8, 'xros-arm64': 11,
    'xros-arm64-simulator': 12,
}

def dependency(name):
    identifiers = {
        'ios-arm64-maccatalyst': 'ios-arm64_x86_64-maccatalyst',
        'ios-arm64-simulator': 'ios-arm64_x86_64-simulator',
        'tvos-arm64-simulator': 'tvos-arm64_x86_64-simulator',
        'macos-arm64': 'macos-arm64_x86_64',
        'xros-arm64-simulator': 'xros-arm64_x86_64-simulator',
    }
    return openssl/identifiers.get(name, name)

def verify(item):
    name = item['LibraryIdentifier']; directory = framework/name
    sdk, target = targets[name]
    assert item['SupportedArchitectures'] == ['arm64']
    archs = subprocess.check_output(['xcrun','lipo','-archs',str(directory/'libsrt.a')],text=True).strip()
    assert archs == 'arm64', archs
    load_commands = subprocess.check_output(
        ['xcrun', 'otool', '-l', str(directory/'libsrt.a')], text=True)
    actual_platforms = {int(value) for value in re.findall(r'^\s+platform (\d+)$', load_commands, re.MULTILINE)}
    assert actual_platforms == {platforms[name]}, (name, actual_platforms)
    definitions = subprocess.check_output(['xcrun', 'nm', '-gU', str(directory/'libsrt.a')], text=True)
    assert not re.search(r'\b_(?:SSL_|OPENSSL_|OpenSSL_|EVP_|CRYPTO_|RAND_)', definitions), name + ': bundled OpenSSL symbols'
    assert ('OpenSSL '+os.environ.get('EXPECTED_OPENSSL_VERSION', '3.3.3')).encode() in (dependency(name)/'OpenSSL.framework/OpenSSL').read_bytes(), name + ': OpenSSL version mismatch'
    sdkpath = subprocess.check_output(['xcrun','--sdk',sdk,'--show-sdk-path'],text=True).strip()
    command = ['xcrun','swiftc',str(root/'tests/smoke.swift'),'-target',target,'-sdk',sdkpath,'-I',str(directory/'Headers'),'-L',str(directory),'-lsrt','-F',str(dependency(name)),'-framework','OpenSSL','-Xlinker','-rpath','-Xlinker',str(dependency(name)),'-lc++','-module-cache-path',str(root/'build/validation/cache'/name),'-o',str(root/'build/validation'/name)]
    result = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (root/'build/validation'/f'{name}.log').write_text(result.stdout)
    assert result.returncode == 0, name + ': ' + result.stdout[-3000:]
    return name+': Swift compile/link OK'
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for result in pool.map(verify, slices): print(result,flush=True)
for name, platform in [('macos-arm64', 'macosx'), ('ios-arm64-maccatalyst', 'macosx_catalyst')]:
    subprocess.run([str(root/'build/validation'/name)],check=True,timeout=20)
    directory = framework/name
    sdk, target = targets[name]
    sdkpath = subprocess.check_output(['xcrun','--sdk',sdk,'--show-sdk-path'],text=True).strip()
    executable = root/'build/validation'/('encrypted-'+name)
    subprocess.run(['xcrun','clang++','-std=c++11','-target',target,'-isysroot',sdkpath,
        '-I',str(directory/'Headers'),'-I',str(root/'build/dependencies/sdk'/platform/'include'),
        str(root/'tests/encrypted-loopback.cpp'),str(directory/'libsrt.a'),'-F',str(dependency(name)),'-framework','OpenSSL','-Wl,-rpath,'+str(dependency(name)),'-o',str(executable)],check=True)
    subprocess.run([str(executable), os.environ.get('EXPECTED_OPENSSL_VERSION', '3.3.3')],check=True,timeout=20)
print('All eight slices and both encrypted runtime checks passed.',flush=True)
