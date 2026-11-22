"""Trace one supplied map crop in one coordinate frame; no legacy placeholders.

Pixel coordinates refer to the user's 320 x 275 map crop. Dimensions are
illustrative, not surveyed: 0.48 scene metres per crop pixel.
"""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'web/public/map-review';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def xy(p):return Vector(((p[0]-176)*.48,(107-p[1])*.48,0))
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.75
 return m
wall=material('一教浅灰粉刷',(.72,.77,.76));office=material('综合楼浅灰白',(.76,.79,.79));trim=material('乳白浮雕与窗套',(.89,.89,.83));glass=material('灰绿窗玻璃',(.16,.28,.29));metal=material('铝合金窗框',(.51,.59,.59));bronze=material('深铜题字',(.16,.10,.05));road=material('沥青道路',(.27,.29,.29));grass=material('地图绿地',(.48,.57,.38));context=material('邻楼简模',(.63,.69,.64));roof=material('深灰檐边',(.20,.24,.24))
officeglass=material('综合楼浅灰绿玻璃',(.32,.43,.41));lawn=material('庭院草坪',(.14,.32,.055));leaves=material('庭院灌木',(.075,.19,.05));bark=material('树干',(.19,.13,.075));stone=material('庭院褐灰假山',(.26,.20,.14));paving=material('庭院石板路',(.44,.44,.37))
feature_bid=None
def box(name,loc,size,mat,angle=0):
 w,d,h=size;c,s=math.cos(angle),math.sin(angle)
 verts=[(loc[0]+c*x-s*y,loc[1]+s*x+c*y,loc[2]+z) for x,y,z in [(-w/2,-d/2,-h/2),(-w/2,-d/2,h/2),(-w/2,d/2,-h/2),(-w/2,d/2,h/2),(w/2,-d/2,-h/2),(w/2,-d/2,h/2),(w/2,d/2,-h/2),(w/2,d/2,h/2)]]
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]);me.materials.append(mat)
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 if feature_bid:o['building_id']=feature_bid
 return o
def prism(name,points,height,mat,bid,z=0):
 ps=[xy(p) for p in points];n=len(ps)
 verts=[(p.x,p.y,h) for h in (z,z+height) for p in ps]
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(mat);o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o['building_id']=bid;o['source']='user map crop traced in pixels'
 # Recalculate normals for opposite polygon winding and concave caps.
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');o.select_set(False)
 return o
def inside(p,poly):
 hit=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
