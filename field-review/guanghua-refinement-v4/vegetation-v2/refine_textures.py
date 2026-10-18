import bpy, numpy as np, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from export_visible_glb import export_visible_glb
O=Path.cwd()/'field-review/guanghua-refinement-v4/vegetation-v2';bpy.ops.wm.open_mainfile(filepath=str(O/'vegetation-v2.blend'))
rng=np.random.default_rng(930);n=2048
# Periodic random noise, many orientations: no directional sine bands.
freq=np.fft.fftfreq(n);fx,fy=np.meshgrid(freq,freq);r=fx*fx+fy*fy
noise=rng.normal(size=(n,n));spectrum=np.fft.fft2(noise)
def blurred(scale):
 a=np.fft.ifft2(spectrum*np.exp(-r*scale*scale)).real;a-=a.mean();return a/max(a.std(),1e-5)
coarse=blurred(150);medium=blurred(25);fine=rng.normal(size=(n,n));variation=.007*coarse+.005*medium+.009*fine
for name in ['FIN_grass','FIN_garden_grass']:
 m=bpy.data.materials[name];im=bpy.data.images['V2_'+name];rgba=np.ones((n,n,4),np.float32)
 for k,b in enumerate([.30,.355,.16]):rgba[:,:,k]=np.clip(b+variation,.03,.8)
 im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(O/('V2_'+name+'.png'));im.save();im.pack()
# Preserve paving character with a simple rectangular tile texture.
m=bpy.data.materials['FIN_pavers'];im=bpy.data.images['V2_FIN_pavers'];n=512;y,x=np.mgrid[:n,:n];row=y//64;xx=(x+(row%2)*64)%128
joint=(xx<2)|(y%64<2);tone=rng.normal(0,.004,(n,n));rgba=np.ones((n,n,4),np.float32)
for k,b in enumerate([.45,.46,.43]):rgba[:,:,k]=b+tone-.08*joint
im.pixels.foreach_set(rgba.ravel());im.save();im.pack()
for name in ['FIN_concrete','FIN_granite','FIN_ramp','FIN_stone_pale']:
 im=bpy.data.images.get('V2_'+name)
 if im:
  n=im.size[0];rgba=np.ones((n,n,4),np.float32);base=bpy.data.materials[name].diffuse_color
  for k in range(3):rgba[:,:,k]=np.clip(base[k]+rng.normal(0,.006,(n,n)),.01,.9)
  im.pixels.foreach_set(rgba.ravel());im.save();im.pack()
s=bpy.context.scene;s.cycles.samples=20
bpy.ops.wm.save_as_mainfile(filepath=str(O/'vegetation-v2.blend'))
for name,cam in [('overall','FINAL landscape'),('east','SHAPE exit approximate'),('west','03-west-garden'),('lawn','05-north-photo-4474')]:
 s.camera=bpy.data.objects[cam];s.render.filepath=str(O/('after-'+name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT')
for ob in s.objects:
 if ob.type=='MESH' and not ob.hide_render:ob.hide_set(False);ob.select_set(True)
export_visible_glb(filepath=str(O/'vegetation-v2.glb'))
print('TEXTURES_REPAIRED')
