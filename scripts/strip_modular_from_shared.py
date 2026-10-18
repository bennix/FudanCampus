"""Remove modular building nodes from a shared district GLB without rewriting the BIN chunk."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'web' / 'public'


def read_glb(path: Path):
    data = path.read_bytes()
    json_len = struct.unpack_from('<I', data, 12)[0]
    json_bytes = data[20 : 20 + json_len]
    bin_start = 20 + json_len
    bin_len = struct.unpack_from('<I', data, bin_start)[0]
    bin_bytes = data[bin_start + 8 : bin_start + 8 + bin_len]
    return json.loads(json_bytes.decode('utf-8')), bin_bytes


def write_glb(path: Path, gltf: dict, bin_bytes: bytes):
    json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    while len(json_bytes) % 4:
        json_bytes += b' '
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    out = bytearray()
    out.extend(struct.pack('<III', 0x46546C67, 2, total))
    out.extend(struct.pack('<II', len(json_bytes), 0x4E4F534A))
    out.extend(json_bytes)
    out.extend(struct.pack('<II', len(bin_bytes), 0x004E4942))
    out.extend(bin_bytes)
    path.write_bytes(out)
    return bytes(out)


def strip(shared_id: str, building_ids: set[str]):
    path = PUBLIC / f'models/shared/{shared_id}.glb'
    gltf, bin_bytes = read_glb(path)
    drop = set()
    for i, node in enumerate(gltf.get('nodes', [])):
        extras = node.get('extras') or {}
        bid = str(extras.get('building_id', extras.get('landmark_id', '')))
        if bid in building_ids:
            drop.add(i)
    if not drop:
        print(f'No matching nodes in {shared_id}.glb')
        return
    kept = [n for i, n in enumerate(gltf['nodes']) if i not in drop]
    gltf['nodes'] = kept
    gltf['scenes'][0]['nodes'] = list(range(len(kept)))
    payload = write_glb(path, gltf, bin_bytes)
    rev = hashlib.sha256(payload).hexdigest()[:12]
    manifest_path = PUBLIC / 'campus-manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for entry in manifest['shared']:
        if entry['id'] == shared_id:
            entry['revision'] = rev
            entry['bytes'] = len(payload)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Stripped {len(drop)} nodes from shared/{shared_id}.glb -> {len(payload)} bytes, revision {rev}')


if __name__ == '__main__':
    ids = set(sys.argv[1:]) if len(sys.argv) > 1 else {'3', '5', '7'}
    strip('03', ids)
