"""Validate manual workflow input before spending time building."""
import json
import os
from pathlib import Path
import re
import subprocess

version = os.environ.get('RELEASE_VERSION', '')
if not re.fullmatch(r'v?(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)', version):
    raise SystemExit('Enter a stable version such as 1.5.7 or v1.5.7')
tag = 'v' + version.removeprefix('v')
repository = 'HaishinKit/libsrt-xcframework'
refs = subprocess.check_output(['git', 'ls-remote', f'https://github.com/{repository}.git',
                                f'refs/tags/{tag}'], text=True)
if refs.strip():
    raise SystemExit(f'{tag} already exists; existing tags are never replaced.')
# --paginate checks all releases, including drafts. API/network errors fail closed.
result = subprocess.check_output(['gh', 'api', '--paginate', '--slurp',
                                  f'repos/{repository}/releases?per_page=100'], text=True)
if any(release['tag_name'] == tag for page in json.loads(result) for release in page):
    raise SystemExit(f'A release or draft for {tag} already exists.')
with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:
    output.write(f'tag={tag}\n')
print(f'Release version validated: {tag}')