def facade(a,b,floors,bid,teaching=False,section=''):
 start,end=xy(a),xy(b);u=(end-start).normalized();normal=Vector((u.y,-u.x,0));angle=math.atan2(u.y,u.x);length=(end-start).length
 main_front=teaching and a==(127,133) and b==(234,112)
 blank_end=bid=='51' and section=='南低楼' and length<16
 count=19 if main_front else max(1,round(length/(2.8 if teaching else 3.05)));spacing=length/count;width=spacing*(.67 if teaching else .77)
 def part(name,d,z,w,h,depth,mat,offset=.07):
  p=start+u*d+normal*offset;p.z=z
  # Clip facade strips against adjacent volumes; joined walls get no windows.
  neighbours=[poly for title,poly,height in parts[bid] if title!=section and z<height+.5]
  def covered(distance):
   q=p+u*distance;pixel=(q.x/.48+176,107-q.y/.48)
   return any(inside(pixel,poly) for poly in neighbours)
  steps=max(1,math.ceil(w/.12));runs=[];run=None
  for i in range(steps):
   left=-w/2+w*i/steps;right=-w/2+w*(i+1)/steps
   if not covered((left+right)/2):
    if run is None:run=left
   elif run is not None:runs.append((run,left));run=None
  if run is not None:runs.append((run,w/2))
  if w<3 and sum(r-l for l,r in runs)<w-.02:return
  for left,right in runs:
   o=box(name,p+u*((left+right)/2),(right-left,depth,h),mat,angle);o['building_id']=bid
 for col in range(count):
  d=(col+.5)*spacing
  for level in range(floors):
   z=1.9+level*3.35
   if blank_end:continue
   if main_front and col in (7,11):
    # Recessed elongated geometric ornament, photographed beside the entrance.
    part('几何窗饰中央竖槽',d,z,.13,1.9,.055,roof,.13)
    for side in (-1,1):
     for top in (-1,1):
      part('几何窗饰折角竖',d+side*.49,z+top*.73,.13,.56,.055,roof,.13)
      part('几何窗饰折角横',d+side*.29,z+top*.96,.53,.13,.055,roof,.13)
    continue
   if main_front and level==0 and col in (8,9,10):continue
   wh=2.3 if teaching else 2.05 if section=='东连廊' else 1.48
   part('浅色窗套',d,z,width+.18,wh+.18,.16,trim)
   part('窗玻璃',d,z,width,wh,.06,glass if teaching else officeglass,.18)
   for offset in ((-width/6,width/6) if teaching else (0,)):part('窗竖梃',d+offset,z,.055,wh+.02,.06,metal,.23)
   part('窗横梃',d,z+wh*.27,width,.055,.06,metal,.23)
   if not teaching:
    for stripe in range(5):part('窗内浅色百叶',d,z-wh*.3+stripe*.13,width*.85,.022,.015,metal,.215)
   if teaching and col%4==1 and level in (0,1):
    part('空调外机',d+.4,z+1.48,.85,.53,.42,trim,.45)
    for offset in (-.24,.24):part('空调支架',d+.4+offset,z+1.15,.055,.16,.5,metal,.4)
    for vent in range(5):part('外机散热格栅',d+.4,z+1.3+vent*.07,.7,.023,.02,metal,.68)
   if teaching and level<2:
    part('窗下浅色方板',d,z+1.7,width+.22,.65,.12,trim)
    for s in (-1,1):
     part('回纹竖边',d+s*width*.4,z+1.7,.045,.4,.05,wall,.16)
     for t in (-1,1):part('回纹横折',d+s*width*.32,z+1.7+t*.2,width*.18,.045,.05,wall,.16)
  if not teaching and not blank_end:part('通高竖向墙肋',d-spacing/2, floors*3.35/2,.18,floors*3.35,.2,trim)
 if not blank_end:
  for level in range(1,floors+1):part('逐层水平线脚',length/2,level*3.35,length,.1,.14,trim)
 if teaching:
  for level in range(floors*4):part('浅灰墙面分缝',length/2,.55+level*.83,length,.018,.02,metal,.085)
  part('屋顶压边',length/2,floors*3.35+.95,length,.13,.42,roof)
 else:
  part('平屋顶女儿墙',length/2,floors*3.35+.3,length,.6,.18,office)
def text(label,p,z,angle,bid,size=.9,attach=None):
 fontpaths=list(Path('/System/Library/AssetsV2').glob('**/Xingkai.ttc'));font=bpy.data.fonts.load(str(fontpaths[0]))
 for i,ch in enumerate(label):
  c=bpy.data.curves.new(label,'FONT');c.body=ch;c.font=font;c.size=size;c.extrude=.008 if attach else .025;c.resolution_u=5
  o=bpy.data.objects.new(label+' · '+ch,c);bpy.context.collection.objects.link(o);q=xy(p)
  if attach:
   a,b=map(xy,attach);u=(b-a).normalized();normal=Vector((-u.y,u.x,0));q=a+u*(q-a).dot(u)+normal*.012
   angle=math.atan2(u.y,u.x)+math.pi;c.align_x='CENTER'
   o['wall_offset_m']=.012;o['extrusion_m']=.008
  o.location=(q.x,q.y,z-i*size*1.15);o.rotation_euler=(math.pi/2,0,angle);c.materials.append(bronze);o['building_id']=bid
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
parts={
 '46':[
 ('南主楼',[(123,109),(231,91),(234,112),(127,133)],11),
 ('西翼',[(129,60),(143,57),(153,105),(140,107)],11),
 ('东翼',[(189,48),(203,45),(213,94),(199,97)],11),
 ('北侧短翼',[(141,62.7),(192,51),(195,64),(144,76)],7.5)],
 '51':[
 ('北高楼',[(128,168),(205,151),(209,164),(224,161),(226,176),(134,195)],20.1),
 ('南低楼',[(133,221),(192,208),(196,233),(137,247)],10.05),
 ('东连廊',[(185,181),(195,179),(201,214),(191,216)],10.05)],
 '44':[('电光源',[(44,17),(65,12),(69,20),(104,12),(110,33),(49,45)],9)],
 '45':[('兴业光学楼',[(119,0),(210,0),(213,13),(123,32)],9)],
 '50':[('档案馆',[(64,172),(111,161),(119,200),(71,211)],8)],
 '48':[('日研中心',[(24,226),(55,219),(60,248),(30,256)],7)],
 '47':[('外事处',[(0,178),(27,171),(35,198),(13,203),(18,225),(4,228)],8)],
 '52':[('保卫处',[(190,263),(231,253),(235,267),(194,275)],6)],
 '56':[('理科图书馆左翼',[(260,139),(279,139),(279,195),(260,195)],11),('理科图书馆南翼',[(260,195),(355,195),(355,217),(260,217)],11),('理科图书馆右翼',[(337,139),(355,139),(355,195),(337,195)],11),('理科图书馆中楼',[(296,131),(328,131),(328,150),(296,150)],11)]}
