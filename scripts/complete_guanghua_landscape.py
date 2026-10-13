"""Evidence-linked completion; preserves every earlier checkpoint and campus asset."""
import bpy, bmesh, ast, math, json, random, hashlib, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'field-review/guanghua-complete-v3'; OUT.mkdir(exist_ok=True)
BASE=ROOT/'field-review/guanghua-lawn-survey-v1/model/guanghua-lawn-v1.blend'
WEST=ROOT/'field-review/west-garden-terrace-v3/west-garden-terrace-v3.blend'
EAST=ROOT/'field-review/east-garden-v2/east-garden-v2.blend'
LAWN=ROOT/'field-review/guanghua-lawn-shape-v2/guanghua-lawn-shape-v2.blend'
protected=[BASE,WEST,EAST,LAWN]+[ROOT/p for p in json.loads((ROOT/'assets/protected-buildings.json').read_text())['files'] if (ROOT/p).exists()]
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
random.seed(92826)
bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene
for c in bpy.data.collections:c.hide_render=False
for o in bpy.data.objects:o.hide_render=False
M={m.name:m for m in bpy.data.materials};B={};ROOTS={};META={};current=('GROUND','02')
COL={n:bpy.data.collections.new('COMPLETE_'+n) for n in ['01','02','03','04']}
for c in COL.values():s.collection.children.link(c)
D=json.loads((ROOT/'field-review/guanghua-lawn-survey-v1/survey.json').read_text(encoding='utf-8'));FEATURES={f['id']:f for f in D['features']}
tree=ast.parse((ROOT/'scripts/build_guanghua_lawn.py').read_text(encoding='utf-8'))
names={'add','box','prism','beam','cyl','blob','curve','edges','ribbon','rail','bench','flush','mat','begin'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<geometry helpers>','exec'))
def delete_ids(ids):
 for o in list(bpy.data.objects):
  if o.get('feature_id') in ids:bpy.data.objects.remove(o,do_unlink=True)
def append_group(path,ids,shift=0):
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=src.objects
 keep=[o for o in dst.objects if o and o.get('feature_id') in ids]
 for o in keep:
  s.collection.objects.link(o);o.hide_render=False
  if o.parent not in keep:o.parent=None;o.location.x+=shift
  o['assembly_status']='Photo-based proportion assembly; site placement inferred'
 for o in dst.objects:
  if o and o not in keep:bpy.data.objects.remove(o,do_unlink=True)
 return keep
def camera(name,loc,target,scale=None,lens=42):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens
 if scale:d.type='ORTHO';d.ortho_scale=scale
 if scale:o.location+=o.rotation_euler.to_quaternion()@Vector((0,0,100));o['safe_ortho_standoff']=True
 return o
views={
 'overall':camera('FINAL overall',(218,-232,216),(9,70,39),320),
 'landscape':camera('FINAL landscape',(142,-133,178),(9,54,0),219),
 'plan':camera('FINAL plan',(10,56,240),(10,56,0),208),
 'west-garages':camera('FINAL west garages',(-112,24,18),(-74,59,.4),58),
 'south-garage':camera('FINAL south garage',(-91,41,7),(-76,48,.8),12),
 'north-garage':camera('FINAL north garage',(-88,63,6),(-76,70,.8),12),
 'stairs-west':camera('FINAL west stair',(-23,72,8),(-32,81,-.15),13),
 'stairs-east':camera('FINAL east stair',(80,42,7),(71.3,49.5,-.1),15),
 'stairs-west-south':camera('FINAL west south stair',(-23,39,8),(-32,48,-.1),15),
 'stairs-east-north':camera('FINAL east north stair',(81,69,8),(72.3,78,-.1),15),
 'pergola':camera('FINAL pergola',(112,7,12),(91,28,1),35),
 'ding':camera('FINAL ding',(-29,20,4.5),(-35,27,1.3),7),
 'fudan':camera('FINAL fudan',(35,-2,4.1),(26,10,1.0),13),
 'flower':camera('FINAL flower',(43,-1,4.5),(38,7,1.2),7),
}
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.render.threads_mode='FIXED';s.render.threads=12
def render(name,prefix='after',res=960):
 for o in bpy.data.objects:
  if o.get('feature_id')=='CONTEXT_GUANGHUA':o.hide_render=name!='overall'
 s.camera=views[name];s.render.resolution_x=res;s.render.resolution_y=round(res*(.70 if name in ['overall','landscape'] else .78));s.render.filepath=str(OUT/f'{prefix}-{name}.png');bpy.ops.render.render(write_still=True)
if '--before' in sys.argv:
 for name in ['landscape','south-garage','stairs-west','ding','fudan','flower']:render(name,'before',760)
 sys.exit()
outline=json.loads((ROOT/'field-review/guanghua-lawn-shape-v2/outline.json').read_text())
east_shift=outline['width_m']-95
east_ids={'ETERR','ERAMP','EPATH','ESKY','EOPEN','EOPEN_S','E_FURNITURE','E_TREES','E_PLANTING'}
delete_ids(east_ids|{'WTERR','LAWN','GROUND','PLAZA','EDGE_PATHS','BOUNDARY','WB1','WB2','WOPEN','WOPEN_S','DING','SIGN','FLOWER','VEGETATION'})
append_group(WEST,{'WTERR'});append_group(EAST,east_ids,east_shift)
# Keep exact accepted lawn vertices and scale; translate its local southwest corner only.
lawn_objects=append_group(LAWN,{'LAWN'})
for o in lawn_objects:
 if not o.parent:o.location+=Vector((-25,16,.055))
 o['assembly_transform']='Translation only (-25,16,0.055); fixed outline unchanged'
M.update({m.name:m for m in bpy.data.materials})
# Independent materials: physically textured render surfaces, never edit source materials.
def surface(name,color,rough=.8,metal=0,scale=6,bump=.04):
 m=mat(name,color,rough,metal);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[0].color=tuple(v*.65 for v in color)+(1,);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=tuple(min(1,v*1.18) for v in color)+(1,)
 coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Object'],tex.inputs['Vector']);l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
 bn=n.new('ShaderNodeBump');bn.inputs['Strength'].default_value=.25;bn.inputs['Distance'].default_value=bump;l.new(tex.outputs['Fac'],bn.inputs['Height']);l.new(bn.outputs['Normal'],p.inputs['Normal']);return m
surface('FIN_concrete',(.51,.49,.42),scale=4,bump=.035)
surface('FIN_granite',(.48,.49,.46),scale=29,bump=.015)
surface('FIN_stone_pale',(.64,.63,.56),scale=32,bump=.013)
surface('FIN_ramp',(.30,.31,.28),scale=12,bump=.045)
surface('FIN_bronze',(.12,.21,.16),.55,.7,6,.025)
surface('FIN_bark',(.19,.145,.10),scale=8,bump=.06)
surface('FIN_grass',(.23,.34,.09),scale=3,bump=.05)
surface('FIN_garden_grass',(.23,.28,.115),scale=4,bump=.05)
surface('FIN_hedge',(.105,.20,.035),scale=13,bump=.08)
surface('FIN_redhedge',(.25,.105,.08),scale=12,bump=.04)
mat('FIN_blue',(.015,.035,.21),.4,.25);mat('FIN_red',(.70,.09,.025),.35,.15)
mat('FIN_sign_gold',(.83,.68,.22),.47,.12);mat('FIN_door',(.50,.53,.51),.63,.25)
mat('FIN_green_metal',(.055,.11,.075),.49,.55)
mat('FIN_flower',(.40,.014,.029),.78)
mat('FIN_black',(.014,.021,.018));mat('FIN_stainless',(.42,.47,.45),.25,.85)
for i,col in enumerate([(.10,.21,.025),(.17,.27,.045),(.25,.32,.075),(.12,.24,.06),(.29,.30,.10)]):surface('FIN_leaf'+str(i),col,scale=18,bump=.04)
# Grey staggered rectangular paving with metre-based UVs.
m=surface('FIN_pavers',(.45,.46,.43),scale=25,bump=.012);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
tx=n.new('ShaderNodeTexBrick');tx.inputs['Color1'].default_value=(.40,.42,.40,1);tx.inputs['Color2'].default_value=(.54,.54,.49,1);tx.inputs['Mortar'].default_value=(.26,.28,.25,1);tx.inputs['Scale'].default_value=1;tx.inputs['Mortar Size'].default_value=.006;tx.inputs['Brick Width'].default_value=.6;tx.inputs['Row Height'].default_value=.3
uv=n.new('ShaderNodeTexCoord');l.new(uv.outputs['UV'],tx.inputs['Vector']);l.new(tx.outputs['Color'],p.inputs['Base Color'])
def text_obj(fid,body,loc,size,matname,rotation=(math.pi/2,0,0),fontpath=None,depth=.018):
 flush();f=bpy.data.curves.new(fid+' text','FONT');f.body=body;f.size=size;f.extrude=depth;f.bevel_depth=.006;f.align_x='CENTER';f.align_y='CENTER'
 if fontpath:f.font=bpy.data.fonts.load(fontpath)
 o=bpy.data.objects.new(fid+'__text__'+body,f);COL['03'].objects.link(o);o.location=loc;o.rotation_euler=rotation;f.materials.append(M[matname]);o.parent=ROOTS[fid]
 for k,v in META[fid].items():o[k]=v
 return o
def leafy_line(points,width=.7,z=0,height=.75,red=False):
 ribbon(points,width,z,z+height*.84,'FIN_redhedge' if red else 'FIN_hedge','hedge-core')
 for a,b in zip(points,points[1:]):
  a,b=Vector(a),Vector(b);num=max(1,round((b-a).length/.33))
  for j in range(num+1):
   q=a+(b-a)*j/num
   blob(q.x+random.uniform(-.1,.1),q.y+random.uniform(-.1,.1),z+height*.78,width*.55,width*.54,height*.27,'FIN_redhedge' if red else 'FIN_hedge','hedge-leaf-clusters',8,5)
def cut(obj,poly,label,zbottom=-4.3):
 begin('CUT','02',refs=[]);prism(poly,zbottom,4.6,'dark',label);flush();cutter=next(o for o in bpy.data.objects if o.name.startswith('CUT__'+label+'__'))
 bpy.context.view_layer.objects.active=obj;mod=obj.modifiers.new('Opening '+label,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name)
 delete_ids({'CUT'});ROOTS.pop('CUT',None);META.pop('CUT',None)
begin('GROUND','01',refs=[4474],note='New assembly support slab; holes represent visible entries only.')
box(14.5+east_shift/2,57.5,-2.005,209+east_shift,133,4,'FIN_garden_grass','terrain');flush();ground=next(o for o in bpy.data.objects if o.name.startswith('GROUND__terrain'))
begin('BOUNDARY','01',refs=[4312,4400,4523])
for x in [-85,114+east_shift]:box(x,59.5,-.15,10,129,.3,'road','road')
box(14.5+east_shift/2,-4,-.145,189+east_shift,10,.29,'road','south-road')
for x in [-78.5,107.5+east_shift]:box(x,56,.025,3,111,.05,'FIN_pavers','sidewalk')
box(14.5+east_shift/2,3,.025,183+east_shift,3,.05,'FIN_pavers','south-sidewalk')
# Main edge walks and concave forecourt follow the frozen grass boundary.
poly=[(x-25,y+16) for x,y in outline['polygon_xy']];north=list(reversed(poly[2:]));rightx=outline['width_m']-25
begin('EDGE_PATHS','01',refs=[4320,4492,4600]);ribbon(poly+[poly[0]],.18,.04,.17,'FIN_stone_pale','grass-curb')
for x in [-27,rightx+2]:ribbon([(x,14),(x,87)],3.6,-.02,.045,'FIN_pavers','edge-walk')
ribbon([(-28,13.8),(rightx+4,13.8)],3.8,-.02,.05,'FIN_pavers','south-walk')
begin('PLAZA','01',refs=[4474]);plazapoly=[(-80,87),(-28.8,87),(-28.8,north[0][1])]+north+[(rightx+3.8,north[-1][1]),(rightx+3.8,87),(109+east_shift,87),(109+east_shift,113),(-80,113)]
prism(plazapoly,-.035,.035,'FIN_pavers','concave-forecourt')
flush()
# Garage doors: open south facade, separate four-leaf north facade, visible apron only.
holes=[]
for fid,cy,closed in [('WB1',48,False),('WB2',70,True)]:
 begin(fid,'02',note='Photo facade confirmed; metric size and short apron slope inferred. Hidden garage omitted.')
 holes.append((fid,[(-80.1,cy-3.05),(-74.2,cy-3.05),(-74.2,cy+3.05),(-80.1,cy+3.05)]))
 v=[(-80.1,cy-3,.055),(-71.6,cy-3,-.93),(-71.6,cy+3,-.93),(-80.1,cy+3,.055)]
 add([(x,y,z-.17) for x,y,z in v]+v,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'FIN_ramp','sloping-apron')
 for yy in [cy-3.2,cy+3.2]:
  box(-75.7,yy,-.04,8.8,.34,1.95,'FIN_concrete','retaining-wall');box(-75.7,yy,.97,8.85,.41,.10,'FIN_stone_pale','coping')
  beam((-79.6,yy,.58),(-72.2,yy,.58),.085,'FIN_stainless','side-pipe')
  leafy_line([(-76.8,yy+(.6 if yy>cy else -.6)),(-71.8,yy+(.6 if yy>cy else -.6))],1.0,.02,1.25)
 for yy in [cy-3.15,cy+3.15]:box(-71.7,yy,.44,.64,.45,2.75,'FIN_concrete','door-jamb')
 box(-71.7,cy,1.80,.65,6.75,.52,'FIN_concrete','door-lintel');box(-72.065,cy,2.08,.14,6.05,.82,'FIN_blue','sign-board')
 for yy in [cy-2.98,cy+2.98]:box(-72.1,yy,.32,.10,.08,2.48,'FIN_door','door-frame')
 box(-72.1,cy,1.53,.10,5.96,.10,'FIN_door','door-frame')
 if closed:
  for j in range(4):
   yy=cy-2.205+j*1.47;box(-72.08,yy,.30,.09,1.435,2.35,'FIN_door','closed-door-leaf')
   box(-72.15,yy-.67,.30,.045,.027,2.30,'FIN_black','door-seam')
  for yy in [cy-.14,cy+.14]:box(-72.19,yy,.20,.07,.035,.23,'FIN_stainless','door-handle')
 else:
  box(-71.53,cy,.22,.065,5.85,2.30,'FIN_black','visibility-limit')
  for yy in [cy-2.9,cy+2.9]:box(-72.75,yy,.30,1.40,.085,2.32,'FIN_door','folded-open-leaf')
  for yy in [cy-2.20,cy+2.20]:box(-72.9,yy,1.25,1.70,.07,.07,'FIN_door','opening-top-return')
 for j in range(32):box(-79.55,cy-2.88+j*.18,-.005,.28,.055,.04,'FIN_stainless','mouth-grate')
 leafy_line([(-71.45,cy-3.3),(-71.45,cy+3.3)],1.2,2.12,.43,True)
 text_obj(fid,'光华楼广场自行车库',(-72.15,cy,2.07),.48,'FIN_sign_gold',(math.pi/2,0,-math.pi/2),'C:/Windows/Fonts/simhei.ttf')
flush()
# Fit each mouth outside the west terrace wall x=-74, preserving road contact x=-80.1.
# Only garage depth is compressed; facade lettering retains height/width.
def garage_x(x):return -80.1+(x+80.1)*(5.9/8.6)
for o in bpy.data.objects:
 if o.get('feature_id') in {'WB1','WB2'}:
  o['registration_note']='Facade placed outside west terrace wall; apron length ~5.9 m inferred to avoid overlap.'
  if o.type=='MESH':
   for v in o.data.vertices:v.co.x=garage_x(v.co.x)
  elif o.type=='FONT':o.location.x=garage_x(o.location.x)
# Rebuild all four independent openings: high-side entry is left unobstructed.
delete_ids({'EOPEN','EOPEN_S'})
for fid,x,y,refs in [('WOPEN',-32,81,[4452,4453]),('WOPEN_S',-32,48,[4354,4357]),('EOPEN',79+east_shift,78,[4492,4493]),('EOPEN_S',78+east_shift,49.5,[4505,4574])]:
 begin(fid,'02',refs=refs,note='Four independent visible openings. Rail form confirmed; entry compass direction, depth and tread count inferred.')
 holes.append((fid,[(x-1.60,y-2.1),(x+1.6,y-2.1),(x+1.6,y+2.1),(x-1.6,y+2.1)]))
 for xx in [x-1.75,x+1.75]:box(xx,y,-.66,.3,4.5,1.65,'FIN_concrete','side-wall');box(xx,y,.20,.40,4.55,.09,'FIN_stone_pale','coping')
 box(x,y-2.25,-.66,3.2,.3,1.65,'FIN_concrete','end-wall')
 for i in range(12):
  yy=y+2.1-(i+.5)*.35;top=.055-i*.14
  box(x,yy,(-1.77+top)/2,2.95,.35,top+1.77,'FIN_concrete','descending-steps')
  box(x,yy,top+.014,2.95,.35,.028,'FIN_granite','tread')
  box(x,yy+.15,top+.032,2.90,.035,.010,'FIN_stone_pale','step-edge')
 rail([(x-1.82,y+2.1),(x-1.82,y-2.4),(x+1.82,y-2.4),(x+1.82,y+2.1)],.24,1.03,'FIN_green_metal')
 for side in [-1,1]:
  beam((x+side*1.82,y-2.3,.94),(x+side*1.82,y+2.1,.94),.055,'FIN_green_metal','middle-rail')
  beam((x+side*1.29,y+1.95,.93),(x+side*1.29,y-1.95,-.61),.046,'FIN_stainless','sloping-handrail')
  for j in range(3):
   yy=y+1.7-j*1.65;z=.055-(2.1-(yy-y))*.4
   beam((x+side*1.29,yy,z),(x+side*1.29,yy,z+.87),.038,'FIN_stainless','handrail-post')
 leafy_line([(x-2.45,y+1.6),(x-2.45,y-3),(x+2.45,y-3),(x+2.45,y+1.6)],.75,.01,.72)
 for j in range(4):box(x,y+2.5+j*.53,.055,1.65,.38,.11,'FIN_granite','entry-stepping-stones')
 box(x,y-2.08,-1.54,3.1,.06,.36,'FIN_black','lower-visibility-limit')
# East curved ramp uses the accepted v2 geometry, adding photographic safety trim and fuller vine canopy.
begin('ERAMP','02',refs=[4539,4540,4550],note='Accepted east v2 deck and pergola retained; safety boards, drain and vine canopy added.')
route=curve([(109+east_shift,19),(102+east_shift,21),(97+east_shift,25),(94+east_shift,31),(94+east_shift,39)],8);left,right=edges(route,6.7)
holes.append(('ERAMP',left+list(reversed(right))))
for side in [left,right]:
 for i in range(3,len(side)-2,2):
  a,b=side[i],side[i+1];beam((*a,.30),(*b,.30),.12,'FIN_black','safety-strip',.18)
  q=Vector(a).lerp(Vector(b),.45);beam((q.x,q.y,.25),(q.x,q.y,.37),.07,'yellow','safety-marker')
 for i in range(3,len(side)-2):
  x,y=side[i]
  for j in range(3):blob(x+random.uniform(-.6,.6),y+random.uniform(-.55,.55),3.55+random.uniform(-.1,.25),.42,.45,.25,'FIN_leaf'+str(j%3),'extra-vines',8,5)
flush()
for fid,p in holes:cut(ground,p,fid)
# Cut the sidewalk where the two western aprons cross it.
walks=[o for o in bpy.data.objects if o.name.startswith('BOUNDARY__sidewalk')]
for walk in walks:
 for fid,p in holes[:2]:cut(walk,p,'walk-'+fid)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'stage01-entrances.blend'))
