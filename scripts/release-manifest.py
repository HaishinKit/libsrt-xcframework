"""Select local/release manifests; keep a single template for both modes."""
import hashlib
from pathlib import Path
import re
import sys

mode = sys.argv[1] if len(sys.argv) > 1 else ''
template = Path('support/Package.swift').read_text()
if mode == 'local':
    Path('Package.swift').write_text(template)
    print('Package.swift now uses the local XCFramework.')
elif mode == 'check-local':
    if Path('Package.swift').read_text() != template:
        raise SystemExit('Run ./build.sh local before testing locally.')
elif mode in ('release', 'check'):
    tag = sys.argv[2] if len(sys.argv) == 3 else ''
    if not re.fullmatch(r'v?(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?', tag):
        raise SystemExit('Provide a version tag, for example v1.5.7 or v1.5.7-1')
    archive = Path('libsrt.xcframework.zip')
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    url = f'https://github.com/HaishinKit/libsrt-xcframework/releases/download/{tag}/{archive.name}'
    manifest, count = re.subn(
        r'\.binaryTarget\(name: "libsrt", path: "libsrt.xcframework"\)',
        f'.binaryTarget(name: "libsrt", url: "{url}", checksum: "{checksum}")',
        template.replace('// Local development manifest. Release manifests are generated separately.\n', ''))
    if count != 1:
        raise SystemExit('Expected exactly one local binary target in support/Package.swift')
    checksum_file = archive.with_suffix(archive.suffix + '.sha256')
    if mode == 'check':
        if Path('Package.swift').read_text() != manifest:
            raise SystemExit('Release manifest does not match the tag and ZIP. Run ./build.sh release TAG.')
        if checksum_file.read_text().strip() != checksum:
            raise SystemExit('ZIP checksum file mismatch. Run ./build.sh release TAG.')
        print('Release URL and ZIP checksum verified.')
    else:
        Path('dist').mkdir(exist_ok=True)
        Path('dist/Package.swift').write_text(manifest)
        Path('Package.swift').write_text(manifest)
        checksum_file.write_text(checksum + '\n')
        print(f'Prepared Package.swift and dist/Package.swift for {tag}; nothing uploaded.')
        print('Commit Package.swift, tag that commit, push the commit and tag, then run ./build.sh publish TAG.')
else:
    raise SystemExit('Usage: release-manifest.py local|check-local|release TAG|check TAG')
