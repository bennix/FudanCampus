"""Remove the old 17 shell and its spatially isolated batched details.

Preserve all source vertices/materials and every non-target index byte. Original
shared/02.glb remains untouched; the manifest points to a derived resource.
"""
import json, struct, hashlib
from pathlib import Path
from strip_modular_from_shared import read_glb, write_glb
ROOT=Path(__file__).resolve().parents[1];public=ROOT/'web/public'
g,raw=read_glb(public/'models/shared/02.glb');binary=bytearray(raw)
def values(ai):
    a=g['accessors'][ai];v=g['bufferViews'][a['bufferView']];fmt={5123:'H',5125:'I',5126:'f'}[a['componentType']];size=struct.calcsize(fmt)
    width={'SCALAR':1,'VEC3':3}[a['type']];start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',width*size)
    return [struct.unpack_from('<'+fmt*width,binary,start+i*stride) for i in range(a['count'])]
def inside(p):return -175.3<=p[0]<=-133.5 and -.05<=p[1]<=13.1 and -211.3<=p[2]<=-195.7
drop={i for i,n in enumerate(g['nodes']) if str(n.get('extras',{}).get('building_id'))=='17'}
assert len(drop)==1,'Expected exactly one old building 17'
removed=0
for n in g['nodes']:
    if n.get('extras',{}).get('building_id') is not None or 'mesh' not in n:continue
    for p in g['meshes'][n['mesh']]['primitives']:
        positions=values(p['attributes']['POSITION']);indices=[v[0] for v in values(p['indices'])];kept=[]
        for i in range(0,len(indices),3):
            tri=indices[i:i+3]
            if all(inside(positions[j]) for j in tri):removed+=1
            else:kept.extend(tri)
        if len(kept)==len(indices):continue
        assert kept
        while len(binary)%4:binary.append(0)
        offset=len(binary);binary.extend(struct.pack('<'+'I'*len(kept),*kept))
        vi=len(g['bufferViews']);g['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=len(kept)*4,target=34963))
        ai=len(g['accessors']);g['accessors'].append(dict(bufferView=vi,componentType=5125,count=len(kept),type='SCALAR',min=[min(kept)],max=[max(kept)]));p['indices']=ai
assert removed>300,(removed,'Old details were not removed')
mapping={old:new for new,old in enumerate(i for i in range(len(g['nodes'])) if i not in drop)}
g['nodes']=[n for i,n in enumerate(g['nodes']) if i not in drop]
for n in g['nodes']:
    if 'children' in n:n['children']=[mapping[i] for i in n['children'] if i not in drop]
for s in g['scenes']:s['nodes']=[mapping[i] for i in s['nodes'] if i not in drop]
g['buffers'][0]['byteLength']=len(binary)
target=public/'models/shared/02-teaching4.glb';payload=write_glb(target,g,bytes(binary))
m=json.loads((public/'campus-manifest.json').read_text())
for a in m['shared']:
    if a['id']=='02':a.update(url='models/shared/02-teaching4.glb',bytes=len(payload),revision=hashlib.sha256(payload).hexdigest()[:12])
(public/'campus-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print('TEACHING4_INTEGRATED: old shell +',removed,'detail triangles removed; source binary preserved')
