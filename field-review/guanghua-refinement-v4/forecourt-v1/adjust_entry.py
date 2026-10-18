import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
R=Path.cwd(); O=Path(__file__).resolve().parent
BASE=O.parent/'vegetation-v2/vegetation-v2.blend'
h=hashlib.sha256(BASE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(BASE)); s=bpy.context.scene
width=json.loads((R/'field-review/guanghua-lawn-shape-v2/outline.json').read_text())['width_m']
axis=width-25+2; dx=axis-72.5
# The four urns share meshes; change only vertices in the two eastern urns.
changes=[]; untouched=[]
for o in s.objects:
 if o.type!='MESH':continue
 ids=[]
 if o.get('feature_id')=='FURNITURE':
  for v in o.data.vertices:
   p=o.matrix_world@v.co
   if 67.8<p.x<77.2 and 87.8<p.y<90.2: ids.append(v.index)
 if o.get('feature_id')=='VEGETATION_V2':
  selected=set()
  for p in o.data.polygons:
   co=o.matrix_world@p.center
   if 67.8<co.x<77.2 and 87.8<co.y<90.2 and 1.5<co.z<2.6:selected.update(p.vertices)
  ids=sorted(selected)
 if ids:
  before=[tuple(v.co) for v in o.data.vertices]
  shift=o.matrix_world.inverted().to_3x3()@Vector((dx,0,0))
  changes.append((o.name,ids,before,shift))
assert len(changes)>=6,[(n,len(ids)) for n,ids,_,_ in changes]
def camera(name,loc,target,scale):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o)
 o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;return o
cam=camera('FORECOURT east entrance',(axis+13,109,25),(axis,86,0),27)
s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True
s.render.resolution_x=1000;s.render.resolution_y=800;s.render.resolution_percentage=100
s.render.threads_mode='FIXED';s.render.threads=12
def render(name):
 s.camera=cam;s.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True)
render('before-entry')
for name,ids,before,shift in changes:
 o=bpy.data.objects[name]
 for i in ids:o.data.vertices[i].co+=shift
 o.data.update();o['east_urn_revision']='Pair straddles east lawn walk entrance; user correction 2026-09-29; dimensions inferred'
 selected=set(ids)
 for v,old in zip(o.data.vertices,before):
  if v.index not in selected:assert tuple(v.co)==old
render('after-entry')
checkpoint=O/'forecourt-entry-v1.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(checkpoint))
bpy.ops.wm.open_mainfile(filepath=str(checkpoint))
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==h
assert 69+dx+1.075<axis-1.8 and 76+dx-1.075>axis+1.8
(O/'validation.json').write_text(json.dumps(dict(baseline_unchanged=True,checkpoint_reopened=True,west_urn_vertices_unchanged=True,changed_meshes=[n for n,_,_,_ in changes],translation_x=dx,walk_axis=axis,centres=[[69+dx,89],[76+dx,89]],clear_width=7-2.15,walk_width=3.6,scope='Only two east urns translated; no material or sculpture changes; no production export'),indent=2))
print('ENTRY_CORRECTION_COMPLETE',dx,flush=True)