for bid,blocks in parts.items():
 for name,pts,h in blocks:
  prism(bid+name,pts,h,wall if bid=='46' else office if bid=='51' else context,bid)
  if bid in ['46','51']:
   prism(name+'薄檐',pts,.16,trim,bid,h)
   # Every exposed side uses the same pixel-derived endpoints as its walls.
   # Image Y increases downward: reverse clockwise image polygons so the
   # right-hand facade normal points OUTSIDE in Blender's XY frame.
   boundary=list(reversed(pts))
   for a,b in zip(boundary,boundary[1:]+boundary[:1]):facade(a,b,round(h/3.35),bid,bid=='46',name)
# Union touching wall volumes and same-level roof caps. This removes the
# duplicate coplanar surfaces that previously made joints flicker.
for bid in ('46','51'):
 groups={}
 for obj in list(bpy.context.scene.objects):
  if obj.type!='MESH' or str(obj.get('building_id',''))!=bid:continue
  if obj.name.startswith(bid):groups.setdefault('body',[]).append(obj)
  elif '薄檐' in obj.name:
   height=round(min(v.co.z for v in obj.data.vertices),2);groups.setdefault(height,[]).append(obj)
 for objects in groups.values():
  base=objects[0]
  for other in objects[1:]:
   bpy.context.view_layer.objects.active=base
   mod=base.modifiers.new('连续连接体','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=other
   bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(other,do_unlink=True)
# Main doorway lies on the south edge of 46; long edge direction from map.
feature_bid='46'
a,b=xy((127,133)),xy((234,112));u=(b-a).normalized();out=Vector((-u.y,u.x,0));out=-out;angle=math.atan2(u.y,u.x)
centre=xy((179,123));centre+=out*.6
box('一教入口深色玻璃门',centre+Vector((0,0,1.65)),(6.5,.18,3.3),glass,angle)
box('一教层叠门廊雨棚',centre+out*.85+Vector((0,0,3.7)),(8.8,2.6,.35),trim,angle)
for z,w in [(3.94,8.9),(4.08,8.7),(4.23,8.95)]:box('门廊叠涩檐口',centre+out*.85+Vector((0,0,z)),(w,2.55,.1),trim,angle)
for d in (-2.2,0,2.2):
 for side in (-1,1):box('门厅铝框竖框',centre+u*(d+side*.97)+out*.15+Vector((0,0,1.65)),(.065,.08,3.2),metal,angle)
 box('门厅上亮横框',centre+u*d+out*.15+Vector((0,0,2.5)),(1.96,.08,.065),metal,angle)
for d in (-1.1,1.1):
 p=centre+u*d+out*1.4;p.z=1.85;bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.26,depth=3.7,location=p);bpy.context.object.data.materials.append(trim);bpy.context.object['building_id']='46'