# DING: square open vessel, four legs, twin rectangular ears, tiered plinth.
begin('DING','03',refs=[4348,4349],note='Silhouette and tier relationships photo-confirmed. Relief represented by restrained bands; inscriptions not reconstructed.')
x,y=-35,27
for z,w,d,h,m in [(.12,4.7,4.3,.24,'FIN_granite'),(.37,3.85,3.6,.26,'FIN_stone_pale'),(.57,3.5,3.25,.14,'FIN_stone_pale'),(.75,1.87,1.62,.22,'FIN_bronze')]:box(x,y,z,w,d,h,m,'plinth')
for xx in [-.58,.58]:
 for yy in [-.45,.45]:
  beam((x+xx*1.08,y+yy*1.08,.86),(x+xx,y+yy,1.48),.23,'FIN_bronze','four-legs',.26)
  box(x+xx*1.08,y+yy*1.08,.9,.32,.30,.12,'FIN_bronze','feet')
box(x,y,1.48,1.42,1.17,.15,'FIN_bronze','vessel-bottom')
for sy in [-1,1]:
 prism([(x-.72,y+sy*.61),(x+.72,y+sy*.61),(x+.79,y+sy*.73),(x-.79,y+sy*.73)],1.5,2.22,'FIN_bronze','vessel-wall')
