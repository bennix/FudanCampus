"""Batched geometry for the October photo-derived review models (metres, Z up)."""
import bpy, math, random, json
from mathutils import Vector
from pathlib import Path
R=random.Random(20261020)
B={}
def reset():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);B.clear()
def mat(name,c,rough=.8,grain=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough
    if grain:
        n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=grain
        b=m.node_tree.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.22;b.inputs['Distance'].default_value=.035
        m.node_tree.links.new(n.outputs['Fac'],b.inputs['Height']);m.node_tree.links.new(b.outputs[0],p.inputs['Normal'])
    return m
def brickmat(name,c):
    m=mat(name,c);m['uv_scale']=1.0
    im=bpy.data.images.new(name+' baked brick',width=256,height=256)
    pixels=[]
    for y in range(256):
        row=y//32
        for x in range(256):
            joint=y%32<2 or (x+(row%2)*32)%64<2
            noise=R.uniform(.90,1.08);rgb=(.44,.40,.34) if joint else tuple(v*noise for v in c)
            pixels.extend((*rgb,1))
    im.pixels=pixels;im.pack()
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    return m
def mesh(name,v,f,m):
    vs,fs=B.setdefault((name,m),([],[]));k=len(vs);vs.extend(v);fs.extend([tuple(k+i for i in a) for a in f])
def box(name,x,y,z,w,d,h,m,a=0):
    v=[]
    for i,j,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]:
        u=i*w/2;t=j*d/2;v.append((x+u*math.cos(a)-t*math.sin(a),y+u*math.sin(a)+t*math.cos(a),z+k*h/2))
    mesh(name,v,[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)],m)
def rod(name,a,b,r,m,r2=None,n=8):
    a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
    if u.length<.001:u=axis.cross(Vector((0,1,0)))
    u.normalize();v=axis.cross(u);r2=r if r2 is None else r2
    vs=[tuple(p+rr*(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))) for p,rr in [(a,r),(b,r2)] for i in range(n)]
    mesh(name,vs,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],m)
def ellipse(name,x,y,rx,ry,z,m,n=96):
    mesh(name,[(x,y,z)]+[(x+rx*math.cos(i*math.tau/n),y+ry*math.sin(i*math.tau/n),z) for i in range(n)],[(0,i+1,(i+1)%n+1) for i in range(n)],m)
def ring(name,x,y,rx,ry,width,z,h,m,n=96,start=0,end=math.tau):
    for i in range(n):
        a=start+(end-start)*i/n;b=start+(end-start)*(i+1)/n
        pts=[(x+r*math.cos(t),y+s*math.sin(t),zz) for zz in [z,z+h] for r,s,t in [(rx,ry,a),(rx,ry,b),(rx-width,ry-width,b),(rx-width,ry-width,a)]]
        mesh(name,pts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m)
def leaf(name,x,y,z,s,m,thin=.42):
    a=R.random()*math.tau;u=Vector((math.cos(a),math.sin(a),R.uniform(-.55,.55)))*s;v=Vector((-math.sin(a),math.cos(a),.1))*s*thin;p=Vector((x,y,z))
    mesh(name,[tuple(p-u),tuple(p+v),tuple(p+u),tuple(p-v),tuple(p+Vector((0,0,s*.12)))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],m)
def rock(name,x,y,z,s,m):
    # Irregular faceted boulder with non-uniform rings.
    vs=[];n=9
    for k in range(4):
        t=math.pi*(.12+.78*k/3)
        for j in range(n):
            a=j*math.tau/n;f=R.uniform(.8,1.17);vs.append((x+s[0]*math.sin(t)*math.cos(a)*f,y+s[1]*math.sin(t)*math.sin(a)*f,z+s[2]*math.cos(t)*f))
    mesh(name,vs,[tuple(range(n-1,-1,-1)),tuple(range(3*n,4*n))]+[(k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j) for k in range(3) for j in range(n)],m)
