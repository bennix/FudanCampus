"""Read-only audit of the saved final checkpoint; does not save the scene."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

previous = json.loads((O / 'final-validation.json').read_text(encoding='utf-8'))
assert sha(BASE) == previous['source_sha256']
checksums = []
for checkpoint in previous['checkpoints']:
    actual = sha(O / checkpoint['file'])
    assert actual == checkpoint['sha256'], checkpoint['file']
    checksums.append(dict(file=checkpoint['file'], matches_reopen_validation=True, sha256=actual))

bpy.ops.wm.open_mainfile(filepath=str(O / 'forecourt-refined-v4.blend'))
solid_names = set()
for stage in ['stage01', 'stage02', 'stage03']:
    data = json.loads((O / (stage + '-validation.json')).read_text(encoding='utf-8'))
    solid_names.update(item['name'] for item in data['solids'])
solid_names.add('EPATH continuous union surface')
solids = [solid_check(bpy.data.objects[name]) for name in sorted(solid_names)]

path = bpy.data.objects['EPATH continuous union surface']
assert len(path.data.materials) == 1
material = path.data.materials[0]
assert material.name.startswith('V4 clean irregular garden stone'), material.name
textures = [node.image for node in material.node_tree.nodes if node.type == 'TEX_IMAGE' and node.image]
assert len(textures) == 1 and textures[0].packed_file
pixels = np.empty(textures[0].size[0] * textures[0].size[1] * 4, np.float32)
textures[0].pixels.foreach_get(pixels)
rgb = pixels.reshape(-1, 4)[:, :3]
assert np.isfinite(rgb).all()
black_pixels = int((rgb.max(axis=1) < .05).sum())
assert black_pixels == 0
plaza = bpy.data.objects['FORECOURT photo grid plaza'].data.materials[0]
assert plaza.name.startswith('V4 calibrated plaza granite')
assert all(node.image.packed_file for node in plaza.node_tree.nodes if node.type == 'TEX_IMAGE' and node.image)

report = dict(
    final_checkpoint='forecourt-refined-v4.blend',
    read_only_audit=True,
    source_unchanged=True,
    checkpoints=checksums,
    previously_audited_solids_checked_in_final=len(solids),
    all_checked_solids_closed_positive_volume_no_zero_area=True,
    curve_material=material.name,
    curve_texture_packed=True,
    curve_texture_size=list(textures[0].size),
    curve_texture_black_pixels_below_005=black_pixels,
    plaza_material=plaza.name,
    plaza_texture_packed=True,
    dimensions_and_cameras='推定，未实测或求解相机',
    solids=solids,
    limits=previous['limits'],
)
(O / 'delivery-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('DELIVERY_AUDIT_PASSED', len(solids), flush=True)
