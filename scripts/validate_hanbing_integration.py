"""Check lossless detail integration, untouched neighbors, and overwrite guards."""
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from asset_protection import ROOT, assert_export_allowed, verify_protected_sources


def read_glb(relative):
    data = (ROOT / relative).read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    return json.loads(data[20:20 + length]), data[20 + length:]


config = verify_protected_sources()
source = config['buildings']['42']
original, original_binary = read_glb(source['source'])
detail, detail_binary = read_glb('web/public/models/buildings/42.glb')
assert detail_binary == original_binary, 'Mesh, material-image or buffer data changed'
wrapper = detail['nodes'].pop()
assert wrapper['translation'] == [-v for v in source['position']]
assert wrapper['children'] == original['scenes'][0]['nodes']
assert detail['scenes'][0]['nodes'] == [len(original['nodes'])]
detail['scenes'][0]['nodes'] = wrapper['children']
assert detail == original, 'Original nodes, transforms, materials or evidence changed'

subprocess.run(['node', str(ROOT / 'web/validate-hanbing-context.mjs')], check=True)

# The real full-rebuild entry point must fail before even importing Blender.
result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_campus.py')], capture_output=True, text=True)
assert result.returncode != 0 and 'Full export blocked' in result.stderr, result.stderr
for bid in (None, '42'):
    try:
        assert_export_allowed(bid)
    except RuntimeError:
        pass
    else:
        raise AssertionError(f'Overwrite guard allowed {bid}')
assert_export_allowed('16')
# A changed accepted file must also block exports of other buildings.
with tempfile.TemporaryDirectory() as directory:
    sandbox = Path(directory)
    (sandbox / 'assets').mkdir()
    (sandbox / 'assets/protected-buildings.json').write_text(json.dumps({
        'files': {'missing-accepted.glb': 'invalid'}, 'buildings': {}}), encoding='utf-8')
    try:
        assert_export_allowed('16', sandbox)
    except RuntimeError as error:
        assert 'Protected baseline changed' in str(error)
    else:
        raise AssertionError('Missing protected source was accepted')
verify_protected_sources()
print('PASS: 11 accepted files unchanged; detailed geometry/images/evidence unchanged; '
      'old 42 and batched remnants removed; full rebuild and protected single-building exports blocked')
