#!/usr/bin/env python3
"""Test workflow preflight and release commits without network/publication."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as name:
    work = Path(name)
    (work / 'bin').mkdir()
    for command, body in {
        'git': 'if [ "$CASE" = tag ]; then echo "commit refs/tags/v1.5.7"; fi',
        'gh': '''case "$CASE" in
 draft) echo '[[{"tag_name":"v1.5.7","draft":true}]]' ;;
 error) exit 1 ;;
 *) echo '[[]]' ;;
esac''',
    }.items():
        p = work / 'bin' / command
        p.write_text('#!/bin/bash\n' + body + '\n'); p.chmod(0o755)
    for version, case, success in [('1.5.7','ok',True), ('v1.5.7','ok',True),
                                  ('1.5.7','tag',False), ('1.5.7','draft',False),
                                  ('1.5.7','error',False), ('01.2.3','ok',False),
                                  ('$(touch unwanted)','ok',False), ('1.5.7\nextra','ok',False)]:
        output = work / 'output'
        output.unlink(missing_ok=True)
        env = dict(os.environ, PATH=str(work/'bin')+os.pathsep+os.environ['PATH'],
                   RELEASE_VERSION=version, CASE=case, GITHUB_OUTPUT=str(output))
        result = subprocess.run(['python3', str(root/'scripts/ci-release.py')], cwd=work,
                                env=env, capture_output=True, text=True)
        assert (result.returncode == 0) == success, result.stdout + result.stderr
        assert output.exists() == success
        if success:
            assert output.read_text() == 'tag=v1.5.7\n'
    assert not (work/'unwanted').exists()

with tempfile.TemporaryDirectory() as name:
    work = Path(name)
    def run(*args, succeeds=True):
        result = subprocess.run(args, cwd=work, capture_output=True, text=True)
        assert (result.returncode == 0) == succeeds, result.stdout + result.stderr
        return result.stdout.strip()
    for folder in ['scripts','support']:
        (work/folder).mkdir()
    for file in ['scripts/commit-release.sh','scripts/release-manifest.py','support/Package.swift']:
        shutil.copyfile(root/file, work/file)
    (work/'.gitignore').write_text('/dist/\n/*.zip\n/*.sha256\n')
    (work/'README.md').write_text('source\n')
    (work/'libsrt.xcframework.zip').write_bytes(b'fixture artifact')
    run('python3','scripts/release-manifest.py','local')
    run('git','init','-b','main')
    run('git','config','user.email','test@example.invalid')
    run('git','config','user.name','Release test')
    run('git','add','.')
    run('git','commit','-m','Source')
    source = run('git','rev-parse','HEAD')
    run('git','checkout','--detach')
    run('python3','scripts/release-manifest.py','release','v1.5.7')
    (work/'README.md').write_text('unexpected modification\n')
    run('bash','scripts/commit-release.sh','v1.5.7',succeeds=False)
    assert run('git','rev-parse','HEAD') == source
    (work/'README.md').write_text('source\n')
    run('bash','scripts/commit-release.sh','v1.5.7')
    assert run('git','rev-parse','main') == source
    assert run('git','rev-parse','v1.5.7') == run('git','rev-parse','HEAD')
    assert run('git','diff','--name-only',source,'HEAD') == 'Package.swift'
    assert run('git','status','--porcelain') == ''
    run('python3','scripts/release-manifest.py','check','v1.5.7')
    run('bash','scripts/commit-release.sh','v1.5.7',succeeds=False)
print('Workflow input, existing release rejection, and detached release commit/tag tests passed.')
