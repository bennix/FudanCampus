"""Relative hard-anchor fit; it is not survey calibration or facade certification."""
import numpy as np,json,math
from pathlib import Path
O=Path(__file__).resolve().parent
position=np.array([-51.,82.,1.8])
world=np.array([[-53.6,99.52,.915],[-46.,99.45,.915],[-53.6,99.52,.035],[-46.,99.45,.035]])
target=np.array([[367/1824,551/1368],[1190/1824,555/1368],[367/1824,611/1368],[1190/1824,630/1368]])
def project(a):
 yaw,pitch,roll,lens=a;f=np.array([math.sin(yaw)*math.cos(pitch),math.cos(yaw)*math.cos(pitch),math.sin(pitch)])
 r=np.array([math.cos(yaw),-math.sin(yaw),0]);u=np.cross(r,f);rr=r*math.cos(roll)+u*math.sin(roll);uu=u*math.cos(roll)-r*math.sin(roll);q=world-position;d=q@f
 return np.column_stack([.5+(q@rr)/d*lens/36,.5-(q@uu)/d*lens/36*4/3])
a=np.array([.14,-.10,0.,40.])
for _ in range(60):
 p=project(a);r=(p-target).ravel();jac=np.column_stack([((project(a+np.eye(4)[i]*1e-5)-p)/1e-5).ravel() for i in range(4)])
 delta=np.linalg.lstsq(jac,r,rcond=None)[0];a-=delta*.5
 a[3]=np.clip(a[3],18,100)
 if np.linalg.norm(delta)<1e-8:break
f=np.array([math.sin(a[0])*math.cos(a[1]),math.cos(a[0])*math.cos(a[1]),math.sin(a[1])])
result={'P5 approximate IMG_4464':dict(location=position.tolist(),target=(position+f*28).tolist(),lens=float(a[3]),roll=float(a[2]),primary_photo=4464,
 anchors=[dict(world=w.tolist(),photo_normalized=t.tolist(),model_normalized=p.tolist()) for w,t,p in zip(world,target,project(a))],
 maximum_anchor_axis_error=float(np.abs(project(a)-target).max()),confidence='Relative fit to four approximate visible plinth anchors; pose/scale inferred. Other facade anchors not certified.')}
result['GV3 west platform photo 4390']=dict(location=[-69.5,46,2.85],target=[-69.5,67,2.3],lens=26,roll=0,primary_photo=4390,confidence='Manual hardscape orientation: glass island on the right, north-facing view within the terrace. Camera position inferred; no metric correspondence claim.')
(O/'camera-overrides.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result)
