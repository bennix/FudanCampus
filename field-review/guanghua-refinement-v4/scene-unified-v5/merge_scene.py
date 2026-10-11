"""Apply three conflict-free branch deltas without overwriting any source."""
import bpy,sys,json
from pathlib import Path
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O))
from scene_fingerprints import sha,snapshot,write,material_signature
A=json.loads((O/'source-audit.json').read_text(encoding='utf-8'))
ST=json.loads((O/'source-snapshots.json').read_text(encoding='utf-8'))
OUT=O/'guanghua-unified-v5.blend'
assert not OUT.exists(),'Never overwrite an existing unified checkpoint'
assert all(not v for v in A['object_conflicts'].values()),A['object_conflicts']
for x in A['sources'].values():assert sha(x['path'])==x['sha256'],x['path']
expected=dict(ST['base'])
owners={n:'base' for n in expected}
for branch,d in A['diff'].items():
    for name in d['deleted']:expected.pop(name);owners.pop(name)
    for name in list(d['changed'])+d['added']:expected[name]=ST[branch][name];owners[name]=branch
bpy.ops.wm.open_mainfile(filepath=A['sources']['garden']['path'])
S=bpy.context.scene
for branch in ['planters','path']:
    delta=A['diff'][branch]
    names=sorted(set(delta['changed'])|set(delta['added']))
    collections={}
    for name in names+delta['deleted']:
        old=bpy.data.objects.get(name)
        if old:
            collections[name]=[c.name for c in old.users_collection]
            bpy.data.objects.remove(old,do_unlink=True)
    with bpy.data.libraries.load(A['sources'][branch]['path'],link=False) as (src,dst):
        assert set(names)<=set(src.objects)
        dst.objects=list(names)
    for ob in dst.objects:
        assert ob and ob.name in names,(ob.name if ob else None,names)
        targets=collections.get(ob.name,[])
        if branch=='path' and ob.get('feature_id')=='E_WALK':targets=['11_A east straight path']
        if not targets:targets=['Unified imported '+branch]
        for cname in targets:
            c=bpy.data.collections.get(cname)
            if not c:c=bpy.data.collections.new(cname);S.collection.children.link(c)
            if ob.name not in c.objects:c.objects.link(ob)
        ob.hide_render=expected[ob.name]['hide_render'];ob.hide_viewport=expected[ob.name]['hide_viewport'];ob.hide_set(expected[ob.name]['hide_set'])
    # Keep source review cameras in the same editable checkpoint.
    prefix='P5 ' if branch=='planters' else 'A '
    with bpy.data.libraries.load(A['sources'][branch]['path'],link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n.startswith(prefix) and n not in bpy.data.objects]
    review=bpy.data.collections.get('Unified review cameras')
    if not review:review=bpy.data.collections.new('Unified review cameras');S.collection.children.link(review)
    for ob in dst.objects:
        if ob and ob.type=='CAMERA':review.objects.link(ob)
    print('MERGED_BRANCH',branch,len(names),len(delta['deleted']),flush=True)

# Resolve appended duplicates by full shader/image signature, not by the datablock name.
canonical={};cache={}
for ob in S.objects:
    if ob.type!='MESH':continue
    for i,m in enumerate(ob.data.materials):
        if not m:continue
        if m.as_pointer() not in cache:cache[m.as_pointer()]=material_signature(m)
        sig=cache[m.as_pointer()]
        if sig in canonical and canonical[sig]!=m:ob.data.materials[i]=canonical[sig]
        else:canonical[sig]=m
actual=snapshot()
errors={n:[k for k in expected[n] if expected[n][k]!=actual.get(n,{}).get(k)] for n in expected if actual.get(n)!=expected[n]}
extras=sorted(actual.keys()-expected.keys())
write(O/'merge-check.json',{'mismatches':errors,'extras':extras,'details':{n:{k:{'expected':expected[n][k],'actual':actual[n][k]} for k in ks} for n,ks in errors.items()}})
assert not errors and not extras,(errors,extras)
S['active_checkpoint']='Guanghua unified v5: forecourt v4 + garden vegetation v3 + entry materials v5 + east straight path A v1'
S['unified_version']='guanghua-unified-v5'
S['unified_source_manifest']='version-manifest.json'
S['unified_base_sha256']=A['sources']['base']['sha256']
S['unified_branch_sources']=json.dumps(A['sources'],ensure_ascii=False)
S['A_groove_depth_and_function']='推定；0.018 场景单位；用途未确认'
S['A_reference_photos']=[4492,4493]
S.camera=bpy.data.objects['FINAL landscape']
S.render.engine='CYCLES';S.cycles.samples=40;S.cycles.use_denoising=True;S.cycles.device='CPU'
S.render.resolution_x=1800;S.render.resolution_y=1350;S.render.resolution_percentage=100
S.view_settings.view_transform='AgX';S.view_settings.exposure=.65
S.render.filepath=str(O/'overall.png')
bpy.ops.file.pack_all()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
write(O/'expected-unified-snapshot.json',expected)
write(O/'version-manifest.json',{
 'version':'guanghua-unified-v5','date':'2026-09-30','status':'merged; reopen validation pending',
 'scene':str(OUT),'scene_sha256':sha(OUT),'sources':A['sources'],
 'merge_method':'Three-way object deltas against the same v4 ancestor; start from complete garden checkpoint; import only planters/path deltas',
 'conflicts':A['object_conflicts'],
 'branch_counts':{k:{'added':len(d['added']),'deleted':len(d['deleted']),'changed':len(d['changed'])} for k,d in A['diff'].items()},
 'mesh_objects':len(actual),'object_owners':owners,'render_policy':'All new overall/review renders must reopen this exact scene and record its SHA-256',
 'web_assets_updated':False,
 'limits':['合并既有成果，不新增现场测量认证','树位、尺度、槽深和用途继承各分支的推定标记','校验限定内容保持与指定通道交界，不是全场景碰撞认证']})
print('UNIFIED_SAVED',len(actual),sha(OUT),flush=True)
