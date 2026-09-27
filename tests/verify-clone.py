#!/usr/bin/env python3
"""Exercise pinned-tag preparation with real shallow repositories and no network."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as name:
    base = Path(name)
    def run(directory, *args, succeeds=True):
        result = subprocess.run(args, cwd=directory, capture_output=True, text=True)
        assert (result.returncode == 0) == succeeds, result.stdout + result.stderr
        return result.stdout.strip()
    upstream = base/'upstream'; upstream.mkdir()
    run(upstream, 'git','init','-b','main')
    run(upstream, 'git','config','user.name','Clone test')
    run(upstream, 'git','config','user.email','test@example.invalid')
    (upstream/'source.txt').write_text('release\n')
    run(upstream, 'git','add','source.txt')
    run(upstream, 'git','commit','-m','Release source')
    run(upstream, 'git','tag','-a','v1.5.7','-m','Pinned release')
    expected = run(upstream, 'git','rev-parse','HEAD')
    (upstream/'source.txt').write_text('newer default branch\n')
    run(upstream, 'git','commit','-am','Advance default branch')
    for existing in (False, True):
        work = base/('existing' if existing else 'fresh')
        scripts = work/'scripts/build'; scripts.mkdir(parents=True)
        script = (root/'scripts/build/build-clone.sh').read_text().replace(
            'https://github.com/Haivision/srt.git', upstream.as_uri())
        (scripts/'build-clone.sh').write_text(script)
        if existing:
            run(work, 'git','clone','--depth','1','--no-tags',upstream.as_uri(),'srt')
            # Reproduce the failed runner's FETCH_HEAD-only state.
            run(work/'srt', 'git','fetch','--depth','1','origin','v1.5.7')
            run(work/'srt', 'git','rev-parse','--verify','refs/tags/v1.5.7',succeeds=False)
        for _ in range(2):
            run(work, 'bash','scripts/build/build-clone.sh')
            assert run(work/'srt','git','rev-parse','HEAD') == expected
            assert run(work/'srt','git','rev-parse','refs/tags/v1.5.7^{commit}') == expected
            run(work/'srt','git','symbolic-ref','-q','HEAD',succeeds=False)
        (work/'srt/source.txt').write_text('local modification\n')
        run(work, 'bash','scripts/build/build-clone.sh',succeeds=False)
        assert (work/'srt/source.txt').read_text() == 'local modification\n'
print('Fresh shallow clone, FETCH_HEAD-only recovery, repeat runs and dirty-tree protection passed.')
