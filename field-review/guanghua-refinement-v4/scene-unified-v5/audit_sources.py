"""Read-only audit of the common ancestor and completed scene branches."""
import bpy,sys,json
from pathlib import Path
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O))
from scene_fingerprints import sha,snapshot,write
SOURCES={
 'base':O.parent/'forecourt-refinement-v4/forecourt-refined-v4.blend',
 'garden':O.parent/'garden-vegetation-v3/garden-vegetation-v3.blend',
 'planters':O.parent/'entry-planters-v5/entry-planters-review-v5.blend',
 'path':O.parent/'straight-path-a-v1/east-straight-path-a-v1.blend'}
states={};sources={}
for key,path in SOURCES.items():
    h=sha(path);bpy.ops.wm.open_mainfile(filepath=str(path));states[key]=snapshot()
    sources[key]={'path':str(path),'sha256':h,'mesh_objects':len(states[key])}
    print('SNAPSHOT',key,len(states[key]),flush=True)
base=states['base'];diff={}
for key in ['garden','planters','path']:
    b=states[key];diff[key]={'added':sorted(b.keys()-base.keys()),'deleted':sorted(base.keys()-b.keys()),
         'changed':{n:[k for k in base[n] if base[n][k]!=b[n][k]] for n in sorted(base.keys()&b.keys()) if base[n]!=b[n]}}
sets={k:set(d['added'])|set(d['deleted'])|set(d['changed']) for k,d in diff.items()}
conflicts={a+' + '+b:sorted(sets[a]&sets[b]) for a,b in [('garden','planters'),('garden','path'),('planters','path')]}
write(O/'source-snapshots.json',states)
write(O/'source-audit.json',{'sources':sources,'diff':diff,'object_conflicts':conflicts})
print('AUDIT_SUMMARY',json.dumps({'sources':sources,'diff':{k:{'added':len(d['added']),'deleted':len(d['deleted']),'changed':d['changed']} for k,d in diff.items()},'conflicts':conflicts},ensure_ascii=False),flush=True)