for sx in [-1,1]:box(x+sx*.75,y,1.86,.14,1.42,.72,'FIN_bronze','vessel-wall')
for z in [1.56,2.10,2.25]:
 for sy in [-1,1]:box(x,y+sy*.75,z,1.72,.09,.09,'FIN_bronze','rim-band')
 for sx in [-1,1]:box(x+sx*.82,y,z,.09,1.58,.09,'FIN_bronze','rim-band')
for sx in [-1,1]:
 for yy in [-.25,.25]:box(x+sx*.55,y+yy,2.50,.15,.15,.51,'FIN_bronze','twin-ears')
 box(x+sx*.55,y,2.75,.15,.65,.14,'FIN_bronze','twin-ears')
for sy in [-1,1]:
 for j in range(9):
  xx=x-.64+j*.16;box(xx,y+sy*.806,1.91,.095,.018,.11,'FIN_bronze','restrained-relief')
 for j in range(8):box(x-.68+j*.195,y+sy*.828,.75,.13,.018,.055,'FIN_black','base-recesses')
# FUDAN: deep blue letters and long base, orange-red thick heart above slatted seat.
begin('SIGN','03',refs=[4603,4604,4606],note='Blue extruded letters, heart and chair confirmed; font and proportions approximate.')
box(26,10,.18,9.2,1.5,.36,'FIN_blue','plinth')
word=text_obj('SIGN','FUDAN',(24.55,9.46,1.13),1.80,'FIN_blue',fontpath='C:/Windows/Fonts/arialbd.ttf',depth=.17)
bpy.context.view_layer.update();word.scale.x=6.2/word.dimensions.x
bpy.context.view_layer.update();word.location.z+=.375-min((word.matrix_world@Vector(v)).z for v in word.bound_box)
begin('SIGN','03');heart=[]
for i in range(129):
 t=2*math.pi*i/128;heart.append((29.25+16*math.sin(t)**3*.085,10.26,1.88+(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))*.085))
