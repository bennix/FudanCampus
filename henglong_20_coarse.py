import bpy, json, math

obj = bpy.data.objects['恒隆物理楼']
assert obj.type == 'MESH' and len(obj.modifiers) == 0
verts, faces, indices = [], [], []
def box(x,y,z,w,d,h,mat):
    n=len(verts)
    verts.extend([(x+a*w/2,y+b*d/2,z+c*h/2) for a,b,c in
                  [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]])
    faces.extend([tuple(n+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
    indices.extend([mat]*6)

def column(x,y,z,r,h,mat):
    n=len(verts)
    for dz in [-h/2,h/2]:
        verts.extend([(x+r*math.cos(i*math.tau/12),y+r*math.sin(i*math.tau/12),z+dz) for i in range(12)])
    faces.append(tuple(n+i for i in reversed(range(12))))
    faces.append(tuple(n+12+i for i in range(12)))
    indices.extend([mat,mat])
    for i in range(12):
        j=(i+1)%12
        faces.append((n+i,n+j,n+12+j,n+12+i))
        indices.append(mat)

def ramp(x0,x1,y,w,z0,z1,zbase):
    n=len(verts)
    verts.extend([(x0,y-w/2,zbase),(x0,y+w/2,zbase),
                  (x1,y+w/2,zbase),(x1,y-w/2,zbase),
                  (x0,y-w/2,z0),(x0,y+w/2,z0),
                  (x1,y+w/2,z1),(x1,y-w/2,z1)])
    faces.extend([tuple(n+i for i in f) for f in
                  [(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)]])
    indices.extend([2]*6)

# Five floors, raised central main entrance, symmetric recessed side entrances.
cx,cy,base=-40.0,202.4,0.25
length,depth,height=92.8,13.6,16.30110168457
front=cy-depth/2
floor=height/5
# Shallow recesses in the same south facade, without Boolean modifiers.
side_entries=[-24.9,24.9]
left=-length/2
for offset in side_entries:
    a,b=offset-3.8,offset+3.8
    box(cx+(left+a)/2,cy,base+height/2,a-left,depth,height,0)
    box(cx+offset,cy+0.65,base+height/2,7.6,depth-1.3,height,0)
    box(cx+offset,front+0.65,base+(height+3.0)/2,7.6,1.3,height-3.0,0)
    left=b
box(cx+(left+length/2)/2,cy,base+height/2,length/2-left,depth,height,0)
box(cx,cy,base+height+0.15,length+0.5,depth+0.65,0.3,2)
box(cx,cy,base+0.2,length,depth+0.1,0.4,2)

# Broad window groups; no individual frames, UVs or reflective glazing.
pitch=2.45
for side in [-1]:
    yy=cy+side*(depth/2+0.04)
    for j in range(-18,19):
        xx=cx+j*pitch
        for level in range(5):
            if level==0 and any(abs(xx-cx-o)<3.8 for o in side_entries): continue
            box(xx,yy,base+level*floor+1.8,1.60,0.07,2.05,3)
    for j in range(-19,19):
        px=(j+0.5)*pitch
        bottom=3.0 if any(abs(px-o)<3.8 for o in side_entries) else 0.15
        box(cx+px,yy+side*0.055,base+(height+bottom)/2,0.78,0.18,height-bottom,1)

# Central main entrance from photo 1; raised top floor and projecting flat eaves.
for offset in [0.0]:
    xx=cx+offset
    th=height+3.1
    box(xx,front+1.45,base+th/2,10.6,3.7,th,0)
    fy=front-0.43
    for dx in [-4.45,4.45]:
        box(xx+dx,fy,base+th/2,1.7,0.22,th,1)
    for level in range(1,6):
        zz=base+level*floor+1.5
        box(xx,fy-0.02,zz,6.95,0.1,1.95,3)
    for dx in [-2.05,2.05]:
        box(xx+dx,fy-0.11,base+th/2,0.32,0.14,th-0.5,2)
    box(xx,front+1.4,base+th+0.15,11.8,4.9,0.3,2)
    # Entrance-only refinement: deeper fascia, round columns, layered soffit.
    entrance_start=len(verts)
    box(xx,front-2.5,base+4.43,29.0,5.8,0.22,2)
    box(xx,front-5.32,base+4.88,29.0,0.18,1.17,2)
    for dx in [-14.41,14.41]:
        box(xx+dx,front-2.5,base+4.88,0.18,5.8,1.17,2)
    box(xx,front-2.4,base+4.20,27.5,4.9,0.24,2)
    box(xx,front-1.4,base+4.01,7.0,2.8,0.18,2)
    for dx in [-2.9,2.9]:
        column(xx+dx,front-4.9,base+2.46,0.22,3.72,2)
    for dx in [-7.5,7.5]:
        for dy in [-5.15,-2.23]:
            column(xx+dx,front+dy,base+(1.05+4.08)/2,0.22,4.08-1.05,2)
    # Four additional outer columns, two on each ramp's solid edge walls.
    # Their bases meet the wall caps and their tops meet the canopy soffit.
    for dx in [-13.0,13.0]:
        for dy in [-4.87,-2.23]:
            wall_top=0.60-(abs(dx)-8.5)/11.0*0.575+0.45
            column(xx+dx,front+dy,base+(wall_top+4.08)/2,0.22,4.08-wall_top,2)
    # Sparse inset-square rhythm on the broad canopy fascia.
    for row in range(3):
        for k in range(43):
            px=xx-13.8+k*0.65+(0.16 if row==1 else 0)
            box(px,front-5.415,base+4.53+row*0.34,0.10,0.015,0.10,3)
    # Bronze-toned portal surrounds and broad dark glazed opening.
    box(xx,fy-0.09,base+2.11,4.6,0.15,3.02,3)
    for dx in [-2.48,2.48]:
        box(xx+dx,fy-0.14,base+2.16,0.32,0.28,3.12,4)
    box(xx,fy-0.16,base+3.68,5.3,0.30,0.55,4)
    for dx in [-1.15,0,1.15]:
        box(xx+dx,fy-0.19,base+1.98,0.055,0.065,2.4,5)
    box(xx,fy-0.19,base+3.13,4.6,0.065,0.07,5)
    for dx in [-3.15,3.15]:
        box(xx+dx,fy-0.04,base+2.05,0.85,0.12,2.7,3)
    # Continuous landing, front stair and long lateral ramps, all building geometry.
    box(xx,front-2.95,base+0.30,17.0,5.30,0.60,2)
    for i in range(5):
        box(xx,front-7.22+i*0.36,base+0.06*(i+1),6.1,0.36,0.12*(i+1),2)
    ramp(xx-19.5,xx-8.5,front-3.55,2.2,base+0.025,base+0.60,base)
    ramp(xx+8.5,xx+19.5,front-3.55,2.2,base+0.60,base+0.025,base)
    # Wall tops and coping follow the ramp, always 0.45 above its surface.
    # Both ends remain open for passage; these are not railings or planters.
    for sign in [-1,1]:
        x0,x1=(xx-19.5,xx-8.5) if sign==-1 else (xx+8.5,xx+19.5)
        h0,h1=(0.025,0.60) if sign==-1 else (0.60,0.025)
        for dy in [-4.87,-2.23]:
            ramp(x0,x1,front+dy,0.44,base+h0+0.40,base+h1+0.40,base)
            n=len(verts)
            ramp(x0,x1,front+dy,0.48,base+h0+0.45,base+h1+0.45,base)
            # Lift coping underside to make a uniform 0.05-thick sloping cap.
            for j in [0,1]:
                x,y,z=verts[n+j]; verts[n+j]=(x,y,base+h0+0.40)
            for j in [2,3]:
                x,y,z=verts[n+j]; verts[n+j]=(x,y,base+h1+0.40)

    # Continue the ramp walls around the level platform; keep access routes open.
    def level_wall(x,y,w,d):
        box(x,y,base+0.50,w,d,1.0,2)
        box(x,y,base+1.025,w+0.04,d+0.04,0.05,2)
    for sign in [-1,1]:
        # Rear wall returns to the facade beside the central entrance.
        level_wall(xx+sign*5.9,front-2.23,5.2,0.44)
        level_wall(xx+sign*3.3,front-1.38,0.44,1.7)
        # Front wall joins the planter and the ramp without closing either route.
        level_wall(xx+sign*7.175,front-5.15,2.65,0.44)
        level_wall(xx+sign*8.28,front-5.01,0.44,0.72)
        # Symmetric hollow stone planters directly beside the stair opening.
        px=xx+sign*4.55
        py=front-6.05
        w,d,t=3.0,2.4,0.22
        for dy in [-d/2+t/2,d/2-t/2]:
            box(px,py+dy,base+0.50,w,t,1.0,2)
            box(px,py+dy,base+1.025,w+0.04,t+0.04,0.05,2)
        for dx in [-w/2+t/2,w/2-t/2]:
            box(px+dx,py,base+0.50,t,d-2*t,1.0,2)
            box(px+dx,py,base+1.025,t+0.04,d-2*t,0.05,2)
        box(px,py,base+0.87,w-2*t,d-2*t,0.08,6)

    # Front-elevation proportions: broader central passage, shorter lateral canopy.
    # Apply consistently to columns, connected walls, ramps, stairs and planters.
    def entrance_x(x):
        dx=x-cx
        a=abs(dx)
        a=a*1.2 if a<=3.05 else 3.66+(a-3.05)*0.69
        return cx+math.copysign(a,dx)
    for i in range(entrance_start,len(verts)):
        x,y,z=verts[i]
        verts[i]=(entrance_x(x),y,base+(z-base)*1.12)

# Symmetric recessed side entrances from photo 2.
for offset in side_entries:
    box(cx+offset,front+1.25,base+1.4,6.8,0.1,2.8,3)
    box(cx+offset,front+0.5,base+0.09,7.6,1.6,0.18,2)

mesh=bpy.data.meshes.new('恒隆物理楼_粗修网格')
mesh.from_pydata(verts,[],faces)
mesh.update()
for name,color in [('浅灰墙体',(0.69,0.71,0.67,1)),('红褐墙柱',(0.40,0.17,0.115,1)),('浅色檐口',(0.62,0.64,0.59,1)),('深色窗组',(0.065,0.115,0.135,1)),('入口色带',(0.43,0.34,0.22,1)),('门框及楼名',(0.09,0.075,0.055,1)),('花坛土面',(0.12,0.085,0.045,1))]:
    mat=bpy.data.materials.new('恒隆20_'+name)
    mat.diffuse_color=color
    mat.use_nodes=False
    mesh.materials.append(mat)
for p,i in zip(mesh.polygons,indices): p.material_index=i
# Retain the original mesh datablock as a recoverable backup; edit this object only.
old=obj.data
old.use_fake_user=True
if 'coarse_original_mesh' not in obj:
    obj['coarse_original_mesh']=old.name
# Convert world coordinates into existing object coordinates without changing its transform.
inv=obj.matrix_world.inverted()
for v in mesh.vertices: v.co=inv@v.co
obj.data=mesh
obj['coarse_reference']='第一张中央正门；第二张对称侧门；同一南立面'
obj['coarse_front_axis']='-Y / south'
obj['coarse_script']='E:/BlenderModel/FudanCampus/henglong_20_coarse.py'
font_path='C:/Users/22624/xwechat_files/wxid_kzd6hj99l89u22_f94f/msg/file/2026-09/fudan(1).ttf'
uploaded_font=bpy.data.fonts.load(font_path,check_existing=True)
uploaded_font.pack()
# The supplied font is a symbol library without the five Chinese glyphs.
# Use an explicit provisional KaiTi fallback until a matching text font is supplied.
font=bpy.data.fonts.load('C:/Windows/Fonts/simkai.ttf',check_existing=True)
font.pack()
label=bpy.data.objects.get('恒隆20_正门楼名')
if label is None:
    text_data=bpy.data.curves.new('恒隆20_楼名字体','FONT')
    label=bpy.data.objects.new('恒隆20_正门楼名',text_data)
    obj.users_collection[0].objects.link(label)
else:
    text_data=label.data
text_data.body='恒隆物理楼'
text_data.font=font
text_data.size=0.49*1.12
text_data.space_character=1.22
text_data.extrude=0.012
text_data.resolution_u=4
text_data.align_x='CENTER'
text_data.materials.clear()
text_data.materials.append(mesh.materials[5])
label.parent=obj
label.matrix_parent_inverse=obj.matrix_world.inverted()
label.location=(cx,front-0.76,base+3.51*1.12)
label.rotation_euler=(math.pi/2,0,0)
label['building_id']='20'
label['font_note']='临时楷体；用户fudan字体未包含恒隆物理楼中文字形'
print(json.dumps({'modified':obj.name,'mesh_faces':len(mesh.polygons),'original_mesh_backup':old.name},ensure_ascii=False))