for d in (-3.5,3.5):box('门廊侧壁柱',centre+u*d+out*.8+Vector((0,0,1.85)),(.55,1.1,3.7),trim,angle)
for i in range(3):box('入口台阶',centre+out*(1.1+i*.38)+Vector((0,0,.3-i*.09)),(9,1.5,.18),trim,angle)
for i in range(48):box('檐口齿饰',centre+u*(-4.1+i*.174)+out*2.1+Vector((0,0,3.6)),(.055,.12,.2),trim,angle)
text('第一教学楼',(194,121),9.9,angle,'46',.85)
# User corrected the photo directions: entrance EAST, garden WEST.
feature_bid='51'
p=xy((198,197));box('综合楼东入口雨棚',p+Vector((1,0,3.3)),(3.8,5.2,.3),roof,.2)
for d in (-1.9,1.9):box('综合楼东雨棚方柱',p+Vector((2,d,1.6)),(.38,.38,3.2),trim)
office_end=((192,208),(196,233))
text('综合楼',(194,219),8.7,0,'51',.78,attach=office_end)
# End-wall stair projection: broad, raised above the roof, with a white cap.
a,b=map(xy,office_end);edge=(b-a).normalized();normal=Vector((-edge.y,edge.x,0));end_angle=math.atan2(edge.y,edge.x)
p=a+edge*8.2+normal*.4
box('综合楼东端通高凸出墙体',p+Vector((0,0,5.5)),(2.2,1.2,11),office,end_angle)
box('凸出墙体顶部白色压边',p+Vector((0,0,11.05)),(2.4,1.42,.18),trim,end_angle)
for d in (.18,(b-a).length-.18):
 q=a+edge*d+normal*.08
 box('综合楼端墙边缘墙垛',q+Vector((0,0,5.1)),(.32,.32,10.2),trim,end_angle)
# West courtyard in the user's reverse-angle photo: grass, rockery, shrubs,
feature_bid=None
# sparse trees and a narrow paved border. Positions are approximate within
# the map-confirmed void; the photographs do not provide surveyed distances.
prism('综合楼西庭院草坪',[(143,196),(182,188),(186,206),(145,215)],.10,lawn,'garden',.04)
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from courtyard_geometry import build_courtyard
build_courtyard(xy,material)
prism('庭院南侧石板步道',[(140,216),(188,206),(190,208),(141,219)],.08,paving,'garden',.02)
# Entrance garden on the EAST side, distinct from the enclosed west court.
prism('东入口草坪',[(206,185),(222,182),(227,210),(204,216)],.10,lawn,'garden',.04)
# Photo-based entrance trees and flower drifts are built by perimeter_vegetation;
# the old spherical placeholders and straight red/yellow strip remain removed.
# Roads are traced as centre-lines from the supplied crop, not fitted around old assets.
routes=[([(30,60),(116,43),(211,24),(230,38),(245,60)],4), ([(40,160),(118,145),(190,132),(221,130),(237,140)],4), ([(245,60),(248,102),(241,131),(245,169),(249,213),(246,260)],5), ([(119,151),(123,184),(129,216),(128,251)],3), ([(126,255),(165,250),(202,243),(212,252),(246,250)],3), ([(55,163),(61,203),(66,232),(72,263)],3)]
routes += [([(246,111),(290,110),(370,110)],5), ([(225,47),(239,64),(225,84),(225,47)],1.8), ([(30,60),(34,108),(40,160)],3)]
prism('街区绿地',[(30,0),(252,0),(252,100),(370,100),(370,240),(252,240),(252,250),(242,250),(242,278),(126,278),(126,260),(0,260),(0,160),(30,160)],.15,grass,'ground',-.2)
for ri,(points,width) in enumerate(routes):
 ps=[xy(p) for p in points];vertices=[]
 for i,p in enumerate(ps):
  before=(ps[i]-ps[i-1]).normalized() if i else (ps[1]-ps[0]).normalized()
  after=(ps[i+1]-ps[i]).normalized() if i<len(ps)-1 else before
  n1=Vector((-before.y,before.x,0));n2=Vector((-after.y,after.x,0));bisector=(n1+n2).normalized()
  offset=bisector*min(width/2/max(bisector.dot(n2),.3),width)
  vertices.extend([(p.x-offset.x,p.y-offset.y,.04),(p.x+offset.x,p.y+offset.y,.04)])
 me=bpy.data.meshes.new('道路连续带');me.from_pydata(vertices,[],[(2*j,2*j+1,2*j+3,2*j+2) for j in range(len(ps)-1)]);me.materials.append(road)
 o=bpy.data.objects.new(f'校图道路 {ri}',me);bpy.context.collection.objects.link(o)
from perimeter_vegetation import build_perimeter
# Narrow planted beds stop short of road edges and the south entrance steps.
for name,poly in [
 ('一教南侧西绿篱草带',[(134,132),(164,126),(165,132),(135,138)]),
 ('一教南侧东绿篱草带',[(203,119),(228,114),(229,119),(204,124)]),
 ('一教后侧棕榈草带',[(140,47),(188,36),(190,47),(142,58)]),
 ('综合楼北侧草带',[(132,153),(202,138),(204,149),(134,164)]),
 ('综合楼东端竹丛草带',[(224,160),(230,159),(232,177),(226,179)])]:
 prism(name,poly,.06,lawn,'garden',.02)