outer=[Vector(p) for p in heart[:-1]];inner=[Vector((29.25+(p.x-29.25)*.79,p.y,1.88+(p.z-1.88)*.79)) for p in outer];num=len(outer)
vv=[tuple(p+Vector((0,dy,0))) for dy in [-.17,.17] for ring in [outer,inner] for p in ring];ff=[]
for i in range(num):
 j=(i+1)%num
 ff.extend([(i,j,j+num,i+num),(i+2*num,i+3*num,j+3*num,j+2*num),(i,i+2*num,j+2*num,j),(i+num,j+num,j+3*num,i+3*num)])
add(vv,ff,'FIN_red','continuous-heart')
for xx in [28.75,29.75]:
 beam((xx,9.8,.37),(xx,9.8,.88),.07,'FIN_blue','seat-legs');beam((xx,10.26,.37),(xx,10.26,1.7),.065,'FIN_blue','seat-back')
for yy in [9.65,9.8,9.95,10.1]:box(29.25,yy,.91,1.38,.11,.055,'FIN_blue','seat-slats')
for zz in [1.14,1.34,1.54,1.73]:box(29.25,10.26,zz,1.38,.07,.10,'FIN_blue','back-slats')
# Inclined two-ring planter. Plane is tilted back; dark planted disk with visible wire grid.
begin('FLOWER','03',refs=[4609,4611],note='Two inclined nested rings and planted backing confirmed; leaf/flower arrangement illustrative.')
c=Vector((38,7,1.28));u=Vector((1,0,0));v=Vector((0,.55,.835));normal=u.cross(v)
for radius in [1.50,1.04]:
 pts=[c+u*(radius*math.cos(i*math.tau/96))+v*(radius*math.sin(i*math.tau/96)) for i in range(97)]
 for a,b in zip(pts,pts[1:]):beam(a,b,.065,'FIN_stone_pale','inclined-double-ring',.08)
