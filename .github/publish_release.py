"""Publish verified, committed release files using the repository workflow token."""
import hashlib
import io
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

REPO = os.environ['GITHUB_REPOSITORY']
COMMIT = os.environ['GITHUB_SHA']
API = f'https://api.github.com/repos/{REPO}'
ARCHIVE = 'KH1FM-Level-Up-Notices-v1.0.0.zip'
TAG = 'v1.0.0'
HEADERS = {'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
           'Accept': 'application/vnd.github+json',
           'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'KH1FM-Mod-Release'}
BODY = '''Gives you more time to read your level-up rewards. Original party level-up cards hold for eight seconds, then fade normally. Includes stat and learned-ability rewards.

Gameplay-tested: party level-ups, consecutive level-ups, ability/stat rewards, pauses, transitions, Next Level Tracker compatibility, and removal restoring original timing. Uses the same native DLL as the tested preview.

Requires Kingdom Hearts Final Mix Steam Global/WW 1.0.0.2 and working LuaBackend. For OpenKH Mod Manager, Panacea must also be configured.

Download KH1FM-Level-Up-Notices-v1.0.0.zip below. Close KH1, import the ZIP without extracting it through Mods > Install new mods > Select and install Mod Archive or Lua Script, enable Level Up Notices - 8 Seconds, then Build and Run. GitHub and manual LuaBackend installation methods are documented in the README. Keep only one copy enabled.

To remove: close KH1, disable the mod, rebuild and restart. Saves and rewards are not edited. The original five-card queue limit remains. Other regions, game versions and HUD replacements are unsupported or unverified; a separate clean-PC installation is untested.

SHA-256 checksums are attached. Use the named mod ZIP rather than GitHub's automatically generated source archives.'''


def request(url, method='GET', data=None, content_type='application/json'):
    payload = json.dumps(data).encode() if isinstance(data, dict) else data
    req = urllib.request.Request(url, data=payload, method=method,
                                 headers={**HEADERS, 'Content-Type': content_type})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def raw(path):
    url = f'https://raw.githubusercontent.com/{REPO}/{COMMIT}/' + urllib.parse.quote(path)
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def main():
    archive_data = raw('downloads/' + ARCHIVE)
    digest = hashlib.sha256(archive_data).hexdigest()
    assert digest == os.environ['ZIP_SHA256'], 'Unexpected release archive'
    checksum_data = raw('downloads/SHA256SUMS.txt')
    assert checksum_data.decode().strip() == f'{digest}  {ARCHIVE}'
    with zipfile.ZipFile(io.BytesIO(archive_data)) as z:
        assert z.testzip() is None
        assert {'mod.yml', 'README.md', 'LICENSE', 'CHANGELOG.md',
                'scripts/kh1_level_up_notices.lua',
                'scripts/io_packages/kh1_level_up_notices.dll'} <= set(z.namelist())
        for name in z.namelist():
            assert not name.startswith('/') and '..' not in Path(name).parts
            assert z.read(name) == raw(name), f'Archive differs from repository: {name}'
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            for name in ('native/timing.h', 'tests/timing_test.c'):
                (temp / Path(name).name).write_bytes(z.read(name))
            subprocess.run(['cc', '-O2', '-UNDEBUG', '-Wall', '-Wextra', '-Werror',
                            '-I', str(temp), str(temp / 'timing_test.c'),
                            '-o', str(temp / 'timing-test')], check=True)
            subprocess.run([str(temp / 'timing-test')], check=True)
    try:
        release = request(API + '/releases/tags/' + TAG)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        release = request(API + '/releases', 'POST', {
            'tag_name': TAG, 'target_commitish': COMMIT,
            'name': 'Level Up Notices – 8 Seconds v1.0.0', 'body': BODY,
            'draft': True, 'prerelease': False})
    existing = {asset['name']: asset for asset in release.get('assets', [])}
    for name, data, kind in ((ARCHIVE, archive_data, 'application/zip'),
                             ('SHA256SUMS.txt', checksum_data, 'text/plain')):
        expected = 'sha256:' + hashlib.sha256(data).hexdigest()
        if name in existing:
            asset = existing[name]
        else:
            assert release['draft'], 'Refusing to change an incomplete published release'
            url = release['upload_url'].split('{', 1)[0] + '?' + urllib.parse.urlencode({'name': name})
            asset = request(url, 'POST', data, kind)
        assert asset['state'] == 'uploaded' and asset['size'] == len(data)
        assert asset.get('digest') == expected, 'Uploaded asset differs'
    if release['draft']:
        release = request(API + '/releases/' + str(release['id']), 'PATCH', {'draft': False})
    assert not release['draft']
    print('Published ' + release['html_url'])
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as summary:
        summary.write(f"Release: {release['html_url']}\n\nZIP SHA256: `{digest}`\n")


if __name__ == '__main__':
    main()
