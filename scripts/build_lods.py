"""Build reproducible three-tier runtime assets from canonical modular GLBs.
Run: blender -b --python scripts/build_lods.py
"""
import bpy, json, hashlib, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'web/public'

def build_lods(only=None):
    source=json.loads((PUBLIC/'campus-manifest.json').read_text())
    output=PUBLIC/'campus-lod.json'
    result=json.loads(output.read_text()) if only and output.exists() else {'version':1,'assets':[]}
    for category in ['shared','buildings']:
        for asset in source[category]:
            key=category+'-'+asset['id']
            if only and key!=only:continue
            bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
            bpy.ops.import_scene.gltf(filepath=str(PUBLIC/asset['url']))
            meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
            corners=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
            lo=[min(v[i] for v in corners) for i in range(3)];hi=[max(v[i] for v in corners) for i in range(3)]
            position=asset.get('position',[0,0,0])
            bounds={'min':[lo[0]+position[0],lo[2]+position[1],-hi[1]+position[2]],'max':[hi[0]+position[0],hi[2]+position[1],-lo[1]+position[2]]}
            tiers=[]
            # Original meshes stay intact; modifiers are evaluated on export.
            for level,ratio in [('far',.025),('medium',.10),('near',1.)]:
                for obj in meshes:
                    obj.modifiers.clear()
                    if ratio<1 and len(obj.data.polygons)>24:
                        mod=obj.modifiers.new('Runtime LOD','DECIMATE');mod.ratio=ratio
                path=PUBLIC/asset['url'] if level=='near' else PUBLIC/f'models/lod/{key}-{level}.glb'
                path.parent.mkdir(exist_ok=True,parents=True)
                if level!='near':
                    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_apply=True,export_extras=True,export_cameras=False,export_lights=False)
                data=path.read_bytes()
                import struct
                n=struct.unpack_from('<I',data,12)[0];gltf=json.loads(data[20:20+n])
                triangles=sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf.get('meshes',[]) for p in m['primitives'] if 'indices' in p)
                tiers.append({'url':str(path.relative_to(PUBLIC)),'revision':hashlib.sha256(data).hexdigest()[:12],'bytes':len(data),'triangles':triangles})
            result['assets']=[a for a in result['assets'] if a['id']!=key]
            result['assets'].append({'id':key,'name':asset['name'],'sourceRevision':asset['revision'],'position':position,'rotation':asset.get('rotation',[0,0,0]),'bounds':bounds,'nearDistance':0 if key=='shared-00' else 35 if asset['id']=='58' else 100,'mediumDistance':0 if key=='shared-00' else 140 if asset['id']=='58' else 340,'tiers':tiers})
            print('LOD_ASSET',key,[(t['bytes'],t['triangles']) for t in tiers],flush=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('LOD_COMPLETE',len(result['assets']),sum(a['tiers'][0]['bytes'] for a in result['assets']),flush=True)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    build_lods(args[0] if args else None)
