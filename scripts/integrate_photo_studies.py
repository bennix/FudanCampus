"""Incrementally place the three photo studies in the existing campus. Blender CLI.
Original studies and protected campus resources are not overwritten.
"""
import bpy,bmesh,json,hashlib,sys,math
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[1];P=R/'web/public';O=R/'field-review/campus-photo-integration';O.mkdir(exist_ok=True)
m=json.loads((O/'manifest-before.json').read_text());lod=json.loads((P/'campus-lod.json').read_text())
lod['assets']=[a for a in lod['assets'] if not a.get('sourceId','').startswith('shared-photo-')]
reports=[]
def meta(path):
 d=path.read_bytes();import struct
 g=json.loads(d[20:20+struct.unpack_from('<I',d,12)[0]])
 return dict(url=str(path.relative_to(P)),bytes=len(d),revision=hashlib.sha256(d).hexdigest()[:12],triangles=sum(sum(g['accessors'][p['indices']]['count']//3 for p in g['meshes'][n['mesh']]['primitives']) for n in g['nodes'] if 'mesh'in n))
def export(path,objs):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 path.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.export_scene.gltf(filepath=str(path),use_selection=True,export_format='GLB',export_apply=True,export_extras=True,export_cameras=False,export_lights=False)
 return meta(path)
def vegetation(n):return any(t in n.lower() for t in ['vegetation','mondo grass','shrub','flower','lotus','lily','bamboo'])
def micro(n):return any(t in n.lower() for t in ['joint','grout','pebble','grid paving','tile','ceiling grid']) and not 'facade' in n.lower()
for key,scale,offset in [('xiyuan',(.9,.84,1),(24,31.32,.22)),('yeyaozhen',(.8,.72,1),(72.8,19.04,.22)),('teaching3',(1.1,1,1),(21.6,103.3,.22))]:
 bpy.ops.wm.open_mainfile(filepath=str(R/f'field-review/{key}-photo-v1/{key}.blend'))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 for o in list(meshes):
  if (key=='teaching3' and o.name.startswith(('courtyard base','annex exterior stairs','annex stair rail'))) or (key=='yeyaozhen' and o.name.lower() in ['forecourt base','forecourt']):
   meshes.remove(o);bpy.data.objects.remove(o,do_unlink=True);continue
  # Clip standalone hardscape at adjacent campus roads/buildings.
  if (key=='teaching3' and 'grid paving'in o.name) or (key=='yeyaozhen' and 'forecourt'in o.name):
   bm=bmesh.new();bm.from_mesh(o.data)
   limit=-25 if key=='teaching3' else (11-offset[1])/scale[1]
   bmesh.ops.delete(bm,geom=[f for f in bm.faces if (o.matrix_world@f.calc_center_median()).y<limit],context='FACES');bm.to_mesh(o.data);bm.free()
  o.matrix_world=Matrix.Translation(Vector(offset))@Matrix.Diagonal((*scale,1))@o.matrix_world
  o['photoStudy']=key;o['campusVegetation']=vegetation(o.name)
  if key=='teaching3' and o.name=='metal sphere sculpture':
   # Preserve a true sphere under the slightly wider footprint fit.
   center=o.matrix_world.translation.copy()
   o.matrix_world=Matrix.Translation(center)@Matrix.Diagonal((1/scale[0],1,1,1))@Matrix.Translation(-center)@o.matrix_world
  # Bake world geometry so no runtime transform can drift between LOD tiers.
  o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
 source=export(P/f'models/photo/{key}.glb',meshes);source.pop('triangles')
 source.update(id='photo-'+key,name={'xiyuan':'曦园 · 实景模型','yeyaozhen':'叶耀珍楼 · 实景模型','teaching3':'第三教学楼 · 实景模型'}[key],source='User field photographs; approximate map registration',editableSource=f'field-review/{key}-photo-v1/{key}.blend')
 m['shared'].append(source)
 # Keep hard structure intact. Separate high-frequency paving and vegetation.
 groups={'structure':[],'surface':[]}
 vi=0
 for o in meshes:
  if vegetation(o.name):groups[f'vegetation-{vi:02d}']=[o];vi+=1
  else:groups['surface' if micro(o.name) else 'structure'].append(o)
 for part,objs in groups.items():
  if not objs:continue
  # Group geometry can exceed mobile near budget; preserve structure regardless.
  tiers=[]
  for level,ratio in [('far',.025),('medium',.22),('near',1)]:
   for o in objs:
    o.modifiers.clear()
    if level!='near' and part!='structure' and len(o.data.polygons)>30:
     mod=o.modifiers.new('Photographic detail LOD','DECIMATE');mod.ratio=ratio
   tiers.append(export(P/f'models/photo/{key}-{part}-{level}.glb',objs))
  for o in objs:o.modifiers.clear()
  corners=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box]
  lo=[min(v[i] for v in corners) for i in range(3)];hi=[max(v[i] for v in corners) for i in range(3)]
  aid=('landscape-tree-' if part.startswith('vegetation') and tiers[2]['triangles']>tiers[0]['triangles'] else 'photo-')+key+'-'+part
  lod['assets']=[a for a in lod['assets'] if a['id']!=aid]
  lod['assets'].append(dict(id=aid,sourceId='shared-photo-'+key,name=source['name']+' '+part,sourceRevision=source['revision'],position=[0,0,0],rotation=[0,0,0],bounds=dict(min=[lo[0],lo[2],-hi[1]],max=[hi[0],hi[2],-lo[1]]),nearDistance=55,mediumDistance=160,tiers=tiers))
 reports.append(dict(key=key,scale=scale,translation_blender=offset,source=source,meshCount=len(meshes)))
# Preserve cleanup revisions applied independently to existing resources.
current=json.loads((P/'campus-manifest.json').read_text())
current['shared']=[a for a in current['shared'] if not a['id'].startswith('photo-')]+[a for a in m['shared'] if a['id'].startswith('photo-')]
(P/'campus-manifest.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n')
(P/'campus-lod.json').write_text(json.dumps(lod,ensure_ascii=False,indent=2)+'\n')
(O/'placement.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
print('PHOTO_INTEGRATION_EXPORTED',flush=True)
