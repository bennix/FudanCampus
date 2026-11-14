"""Audit a cartographic scale without editing campus models. Pixel picks are explicit/manual."""
from pathlib import Path
import hashlib,json,math
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'field-review/map-scale-2026-11-14';OUT.mkdir(exist_ok=True)
source=ROOT/'web/public/campus-map.png'
im=Image.open(source)
# Manual picks on the original 3508x2480 raster; x right, y down, origin upper left.
# Scale bar's entire black/white span is 0--200 m; do not measure only a black segment.
bar=((2089,849),(2511,849));building=((1828,1380),(1920,1380))
ticks=[{'metres':m,'pixel_x':x} for m,x in [(0,2089),(10,2106),(50,2173),(100,2258),(200,2511)]]
bar_px=math.dist(*bar);width_px=math.dist(*building);metres_per_pixel=200/bar_px
length=width_px*metres_per_pixel;model_width=40.8
# +-2px per endpoint => conservative +-4px on each span. Not a survey confidence interval.
low=200*(width_px-4)/(bar_px+4);high=200*(width_px+4)/(bar_px-4)
report={'source':source.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'image_size':list(im.size),'source_type':'既有Fudan校园导览图，不是本轮高德截图；原发布方/年份未核实',
 'coordinate_convention':'原图像素，左上原点，x向右，y向下','selection':'人工读取示意线外缘，非自动地物分割',
 'scale_bar':{'points':bar,'pixels':bar_px,'metres':200},'building_17':{'points':building,'pixels':width_px,'direction':'图面左右的楼体主轴，对应模型本地X；不是精确地理东西轴'},
 'metres_per_pixel':metres_per_pixel,'map_estimated_width_m':length,'model_wall_width_units':model_width,
 'reference_metres_per_model_unit':length/model_width,'model_vs_map_relative_difference_percent':100*(model_width-length)/length,
 'pixel_reading_sensitivity':{'endpoint_error_px':2,'span_error_px':4,'width_m_range':[low,high],'meaning':'仅像素端点误差敏感性，不包括地图概化/形变；不是统计置信区间'},
 'status':'地图比例尺估算与模型尺度交叉校核，非实地测量；不改变现有1unit约1m工程约定，不统一缩放全校园'}
first100=2258-2089;alternative=100/first100*width_px
report['scale_bar']['ticks']=ticks
report['scale_consistency']={'first_100m_pixels':first100,'full_200m_pixels':bar_px,'ratio_full_to_first100':bar_px/first100,'expected_ratio':2,'consistent':False,'first100_metres_per_pixel':100/first100,'first100_estimated_width_m':alternative,'first100_metres_per_model_unit':alternative/model_width,'finding':'比例尺各段不自洽，不能选择单一绝对尺度作为有效校准；保留两种条件计算展示问题。'}
report['status']='不采纳为有效绝对尺度校准：导览比例尺内部不一致，43.6m/54.4m仅为两种条件读数；需要高德测距或可靠带比例尺截图校核；未修改模型'
report['conditional_full200m']={key:report.pop(key) for key in ['metres_per_pixel','map_estimated_width_m','reference_metres_per_model_unit','model_vs_map_relative_difference_percent']}
(OUT/'scale-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
plt.rcParams['font.sans-serif']=['Microsoft YaHei','SimHei'];plt.rcParams['axes.unicode_minus']=False
fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
for ax,box,points,title in [
 (axes[0],(2040,790,2560,900),bar,'校园导览图：整段 0—200 米比例尺'),
 (axes[1],(1760,1290,1950,1440),building,'17号楼：图面左右主体边界')]:
 x0,y0,x1,y1=box;ax.imshow(im.crop(box),extent=(x0,x1,y1,y0));ax.plot([p[0] for p in points],[p[1] for p in points],'o-',color='#c52629',linewidth=2,markersize=5);ax.set_title(title,fontsize=11);ax.set_xlabel('原图x像素');ax.set_ylabel('原图y像素')
axes[0].scatter([t['pixel_x'] for t in ticks],[849]*len(ticks),color='#c52629',s=18)
fig.suptitle(f'比例尺不自洽：0—100m={first100}px，0—200m={bar_px:.0f}px；四教条件读数 {alternative:.1f}m / {length:.1f}m',fontsize=12)
fig.savefig(OUT/'scale-audit.png',dpi=180);plt.close(fig)
print(json.dumps(report,ensure_ascii=False,indent=2))
