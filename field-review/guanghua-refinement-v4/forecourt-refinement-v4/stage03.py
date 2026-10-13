import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(O/'stage02-east-urn.blend'));s=bpy.context.scene;before=all_digests()
cams={'top':camera('V4 straight path overhead',(78,46,130),(78,46,0),90),
 '4492':camera('V4 approximate photo4492',(65.4,81,1.7),(65.4,34,1.0),lens=26)}
render('stage03-before-4492.png',cams['4492'],width=1000,samples=10)
walk=bpy.data.objects['EDGE_PATHS__edge-walk__FIN_pavers'];changed=[walk.name]
ps=[walk.matrix_world@v.co for v in walk.data.vertices if (walk.matrix_world@v.co).x>50]
x0,x1=min(p.x for p in ps),max(p.x for p in ps);y0,y1=min(p.y for p in ps),max(p.y for p in ps)
west_vertices=sorted(tuple(v.co) for v in walk.data.vertices if (walk.matrix_world@v.co).x<0)
bm=bmesh.new();bm.from_mesh(walk.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if (walk.matrix_world@v.co).x>50],context='VERTS');bm.to_mesh(walk.data);bm.free()
assert west_vertices==sorted(tuple(v.co) for v in walk.data.vertices)
def brickpattern(x,y,rng):
 row=np.floor(y/.3).astype(int);u=np.mod(x+((row%2)*.3),.6);v=np.mod(y,.3)
 seam=(u<.009)|(v<.008);return -.048*seam+.012*np.sin(np.floor((x+row%2*.3)/.6)*17+row*11)
paver=texture_material('V4 walkway rectangular pavers',(.47,.455,.43),(1.2,.6),brickpattern)
fid='E_WALK';refs=[4492];band=.33;new=[]
main=prism('E_WALK central staggered paving',[(x0+band,y0),(x1-band,y0),(x1-band,y1),(x0+band,y1)],-.02,.045,paver,fid,refs);uv(main);new.append(main)
# Texture axes are metre coordinates, preserving the rectangular module along Y.
for li in main.data.loops:
 q=main.data.vertices[li.vertex_index].co;main.data.uv_layers.active.data[li.index].uv=(q.x/1.2,q.y/.6)
stone=bpy.data.materials['FC_light_band'];n=math.ceil((y1-y0)/.65);pitch=(y1-y0)/n
for side,(a,b) in enumerate(((x0,x0+band),(x1-band,x1))):
 for i in range(n):
  ya=y0+i*pitch+.002;yb=y0+(i+1)*pitch-.002;cx=(a+b)/2;cy=(ya+yb)/2-.10
  nx=10;ny=20;vs=[];fs=[]
  for j in range(ny+1):
   y=ya+(yb-ya)*j/ny
   for k in range(nx+1):
    x=a+(b-a)*k/nx;rad=math.hypot(x-cx,y-cy);dist=abs(rad-.23)
    groove=.06*math.exp(-(dist/.038)**2) if y>=cy else 0
    vs.append((x,y,.11-groove))
  topcount=len(vs)
  for j in range(ny):
   for k in range(nx):q=j*(nx+1)+k;fs.append((q,q+1,q+nx+2,q+nx+1))
  edge=list(range(nx+1))+[(j*(nx+1)+nx) for j in range(1,ny+1)]+[ny*(nx+1)+k for k in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
  vs.extend([(vs[q][0],vs[q][1],-.02) for q in edge]);fs.append(tuple(reversed(range(topcount,len(vs)))))
  for k,q in enumerate(edge):r=edge[(k+1)%len(edge)];fs.append((q,topcount+k,topcount+(k+1)%len(edge),r))
  ob=mesh('E_WALK recessed arc band %d %03d'%(side,i),vs,fs,stone,fid,refs);ob['estimated_groove_depth']=.06;ob['estimated_band_width']=band;new.append(ob)
solids=[solid_check(ob) for ob in new];unchanged=verify_unchanged(before,changed)
s.camera=cams['4492'];bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage03-straight-path.blend'))
save_report('stage03',dict(protected_meshes_unchanged=unchanged,west_straight_walk_vertices_unchanged=True,walk_bounds=[x0,x1,y0,y1],central_width=x1-x0-band*2,separate_border_solids=2*n,estimated_border_width=band,estimated_groove_depth=.06,estimated_border_pitch=pitch,solids=solids,views=['top','4492']))
for k,cam in cams.items():render('stage03-after-'+k+'.png',cam,k=='top',width=1400,samples=24)
print('STAGE03_COMPLETE',flush=True)
