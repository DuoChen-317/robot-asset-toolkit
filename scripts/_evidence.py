"""Small I/O helpers shared by read-only simulation evidence tools."""
import hashlib
import json
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def check_new_report(path):
    if path is not None and Path(path).exists():
        raise ValueError('Report already exists: ' + str(path))


def emit(report, path=None):
    text = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
    print(text, end='')
