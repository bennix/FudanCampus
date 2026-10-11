import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(BASE))
top=camera('V4 ENTRY overhead',(20,105,160),(20,105,0),153)
photo=camera('V4 approximate photo4464',(-42,88.5,2.2),(-48,111,2.8),lens=27)
render('stage01-before-top.png',top,True,width=1000,samples=12,ratio=.42)
render('stage01-before-4464.png',photo,width=1000,samples=12)
bpy.ops.wm.open_mainfile(filepath=str(O/'stage01-building-entry.blend'));before=all_digests()
photo=camera('V4 approximate photo4464',(-42,88.5,2.2),(-48,111,2.8),lens=27)
assert before==all_digests()
bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage01-building-entry.blend'))
render('stage01-after-4464.png',photo,width=1400,samples=24)
print('STAGE01_COMPARISON_REFRESHED',flush=True)
