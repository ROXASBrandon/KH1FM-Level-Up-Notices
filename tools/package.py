"""Package the existing tested helper without rebuilding it."""
from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = 'KH1FM-Level-Up-Notices-v1.0.0.zip'
OUTPUT = ROOT / 'downloads'
EXCLUDED = {'.lib', '.pdb', '.obj', '.pyc'}


def payloads():
    for name in ('mod.yml', 'README.md', 'CHANGELOG.md', 'CREDITS.md', 'LICENSE'):
        yield ROOT / name
    for folder in ('scripts', 'native', 'tests', 'tools', 'images'):
        for path in sorted((ROOT / folder).rglob('*')):
            if path.is_file() and path.suffix not in EXCLUDED and '__pycache__' not in path.parts:
                yield path


def private_path(data):
    # Match private Windows and WSL home paths without embedding one here.
    markers = ('/'.join(('', 'mnt', 'c', 'Users')) + '/',
               chr(92).join(('C:', 'Users')) + chr(92))
    return any(marker.encode(enc) in data
               for marker in markers for enc in ('utf-8', 'utf-16le'))


def main():
    OUTPUT.mkdir(exist_ok=True)
    target = OUTPUT / ARCHIVE
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in payloads():
            name = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            assert not private_path(data), f'Private path in {name}'
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        for path in payloads():
            assert archive.read(path.relative_to(ROOT).as_posix()) == path.read_bytes()
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (OUTPUT / 'SHA256SUMS.txt').write_text(f'{digest}  {ARCHIVE}\n', encoding='utf-8')
    print(f'{digest}  {target}')


if __name__ == '__main__':
    main()
