import bpy,json
from pathlib import Path
R=Path.cwd();O=R/'field-review/guanghua-refinement-v4/vegetation-v2'
bpy.ops.wm.open_mainfile(filepath=str(O.parent/'vegetation-v1/vegetation-v1.blend'))
rows=[]
for m in bpy.data.materials:
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m.use_nodes else None
 if m.users:rows.append(dict(name=m.name,users=m.users,diffuse=list(m.diffuse_color),base=list(p.inputs['Base Color'].default_value) if p else None,linked=p.inputs['Base Color'].is_linked if p else False,images=[n.image.name if n.image else None for n in m.node_tree.nodes if n.type=='TEX_IMAGE'] if m.use_nodes else []))
(O/'material-inventory.json').write_text(json.dumps(rows,indent=2))
print('MATERIALS',len(rows));print('CAMERAS',[o.name for o in bpy.data.objects if o.type=='CAMERA'])
