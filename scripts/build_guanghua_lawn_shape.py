"""Frozen satellite trace -> isolated lawn mesh and review drawings. No campus writes."""
from pathlib import Path
import json, math, hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'field-review/guanghua-lawn-shape-v2'
BASE=ROOT/'field-review/guanghua-lawn-survey-v1/model/guanghua-lawn-v1.blend'
# Pixel coordinates in the preserved 3056 x 1588 screenshot (crop origin 1080,560).
# North edge follows the visible grass/paving interface. South is obscured by trees.
NORTH=[(94,199),(119,188),(143,181),(160,178),(188,182),(221,185),(252,183),(282,179),(311,171),(340,160),(367,146),(391,129),(412,110),(430,92),(449,77),(469,65),(490,56)]
SW=(190,480); SE=(589,337)
SCALE=20/96 # screenshot scale bar, approximately 96 original pixels
ux,uy=396/math.hypot(396,143),-143/math.hypot(396,143)
def world(p):
    dx,dy=p[0]-SW[0],p[1]-SW[1]
    return ((dx*ux+dy*uy)*SCALE,(dx*uy-dy*ux)*SCALE)
def smooth(points,steps=8):
    # Centripetal-looking bounded interpolation: cubic Bezier with local tangents.
    out=[]
    for i in range(len(points)-1):
        a=points[max(0,i-1)];b=points[i];c=points[i+1];d=points[min(len(points)-1,i+2)]
        for j in range(steps):
            t=j/steps
            out.append(tuple(.5*(2*b[k]+(-a[k]+c[k])*t+(2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+(-a[k]+3*b[k]-3*c[k]+d[k])*t**3) for k in (0,1)))
    return out+[points[-1]]
trace=[SW,SE]+list(reversed(smooth(NORTH)))
poly=[world(p) for p in trace]
area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2
meta={'feature_id':'LAWN','reference':'satellite-reference.png','source_sha256':hashlib.sha256((OUT/'satellite-reference.png').read_bytes()).hexdigest(),'source_size':[3056,1588],'crop_origin':[1080,560],'north_trace_crop_pixels':NORTH,'south_corners_crop_pixels':[SW,SE],'metres_per_pixel':SCALE,'scale_status':'Approximate screenshot scale; not surveyed','shape_status':'User-fixed satellite outline; south edge reconstructed through canopy using ground photos','north_edge':'Concave plaza-facing edge, traced without imposing symmetry','width_m':world(SE)[0],'west_length_m':world(NORTH[0])[1],'area_m2':area,'ground_photos':[4315,4320,4474,4494,4519,4600],'height_status':'Planar top z=0; 0.18m closed backing is a modeling convention, not measured terrain','polygon_xy':poly}
if '--draw' in sys.argv:
    from PIL import Image,ImageDraw,ImageFont
    fontpath='C:/Windows/Fonts/msyh.ttc'
    def font(n):return ImageFont.truetype(fontpath,n)
    im=Image.new('RGB',(1600,1340),'#f7f7f2');d=ImageDraw.Draw(im)
    d.text((80,42),'光华楼主草坪 · 固定轮廓',font=font(42),fill='#213b36')
    d.text((82,105),'卫星截图描边  /  正交俯视  /  2026-09-27',font=font(23),fill='#63736e')
    def screen(p):return (260+p[0]*12,1040-p[1]*12)
    pp=[screen(p) for p in poly]
    d.rectangle((210,240,1380,1090),fill='#e6e6de')
    d.polygon(pp,fill='#78a75c')
    d.line(pp+[pp[0]],fill='#365b36',width=4)
    # Dashed south outline distinguishes canopy-inferred boundary.
    a,b=pp[:2]
    for i in range(0,60,2):
        t=i/60;u=(i+1)/60
        d.line((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u),fill='#f4d58b',width=7)
    d.text((570,190),'光华楼方向（场地北侧） ↑',font=font(27),fill='#44544e')
    d.text((650,318),'楼前广场',font=font(28),fill='#63736e')
    d.text((604,454),'北侧内凹弧边',font=font(25),fill='#365b36')
    d.text((665,685),'连续主草坪',font=font(36),fill='#fffef4')
    d.text((626,744),f'约 {area:.0f} ㎡（截图估算）',font=font(23),fill='#f5f9ee')
    d.text((590,1098),f'东西宽约 {world(SE)[0]:.0f} m',font=font(25),fill='#43554c')
    d.text((80,1144),'绿色实线：可见边界描摹    黄色虚线：树冠遮挡下的南侧直边推定',font=font(24),fill='#43554c')
    d.text((80,1190),'尺度依据截图 20 米标尺；场地轴线已摆正，图上方不等于严格地理正北。',font=font(23),fill='#65736d')
    d.text((80,1233),'本轮仅完成草坪本体；平面标高与土层厚度为建模约定。',font=font(23),fill='#65736d')
    im.save(OUT/'lawn-top-view.png')
    src=Image.open(OUT/'satellite-reference.png').convert('RGB');dr=ImageDraw.Draw(src)
    path=[(x+1080,y+560) for x,y in trace]
    dr.line(path[1:]+[path[0]],fill='#ffff35',width=5)
    for i in range(0,60,2):
        a,b=path[:2];t=i/60;u=(i+1)/60
        dr.line((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u),fill='#ffad35',width=6)
    src.crop((1120,580,1720,1080)).resize((1200,1000)).save(OUT/'satellite-trace-overlay.png')
    (OUT/'outline.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:meta[k] for k in ['width_m','west_length_m','area_m2']}))
    sys.exit()

import bpy,bmesh
from mathutils import Vector
before=hashlib.sha256(BASE.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.unit_settings.system='METRIC'
mesh=bpy.data.meshes.new('LAWN_satellite_boundary')
n=len(poly);vertices=[(x,y,z) for z in [-.18,0] for x,y in poly]
faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh.from_pydata(vertices,[],faces);mesh.update()
ob=bpy.data.objects.new('LAWN | satellite-fixed concave north edge',mesh);s.collection.objects.link(ob)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
for k,v in meta.items():
    if isinstance(v,(str,int,float)):ob[k]=v
ob['source_photos']='4315,4320,4474,4494,4519,4600'
mat=bpy.data.materials.new('Grass | restrained procedural variation');mat.use_nodes=True
mat.diffuse_color=(.25,.38,.09,1)
nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.95
bs.inputs['Base Color'].default_value=(.25,.38,.09,1)
noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7;noise.inputs['Detail'].default_value=2
ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.16,.29,.055,1);ramp.color_ramp.elements[1].color=(.33,.46,.14,1)
links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(mat)
bpy.context.view_layer.objects.active=ob;ob.select_set(True)
bm=bmesh.new();bm.from_mesh(mesh)
assert all(e.is_manifold for e in bm.edges)
volume=bm.calc_volume(signed=True);assert volume>0
assert abs(volume-area*.18)<.1
bm.free()
worldmat=bpy.data.worlds.new('Soft daylight');worldmat.use_nodes=True;worldmat.node_tree.nodes['Background'].inputs[0].default_value=(.8,.85,.9,1);worldmat.node_tree.nodes['Background'].inputs[1].default_value=.8;s.world=worldmat
ld=bpy.data.lights.new('Sun','SUN');ld.energy=2;lo=bpy.data.objects.new('Sun',ld);s.collection.objects.link(lo);lo.rotation_euler=(.2,-.3,-.2)
cd=bpy.data.cameras.new('Orthographic top');cam=bpy.data.objects.new('Orthographic top',cd);s.collection.objects.link(cam);cam.location=(44,30,150);cd.type='ORTHO';cd.ortho_scale=104;s.camera=cam
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=1500;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.film_transparent=True
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_rotation=(1,0,0,0);a.spaces.active.region_3d.view_location=(44,30,0);a.spaces.active.region_3d.view_distance=110;a.spaces.active.region_3d.view_perspective='ORTHO'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'guanghua-lawn-shape-v2.blend'))
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
for link in list(bs.inputs['Base Color'].links):links.remove(link)
bpy.ops.export_scene.gltf(filepath=str(OUT/'guanghua-lawn-shape-v2.glb'),export_format='GLB',use_selection=True,export_extras=True)
links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
s.render.filepath=str(OUT/'lawn-model-top.png');bpy.ops.render.render(write_still=True)
cam.location=(112,-80,105);cam.rotation_euler=(Vector((44,30,0))-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=110
s.render.filepath=str(OUT/'lawn-model-oblique.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'guanghua-lawn-shape-v2.blend'))
assert bpy.data.objects.get('LAWN | satellite-fixed concave north edge') is not None
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==before
(OUT/'validation.json').write_text(json.dumps({'closed_manifold':True,'positive_volume_m3':volume,'expected_volume_m3':area*.18,'baseline_unchanged':True,'checkpoint_reopened':True,'baseline_sha256':before},indent=2),encoding='utf-8')
