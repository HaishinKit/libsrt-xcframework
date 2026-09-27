#!/usr/bin/env python3
"""Verify shipped notices and exact Git/submodule source contents, without publishing."""
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('sources', root/'scripts/source-distribution.py')
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)
sources.check()
records = json.loads((sources.OUT/'SOURCES.json').read_text())
assert records == sources.snapshot()
license_text = (sources.OUT/'THIRD-PARTY-LICENSES.txt').read_text()
assert 'The Board of Trustees of the University of Illinois' in license_text
assert 'Aladdin Enterprises' in license_text
assert records[0]['excludedSubmodules'][0]['path'] == 'submodules/abi-compliance-checker'
with zipfile.ZipFile(sources.OUT/'libsrt-sources.zip') as bundle:
    assert len(bundle.namelist()) == len(set(bundle.namelist()))
    assert not any('.git' in Path(name).parts for name in bundle.namelist())
    for r in records:
        prefix = 'libsrt/' + (r['path']+'/' if r['path'] != '.' else '')
        raw = sources.git(sources.SOURCE/r['path'], 'archive', '--format=zip', '--prefix='+prefix, r['commit'])
        with zipfile.ZipFile(io.BytesIO(raw)) as original:
            for entry in original.infolist():
                if not entry.is_dir():
                    assert bundle.read(entry.filename) == original.read(entry), entry.filename
        assert r['commit'] in (sources.OUT/'SOURCE-NOTICE.txt').read_text()
        assert (sources.SOURCE/r['path']/r['licenseFile']).read_text() in (sources.OUT/'THIRD-PARTY-LICENSES.txt').read_text()
    for name in sources.OUTPUTS[:3]:
        assert bundle.read('distribution/'+name) == (sources.OUT/name).read_bytes()

with tempfile.TemporaryDirectory() as name:
    temp = Path(name)
    shutil.copytree(sources.OUT, temp/'dist/licensing')
    shutil.copyfile(root/'libsrt.xcframework.zip', temp/'libsrt.xcframework.zip')
    sources.ROOT = temp
    sources.OUT = temp/'dist/licensing'
    def rejected(call):
        try:
            call()
        except SystemExit:
            return
        raise AssertionError('Expected rejection')
    p = sources.OUT/'SOURCE-NOTICE.txt'
    original = p.read_bytes(); p.write_bytes(original+b'changed')
    rejected(sources.check)
    p.write_bytes(original)
    sources.check()
    with (temp/'libsrt.xcframework.zip').open('ab') as f:
        f.write(b'changed')
    rejected(sources.check)
    # A source tree cannot be packaged as a previously built binary without matching records.
    sources.snapshot = lambda: records
    rejected(sources.package)
    for platform in sources.BUILDS:
        p=temp/'build'/platform/'SOURCES.json';p.parent.mkdir(parents=True);p.write_text('[]')
    rejected(sources.package)
print('SRT source tree, license texts, bundled notices, and artifact mismatch checks passed.')