for j in range(-6,7):
 q=j*.20;half=math.sqrt(1.43**2-q*q)
 beam(c+u*q-v*half-normal*.03,c+u*q+v*half-normal*.03,.016,'FIN_green_metal','planter-grid')
 beam(c+v*q-u*half-normal*.03,c+v*q+u*half-normal*.03,.016,'FIN_green_metal','planter-grid')
ring=[c+u*(1.42*math.cos(i*math.tau/64))+v*(1.42*math.sin(i*math.tau/64))-normal*.14 for i in range(64)]
vv=[tuple(p+normal*z) for z in [-.035,.035] for p in ring];add(vv,[tuple(range(63,-1,-1)),tuple(range(64,128))]+[(i,(i+1)%64,(i+1)%64+64,i+64) for i in range(64)],'FIN_hedge','planted-backing')
for j in range(370):
 r=1.39*math.sqrt(random.random());a=random.random()*math.tau;p=c+u*(r*math.cos(a))+v*(r*math.sin(a))-normal*.10
 blob(*p,.105,.075,.105,'FIN_leaf'+str(j%4),'planted-disk',7,4)
for dx in [-.8,.8]:beam((38+dx,7,.04),c+u*dx-v*.4-normal*.15,.055,'FIN_green_metal','ring-support')
for i in range(140):
 t=random.random()*math.tau;r=random.uniform(1.65,2.35);xx=38+r*math.cos(t);yy=7+r*.68*math.sin(t)
 cyl(xx,yy,.02,.018,random.uniform(.15,.28),'FIN_hedge',steps=5,part='flower-stems')
 for z in [.16,.23,.29]:blob(xx,yy,z,.068,.065,.060,'FIN_flower','flower-bed',7,4)