def tree(x,y,h,kind,bark,greens):
    name='vegetation '+kind
    top=Vector((x+.3,y+.1,h));rod(name+' trunk',(x,y,0),top,.22 if kind=='cedar' else .32,bark,.08)
    if kind=='palm':
        for k in range(int(h*7)):ring(name+' bark',x,y,.23,.23,.04,k/7,.065,bark,n=8)
        for i in range(15):
            a=i*math.tau/15;end=Vector((x+1.2*math.cos(a),y+1.2*math.sin(a),h+R.uniform(-.45,.8)));rod(name+' frond stem',top,end,.025,bark)
            for j in range(22):
                t=a+(j-10.5)*.125;p=end+Vector((1.2*math.cos(t),1.2*math.sin(t),-.35+.22*math.cos((j-10.5)*.125)))
                mesh(name+' fan',[tuple(end),tuple(p),tuple(p+Vector((-.085*math.sin(t),.085*math.cos(t),.03)))],[(0,1,2)],R.choice(greens))
        return
    for i in range(16 if kind!='willow' else 24):
        a=i*2.399;zz=h*(.35+.60*i/15) if kind=='cedar' else h*R.uniform(.55,.95)
        radius=(h-zz)*.6 if kind=='cedar' else R.uniform(1.5,3.8)
        p=Vector((x+radius*math.cos(a),y+radius*math.sin(a),zz));rod(name+' branches',(x,y,zz-.8),p,.09,bark,.022)
        if kind=='willow':
            for j in range(7):
                q=p+Vector((R.uniform(-.7,.7),R.uniform(-.7,.7),0));length=R.uniform(2,4)
                rod(name+' hanging twigs',q,q+Vector((.2,.1,-length)),.009,bark)
                for k in range(75):
                    t=k/75;leaf(name+' leaves',q.x+.2*t+R.uniform(-.20,.20),q.y+R.uniform(-.18,.18),q.z-length*t,.18,R.choice(greens),.16)
        else:
            for j in range(520):
                t=R.random()*math.tau;r=R.random()**.5*1.35
                leaf(name+' leaves',p.x+r*math.cos(t),p.y+r*math.sin(t),p.z+R.uniform(-.7,.7),R.uniform(.13,.28),R.choice(greens),.25 if kind=='cedar' else .42)
def shrub(x,y,rx,ry,h,greens,n=600):
    for i in range(n):
        a=R.random()*math.tau;r=R.random()**.5
        leaf('shrubs',x+rx*r*math.cos(a),y+ry*r*math.sin(a),.12+h*math.sqrt(1-r*r)+R.uniform(-.1,.1),.16,R.choice(greens))
def grass(x,y,m):
    for i in range(32):
        a=R.random()*math.tau;r=R.uniform(.2,.48);h=R.uniform(.18,.5)
        pts=[]
        for k in range(5):
            t=k/4;rr=r*t;z=.03+h*math.sin(t*math.pi*.8);w=.013*(1-t)+.001
            pts.extend([(x+rr*math.cos(a)-w*math.sin(a),y+rr*math.sin(a)+w*math.cos(a),z),(x+rr*math.cos(a)+w*math.sin(a),y+rr*math.sin(a)-w*math.cos(a),z)])
        mesh('mondo grass',pts,[(k*2,k*2+1,k*2+3,k*2+2) for k in range(4)],m)
def flush():
    objects=[]
    for (name,m),(v,f) in B.items():
        data=bpy.data.meshes.new(name);data.from_pydata(v,[],f);data.materials.append(m);data.update()
        if m.get('uv_scale'):
            uv=data.uv_layers.new(name='world metres')
            for poly in data.polygons:
                axis=max(range(3),key=lambda i:abs(poly.normal[i]));axes=[i for i in range(3) if i!=axis]
                for li in poly.loop_indices:
                    co=data.vertices[data.loops[li].vertex_index].co
                    uv.data[li].uv=(co[axes[0]],co[axes[1]])
        ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob['basis']='User photos; dimensions and unobserved connections inferred';objects.append(ob)
    B.clear();return objects
def text_obj(body,pos,size,m,angle=0):
    cu=bpy.data.curves.new(body,'FONT');cu.body=body;cu.size=size;cu.align_x='CENTER';cu.extrude=.008
    try:cu.font=bpy.data.fonts.load('/System/Library/Fonts/STHeiti Medium.ttc')
    except RuntimeError:pass
    o=bpy.data.objects.new(body,cu);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(math.pi/2,0,angle);cu.materials.append(m)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
    # Font triangulation occasionally emits collapsed faces at stroke intersections.
    import bmesh
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_area()<=1e-9 or o.data.polygons[f.index].area<=1e-12],context='FACES_ONLY')
    bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_edges],context='VERTS')
    bm.to_mesh(o.data);bm.free();o.data.update()
def finish(out,stem,views):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);flush();scene=bpy.context.scene
    scene.world.use_nodes=True;bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.67,.73,.78,1);bg.inputs[1].default_value=.65
    light=bpy.data.lights.new('Cloud-filtered sunlight','SUN');light.energy=2;light.angle=.32;o=bpy.data.objects.new('Cloud-filtered sunlight',light);scene.collection.objects.link(o);o.rotation_euler=(.45,-.5,-.6)
    camera=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));scene.collection.objects.link(camera);scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True;scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    bpy.ops.object.select_all(action='DESELECT')
    for ob in scene.objects:
        if ob.type=='MESH':ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/(stem+'.glb')),export_format='GLB',use_selection=True,export_extras=True)
    camera.location=views[0][1];camera.rotation_euler=(Vector(views[0][2])-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=42
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(stem+'.blend')))
    for name,pos,target in views:
        camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=42
        scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
    meshes=[o for o in scene.objects if o.type=='MESH'];tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
    (out/'geometry-report.json').write_text(json.dumps({'objects':len(meshes),'triangles':tri,'dimensions':'approximate metres','source':'user photographs','renders':[v[0]+'.png' for v in views]},indent=2))
