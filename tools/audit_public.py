"""Check the public source tree and release package without printing sensitive matches."""
from __future__ import annotations

import argparse
import io
import json
import marshal
from pathlib import Path
import re
import subprocess
import sys
from types import CodeType
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRECTORIES = {'.git', '.local', '.venv', '.impeccable', '.taste-skill', '.tools', '__pycache__'}
PHOTO_EXTENSIONS = {'.cr2', '.cr3', '.crw', '.nef', '.nrw', '.arw', '.raf', '.orf', '.rw2', '.pef', '.dng', '.raw', '.jpg', '.jpeg', '.heic', '.heif', '.tif', '.tiff', '.webp', '.gif'}
RULES = {
    'private-key': rb'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----',
    'github-token': rb'\bgh[pousr]_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b',
    'cloud-access-key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'google-api-key': rb'\bAIza[A-Za-z0-9_-]{35}\b',
    'slack-token': rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b',
    'openai-key': rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}\b',
    'credential-url': rb'https?://[^\s/:@]+:[^\s/@]+@[^\s/]+',
}
COMPILED_RULES = {name: re.compile(pattern) for name, pattern in RULES.items()}
USER_PATH = re.compile(rb'(?i)(?:[a-z]:[/\\](?:users|documents and settings)[/\\]|/(?:users|home)/)([^\\/\s\x00\"\x27]+)')
PUBLIC_BUILD_USERS = {b'runner', b'runneradmin', b'public', b'default', b'buildbot'}
# Upstream standard-library examples and unmodified wheel debug metadata are
# public upstream content. The build machine's own profile is always rejected.
UPSTREAM_PATH_CONTEXTS = {
    'Revela.exe/numpy.lib._datasource',
    'Revela.exe/pydoc_data.topics',
    '_internal/clr_loader/ffi/dlls/amd64/ClrLoader.dll',
    '_internal/clr_loader/ffi/dlls/x86/ClrLoader.dll',
}


class Audit:
    def __init__(self):
        self.findings = set()
        self.count = 0

    def fail(self, name: str, rule: str) -> None:
        self.findings.add((name, rule))

    def inspect(self, name: str, raw: bytes) -> None:
        self.count += 1
        profile = str(Path.home()).encode('utf-8').lower()
        for data in (raw, raw.replace(b'\x00', b'')):
            for rule, pattern in COMPILED_RULES.items():
                if pattern.search(data):
                    self.fail(name, rule)
            normalized = data.replace(b'\\\\', b'\\')
            if profile in normalized.lower() or profile.replace(b'\\', b'/') in normalized.lower():
                self.fail(name, 'local-profile-path')
            for match in USER_PATH.finditer(normalized):
                if match.group(1).lower() not in PUBLIC_BUILD_USERS and name not in UPSTREAM_PATH_CONTEXTS:
                    self.fail(name, 'user-profile-path')

    def code(self, name: str, value) -> None:
        if isinstance(value, CodeType):
            self.inspect(name + ':filename', value.co_filename.encode('utf-8'))
            for const in value.co_consts:
                self.code(name, const)
        elif isinstance(value, str):
            self.inspect(name, value.encode('utf-8'))
        elif isinstance(value, bytes):
            self.inspect(name, value)
        elif isinstance(value, (tuple, frozenset)):
            for element in value:
                self.code(name, element)

    def file(self, path: Path, name: str, package=False) -> None:
        parts = Path(name.replace('\\', '/')).parts
        lower = path.suffix.lower()
        if any(part in PRIVATE_DIRECTORIES for part in parts):
            self.fail(name, 'local-or-cache-file')
        if lower in {'.log', '.csv', '.pem', '.key', '.p12', '.pfx', '.kdbx'} or path.name.startswith('.env'):
            self.fail(name, 'private-file-type')
        if lower in PHOTO_EXTENSIONS or (lower == '.png' and 'assets' not in parts):
            self.fail(name, 'photograph-or-result')
        if 'licenses' in parts and lower in {'.py', '.pyc', '.pyo'}:
            self.fail(name, 'code-in-license-directory')
        raw = path.read_bytes()
        self.inspect(name, raw)
        if lower == '.zip':
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                for item in archive.infolist():
                    if not item.is_dir():
                        self.inspect(name + '/' + item.filename, archive.read(item))
        if package and path.name == 'Revela.exe':
            from PyInstaller.archive.readers import CArchiveReader
            archive = CArchiveReader(str(path))
            for entry, record in archive.toc.items():
                if record[-1] in ('s', 'm', 'M'):
                    self.code(name + '/' + entry, marshal.loads(archive.extract(entry)))
                elif entry.endswith('.pyz'):
                    embedded = archive.open_embedded_archive(entry)
                    for module in embedded.toc:
                        code = embedded.extract(module)
                        if code is not None:
                            self.code(name + '/' + module, code)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', action='store_true')
    parser.add_argument('--package', type=Path)
    args = parser.parse_args()
    if not args.source and args.package is None:
        parser.error('Specify --source or --package.')
    audit = Audit()
    if args.source:
        listed = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT)
        names = sorted(set(listed.decode('utf-8').split('\x00')) - {''})
        for name in names:
            path = ROOT / name
            if path.is_file():
                audit.file(path, name)
    if args.package is not None:
        folder = args.package.resolve()
        if not folder.is_dir():
            raise RuntimeError('Package directory does not exist.')
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                audit.file(path, path.relative_to(folder).as_posix(), package=True)
    print(json.dumps({'inspected': audit.count, 'findings': [{'file': name, 'rule': rule} for name, rule in sorted(audit.findings)]}, ensure_ascii=False))
    return int(bool(audit.findings))


if __name__ == '__main__':
    sys.exit(main())