build_perimeter(xy,material,parts,routes,inside,OUT)
labels=[]
names={'46':'第一教学楼','51':'综合办公楼','44':'电光源研究所','45':'兴业光学楼','50':'档案馆','47':'外事处','48':'日研中心','52':'保卫处','56':'理科图书馆'}
for bid,blocks in parts.items():
 ps=[p for _,poly,_ in blocks for p in poly];cx=sum(p[0] for p in ps)/len(ps);cy=sum(p[1] for p in ps)/len(ps);p=xy((cx,cy));labels.append({'id':bid,'name':names[bid],'position':[p.x,max(h for _,_,h in blocks)+1,-p.y],'source':'user-map-trace','category':'building'})
scene=bpy.context.scene;scene.world.color=(.65,.65,.65)
sun=bpy.data.lights.new('日光','SUN');sun.energy=3;o=bpy.data.objects.new('日光',sun);scene.collection.objects.link(o);o.rotation_euler=(.4,-.5,-.4)
bpy.ops.object.camera_add(location=(0,0,160));camera=bpy.context.object;camera.rotation_euler=(0,0,0);camera.data.type='ORTHO';camera.data.ortho_scale=185;camera.location=(4,-15,160);scene.camera=camera
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1300;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.render.filepath=str(ROOT/'output/map-traced-neighbourhood.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/map-traced-neighbourhood.blend'))
bpy.ops.render.render(write_still=True)
# Keep editable pieces in .blend; batch export by building/material for WebGL.
bpy.context.view_layer.update();buckets={}
for obj in list(scene.objects):
 if obj.type!='MESH':continue
 for material_index,mat in enumerate(obj.data.materials):
  polygons=[face for face in obj.data.polygons if face.material_index==material_index]
  if not polygons:continue
  key=(str(obj.get('building_id','detail')),mat.name)
  vertices,faces=buckets.setdefault(key,([],[]));offset=len(vertices)
  vertices.extend(tuple(obj.matrix_world@v.co) for v in obj.data.vertices)
  faces.extend(tuple(offset+i for i in face.vertices) for face in polygons)
bpy.ops.object.select_all(action='DESELECT');export_objects=[]
for (bid,matname),(vertices,faces) in buckets.items():
 mesh=bpy.data.meshes.new(bid+' '+matname);mesh.from_pydata(vertices,[],faces);mesh.materials.append(bpy.data.materials[matname])
 if '假山' in matname or '树干' in matname:
  for face in mesh.polygons:face.use_smooth=True
 obj=bpy.data.objects.new(bid+' '+matname,mesh);scene.collection.objects.link(obj);obj['building_id']=bid;obj.select_set(True);export_objects.append(obj)
path=OUT/'neighbourhood.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False,export_extras=True)
data=path.read_bytes();asset={'id':'map-neighbourhood','url':'neighbourhood.glb','bytes':len(data),'revision':hashlib.sha256(data).hexdigest()[:12]}
(OUT/'manifest.json').write_text(json.dumps({'version':1,'shared':[asset],'buildings':[]},ensure_ascii=False,indent=2))
(OUT/'labels.json').write_text(json.dumps({'buildings':labels},ensure_ascii=False,indent=2))
(OUT/'trace.json').write_text(json.dumps({'scale':.48,'origin':[176,107],'parts':parts,'roads':routes},ensure_ascii=False,indent=2))
print('MAP_NEIGHBOURHOOD_COMPLETE',len(data))
# Reviewable standalone contributions, in exactly the same coordinate frame.
components=OUT/'components';components.mkdir(exist_ok=True);component_manifest=[]
for key in ('46','51','context-landscape'):
 bpy.ops.object.select_all(action='DESELECT')
 for obj in export_objects:
  bid=str(obj.get('building_id',''))
  obj.select_set(bid==key if key!='context-landscape' else bid not in ('46','51'))
 component_path=components/(key+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(component_path),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False,export_extras=True)
 component_data=component_path.read_bytes()
 component_manifest.append({'id':key,'url':key+'.glb','bytes':len(component_data),'sha256':hashlib.sha256(component_data).hexdigest(),'worldOffset':[-167.2,.5,-116]})
(components/'manifest.json').write_text(json.dumps(component_manifest,ensure_ascii=False,indent=2))