begin('SIGN','03');box(26,8.6,.018,10.5,6.5,.036,'FIN_pavers','visitor-apron')
# Unify retained surfaces, preserving the two refined terrace palettes.
flush()
for o in bpy.data.objects:
 if o.type!='MESH' or o.get('feature_id') in {'CONTEXT_GUANGHUA','WTERR','ETERR'}:continue
 for i,m in enumerate(o.data.materials):
  if o.get('feature_id')=='LAWN':o.data.materials[i]=M['FIN_grass']
  elif m.name in ['turf','soil']:o.data.materials[i]=M['FIN_garden_grass']
  elif m.name in ['paving','path-grey']:o.data.materials[i]=M['FIN_pavers']
  elif m.name=='concrete':o.data.materials[i]=M['FIN_concrete']
  elif m.name=='hedge':o.data.materials[i]=M['FIN_hedge']
  elif m.name=='redhedge':o.data.materials[i]=M['FIN_redhedge']
  elif m.name=='rail':o.data.materials[i]=M['FIN_green_metal']
 # Meter UV projection for the new brick material.
 if any(m.name=='FIN_pavers' for m in o.data.materials):
  uv=o.data.uv_layers.active or o.data.uv_layers.new(name='Paving metres')
  for p in o.data.polygons:
   axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=axis]
   for li in p.loop_indices:
    co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]],co[axes[1]])
