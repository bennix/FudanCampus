"""Read-only manual-pick scale audit for the user's 25m Gaode screenshot."""
from pathlib import Path
import ast,hashlib,json,math,shutil
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'assets/比例尺-来源高德地图.jpeg'
OUT=ROOT/'field-review/gaode-scale-2026-11-15';OUT.mkdir(exist_ok=True)
im=Image.open(SOURCE)
assert im.size==(1080,1870),'Coordinate picks apply only to the recorded original resolution'
# Original raster coordinates: left-top origin, x right, y down. End caps' centres.
bar=((216,1253),(385,1253));building=((148,820),(850,820))
bar_px=math.dist(*bar);width_px=math.dist(*building)
metres_per_pixel=25/bar_px
width_m=width_px*metres_per_pixel
model_source=ROOT/'scripts/chemistry_geometry.py'
footprint=next(ast.literal_eval(node.value) for node in ast.parse(model_source.read_text(encoding='utf-8')).body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='FOOTPRINT' for target in node.targets))
model_width=max(p[0] for p in footprint)-min(p[0] for p in footprint)
assert abs(model_width-65.6)<1e-8
# Manual reading sensitivity only: +-1px per bar endpoint, +-2px per wall endpoint.
lower=25*(width_px-4)/(bar_px+2);upper=25*(width_px+4)/(bar_px-2)
report={'date':'2026-11-15','source':SOURCE.relative_to(ROOT.parent).as_posix(),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'image_size':list(im.size),'provider':'高德地图，用户确认','capture_date':'未知；文件接收/分析日期不作为截图日期','map_view':'平面轮廓视图，未见明显楼体立面透视；地图姿态未取得设备元数据验证',
 'pixel_origin':'左上，x向右、y向下；人工原图取点，不使用缩略图像素',
 'scale_bar':{'points':bar,'pixels':bar_px,'metres':25,'selection':'25米横向标尺两端端帽中心'},
 'building_55':{'points':building,'pixels':width_px,'selection':'同一水平行上左右侧翼主体外轮廓，不含道路、树冠、图标或阴影','axis':'图面左右主轴，对应模型本地X；不假定精确地理东西轴'},
 'metres_per_pixel':metres_per_pixel,'estimated_width_m':width_m,'model_wall_width_units':model_width,'reference_metres_per_model_unit':width_m/model_width,
 'model_source':model_source.relative_to(ROOT).as_posix(),'model_source_sha256':hashlib.sha256(model_source.read_bytes()).hexdigest(),
 'map_width_to_model_width_ratio_under_original_1m_convention':width_m/model_width,
 'model_width_shortfall_percent_relative_to_map_under_original_1m_convention':(1-model_width/width_m)*100,
 'endpoint_sensitivity':{'bar_endpoint_px':1,'wall_endpoint_px':2,'estimated_width_m_range':[lower,upper],'reference_metres_per_unit_range':[lower/model_width,upper/model_width],'meaning':'仅像素端点读取敏感性；不是统计置信区间，不包括地图轮廓概化或未知视角误差'},
 'scope':'采用为化学楼横向平面地图估算锚点；非现场测距，不自动标定楼高、四教或全校园；模型/manifest/碰撞未修改'}
(OUT/'scale-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(SOURCE,OUT/'reference-gaode-25m.jpeg')
plt.rcParams['font.sans-serif']=['Microsoft YaHei','SimHei'];plt.rcParams['axes.unicode_minus']=False
fig,axes=plt.subplots(1,2,figsize=(12,6),layout='constrained',gridspec_kw={'width_ratios':[1,2.6]})
for ax,box,points,title in [
 (axes[0],(195,1195,405,1275),bar,'高德图同幅比例尺：25米'),
 (axes[1],(120,465,885,925),building,'化学楼主体：图面横向外轮廓')]:
 x0,y0,x1,y1=box;ax.imshow(im.crop(box),extent=(x0,x1,y1,y0));ax.plot([p[0] for p in points],[p[1] for p in points],'o-',color='#c52629',linewidth=2,markersize=4);ax.set_title(title,fontsize=11);ax.set_xlabel('原图x像素');ax.set_ylabel('原图y像素')
fig.suptitle(f'25m / {bar_px:.0f}px × {width_px:.0f}px ≈ {width_m:.1f}m；{width_m:.1f}m / 65.6模型单位 ≈ {width_m/model_width:.3f}m/单位',fontsize=12)
fig.savefig(OUT/'scale-audit.png',dpi=180);plt.close(fig)
print(json.dumps(report,ensure_ascii=False,indent=2))
