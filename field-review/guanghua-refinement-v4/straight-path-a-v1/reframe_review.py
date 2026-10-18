import sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build as B
bpy.ops.wm.open_mainfile(filepath=str(B.OUT))
camera=B.cams()
bpy.context.scene.camera=camera['4492']
bpy.ops.wm.save_as_mainfile(filepath=str(B.OUT))
B.render('after-top.png',camera['top'],width=1800,samples=28,top=True)
B.section()
print('REVIEW_FRAMING_OK',flush=True)