# Avoid stale west terrace access crossing the new stair arrangement.
for o in list(bpy.data.objects):
 if o.get('feature_id')=='WPATH' and 'west-terrace-link' in o.name:bpy.data.objects.remove(o,do_unlink=True)
 elif o.get('feature_id')=='FURNITURE' and 'tree-ring-seat' in o.name:bpy.data.objects.remove(o,do_unlink=True)
begin('WPATH','01',refs=[4366,4368]);ribbon(curve([(-43,41),(-46,42),(-49.5,42.5),(-49.5,44)]),1.8,-.02,.06,'FIN_pavers','reconnected-terrace-access')
# Replace coarse sphere trees by clustered crowns, trunks and visible branching.
delete_ids({'E_TREES'})
begin('VEGETATION','04',refs=[4338,4349,4378,4474,4505,4556],note='Photo-guided canopy character; individual tree positions, sizes, counts and species remain inferred.')
trees=[(-75,10,9),(-76,27,10),(-77,38,9),(-75,81,10),(-73,91,9),(-46,8,8),(-44,17,9),(-50,34,9),(-40,52,8),(-44,64,9),(-48,78,8),(-40,89,9),(-65,77,9),(-62,38,8)]
trees += [(x,6,9) for x in [-26,-13,1,13,52,64,78,91]]
trees += [(x+east_shift,y,h) for x,y,h in [(103.2,36.8,8),(105,64,8),(98,73,7),(87,35,7),(77.5,57.5,6),(92,81,8),(87,20,8),(101,15,8),(104,92,9)]]
for k,(x,y,h) in enumerate(trees):
 cyl(x,y,-.03,.21,h*.63,'FIN_bark',.10,10,'tree-trunks')
 for j in range(7):
  a=j*2.399+k;r=random.uniform(1.3,2.3);z=h*random.uniform(.63,.87);p=(x+math.cos(a)*r,y+math.sin(a)*r,z)
  beam((x,y,h*.43),p,.12 if j<4 else .075,'FIN_bark','tree-branches')
  for q in range(4):
   aa=a+q*1.8;xx=p[0]+math.cos(aa)*.7;yy=p[1]+math.sin(aa)*.7;zz=z+random.uniform(-.2,.8)
   blob(xx,yy,zz,random.uniform(.8,1.3),random.uniform(.8,1.3),random.uniform(.8,1.45),'FIN_leaf'+str((j+k+q)%5),'tree-canopies',9,6)
for x,y in [(-38,34),(-40,38),(-45,67),(-36,73),(-62,79),(-54,21),(-70,86)]:
 cyl(x,y,.01,.07,.7,'FIN_bark',steps=8,part='shrub-stem')
 for j in range(8):t=j*2.4;blob(x+.45*math.cos(t),y+.45*math.sin(t),1.03,.64,.65,.67,'FIN_hedge','clipped-shrubs',9,6)
