#!/usr/bin/env python3
"""Exercise manifest switching and reject mismatched release artifacts without publishing."""
import hashlib
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
script = root / 'scripts/release-manifest.py'
with tempfile.TemporaryDirectory() as name:
    work = Path(name)
    (work / 'support').mkdir()
    template = (root / 'support/Package.swift').read_text()
    (work / 'support/Package.swift').write_text(template)
    archive = work / 'libsrt.xcframework.zip'
    archive.write_bytes(b'release fixture')
    def run(*args, succeeds=True):
        result = subprocess.run(['python3', str(script), *args], cwd=work,
                                capture_output=True, text=True)
        assert (result.returncode == 0) == succeeds, result.stdout + result.stderr
    run('local')
    run('check-local')
    run('release', '../invalid', succeeds=False)
    assert (work / 'Package.swift').read_text() == template
    run('release', 'v1.5.7')
    manifest = (work / 'Package.swift').read_text()
    assert '/releases/download/v1.5.7/libsrt.xcframework.zip' in manifest
    assert hashlib.sha256(archive.read_bytes()).hexdigest() in manifest
    assert '.product(name: "OpenSSL", package: "OpenSSL-Package")' in manifest
    assert manifest == (work / 'dist/Package.swift').read_text()
    run('check', 'v1.5.7')
    run('check-local', succeeds=False)
    run('check', 'v0.24.7', succeeds=False)
    archive.write_bytes(b'changed artifact')
    run('check', 'v1.5.7', succeeds=False)
    run('release', 'v1.5.7')
    checksum = work / 'libsrt.xcframework.zip.sha256'
    checksum.write_text('incorrect\n')
    run('check', 'v1.5.7', succeeds=False)
    run('local')
    assert (work / 'Package.swift').read_text() == template
print('Manifest switching, tag validation, and stale artifact rejection passed; nothing published.')

# Replace Git/GitHub commands inside an isolated fixture: no network or release creation.
import os
import shutil
with tempfile.TemporaryDirectory() as name:
    work = Path(name)
    for directory in ['scripts', 'support', 'bin']:
        (work / directory).mkdir()
    shutil.copyfile(root / 'build.sh', work / 'build.sh')
    shutil.copyfile(script, work / 'scripts/release-manifest.py')
    shutil.copyfile(root / 'support/Package.swift', work / 'support/Package.swift')
    (work / 'libsrt.xcframework.zip').write_bytes(b'publish fixture')
    subprocess.run(['bash', 'build.sh', 'release', 'v1.5.7'], cwd=work, check=True,
                   stdout=subprocess.DEVNULL)
    git = work / 'bin/git'
    git.write_text('''#!/bin/bash
case "$1" in
 status) if [ "${CASE:-}" = dirty ]; then echo ' M README.md'; fi ;;
 rev-parse) if [ "$2" != HEAD ] && [ "${CASE:-}" = tag ]; then echo other; else echo commit; fi ;;
 ls-remote) if [ "${CASE:-}" != remote ]; then printf 'commit\\trefs/tags/v1.5.7\\n'; fi ;;
 *) exit 98 ;;
esac
''')
    gh = work / 'bin/gh'
    gh.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > gh-arguments\n')
    git.chmod(0o755); gh.chmod(0o755)
    for case in ['dirty', 'tag', 'remote', 'ok']:
        environment = dict(os.environ, PATH=str(work / 'bin') + os.pathsep + os.environ['PATH'], CASE=case)
        result = subprocess.run(['bash', 'build.sh', 'publish', 'v1.5.7'], cwd=work,
                                env=environment, capture_output=True, text=True)
        assert (result.returncode == 0) == (case == 'ok'), result.stdout + result.stderr
        assert (work / 'gh-arguments').exists() == (case == 'ok')
    args = (work / 'gh-arguments').read_text().splitlines()
    assert args[:3] == ['release', 'create', 'v1.5.7']
    assert '--verify-tag' in args
    assert args[-2:] == ['libsrt.xcframework.zip', 'libsrt.xcframework.zip.sha256']
print('Publish preflight and upload arguments verified with isolated Git/GitHub stubs.')
