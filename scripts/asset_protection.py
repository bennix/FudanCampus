"""Fail before regenerating existing standalone or accepted building assets."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify_protected_sources(root=ROOT):
    config = json.loads((root / 'assets/protected-buildings.json').read_text(encoding='utf-8'))
    for relative, expected in config['files'].items():
        path = root / relative
        data = path.read_bytes() if path.exists() else b''
        if relative in config.get('textFiles', []):
            data = data.replace(b'\r\n', b'\n')
        if not path.exists() or hashlib.sha256(data).hexdigest() != expected:
            raise RuntimeError(f'Protected baseline changed: {relative}. Review it before exporting.')
    return config


def assert_export_allowed(only_bid=None, root=ROOT):
    config_path = root / 'assets/protected-buildings.json'
    protected = verify_protected_sources(root) if config_path.exists() else {'buildings': {}}
    if only_bid is not None:
        if str(only_bid) in protected['buildings']:
            raise RuntimeError(f'Building {only_bid} is an accepted local model; use its dedicated integration script.')
        return
    existing = list((root / 'assets/buildings').glob('*.blend'))
    existing += list((root / 'web/public/models/buildings').glob('*.glb'))
    if existing or protected['buildings']:
        raise RuntimeError('Full export blocked: existing standalone buildings must not be overwritten. '
                           'Export one unprotected building with --building ID, or rebuild in a separate staging repository.')