leafy_line([(-72,4),(-40,4)],1.0,.02,.7,True);leafy_line([(47,4),(64,4)],.85,.02,.60,True)
flush()
# Restore both skylight/entry groups without old open-surface geometry.
for o in bpy.data.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));open_count=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(o.data);bm.free()
 if open_count and o.get('feature_id') in {'WGLASS','WGLASS2'}:
  bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Thin enclosed glass shell','SOLIDIFY');mod.thickness=.025;bpy.ops.object.modifier_apply(modifier=mod.name)
 if any(k in o.name for k in ['leaf-clusters','tree-canopies','clipped-shrubs','extra-vines','planted-disk','flower-bed']):
  for p in o.data.polygons:p.use_smooth=True
 if o.get('feature_id') in {'WB1','WB2','DING','SIGN'} and len(o.data.polygons)<3000:
  bevel=o.modifiers.new('Small edge highlights','BEVEL');bevel.width=.012;bevel.segments=2
for c in bpy.data.collections:c.hide_render=False
for o in bpy.data.objects:o.hide_render=False
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.72,.79,.85,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55
for o in bpy.data.objects:
 if o.type=='LIGHT' and o.data.type=='SUN':o.data.energy=2.1;o.data.angle=.18
s.view_settings.view_transform='AgX';s.camera=views['overall'];s.cycles.samples=40
s['scope']='Complete Guanghua south landscape review: accepted west v3 + east v2 + fixed lawn, new entrances and landmark details.'
s['scale_status']='Evidence-limited photo reconstruction; dimensions, registration, hidden stair depth and vegetation are inferred.'
s['lawn_registration']='Exact unchanged lawn XY shape, translation only. East garden translated X by '+str(east_shift)+' m to keep its relationship to east lawn walk.'
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=240;area.spaces.active.region_3d.view_location=(8,55,0)
bpy.ops.file.pack_all()
checkpoint=OUT/'guanghua-complete-v3.blend';bpy.ops.wm.save_as_mainfile(filepath=str(checkpoint))
view_names={key:value.name for key,value in views.items()}
(OUT/'component-evidence.json').write_text(json.dumps(META,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'assembly.json').write_text(json.dumps(dict(east_translation_x=east_shift,lawn_translation=[-25,16,.055],retained_sources=[str(p.relative_to(ROOT)) for p in [BASE,WEST,EAST,LAWN]],tree_positions=trees,opening_ids=[h[0] for h in holes]),ensure_ascii=False,indent=2),encoding='utf-8')
# Reopen saved native artifact, then inspect required identities and closed new solids.
bpy.ops.wm.open_mainfile(filepath=str(checkpoint));s=bpy.context.scene
required=set(FEATURES);present={o.get('feature_id') for o in bpy.data.objects};assert required<=present,required-present
checks=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.get('feature_id') not in {'WB1','WB2','WOPEN','WOPEN_S','EOPEN','EOPEN_S','DING','SIGN','FLOWER','GROUND','PLAZA','VEGETATION'}:continue
 bm=bmesh.new();bm.from_mesh(o.data);checks.append(dict(object=o.name,nonmanifold=sum(not e.is_manifold for e in bm.edges),volume=bm.calc_volume(signed=True),finite=all(math.isfinite(v) for p in o.data.vertices for v in p.co)));bm.free()
bad=[x for x in checks if x['nonmanifold'] or x['volume']<=0 or not x['finite']]
assert not bad,bad
unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());assert unchanged
report=dict(checkpoint_reopened=True,required_21_ids=sorted(required),new_closed_positive_meshes=len(checks),checks=checks,baselines_unchanged=hashes,lawn_shape_unscaled=True,limits=['photo proportions, not surveyed','four stair entry directions and basement depths inferred','no exhaustive scene intersection test','legacy building context unchanged; no campus asset replaced'])
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPLETION_BUILD_VALIDATED',len(checks),flush=True)
if '--build-only' in sys.argv:sys.exit()
views={key:bpy.data.objects[value] for key,value in view_names.items()}
for name in ['landscape','south-garage','north-garage','stairs-west','stairs-east','pergola','ding','fudan','flower']:
 s.cycles.samples=16;render(name,'diagnostic',900)
print('DIAGNOSTICS_COMPLETE',flush=True)
