"""Content fingerprints for a three-way Blender scene merge, independent of datablock suffixes."""
import bpy, numpy as np, hashlib, json

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def plain(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    if hasattr(v,'to_dict'):return {k:plain(x) for k,x in v.to_dict().items()}
    if hasattr(v,'to_list'):return plain(v.to_list())
    try:return [plain(x) for x in v]
    except TypeError:return str(v)

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def props(ob):return {k:plain(v) for k,v in ob.items() if k!='_RNA_UI'}

def rna_values(ob,exclude=()):
    result={}
    for p in ob.bl_rna.properties:
        if p.identifier in exclude or p.identifier=='rna_type' or p.type not in {'BOOLEAN','INT','FLOAT','STRING','ENUM'}:continue
        try:result[p.identifier]=plain(getattr(ob,p.identifier))
        except (AttributeError,TypeError):pass
    return result

def material_signature(m,image_cache=None):
    if m is None:return None
    image_cache={} if image_cache is None else image_cache
    nt=m.node_tree
    nodes=[]
    if nt:
        for n in nt.nodes:
            data={'id':n.name,'type':n.bl_idname,'settings':rna_values(n,('name','label','location','width','height','dimensions','select','show_options','show_preview','show_texture','hide','color','use_custom_color','is_active_output','bl_description','bl_label','bl_icon','bl_static_type','bl_width_default','bl_width_min','bl_width_max','bl_height_default','bl_height_min','bl_height_max')),
                  'inputs':[(s.identifier,plain(s.default_value)) for s in n.inputs if hasattr(s,'default_value')]}
            if hasattr(n,'color_ramp'):
                r=n.color_ramp;data['ramp']=[r.interpolation,r.color_mode,r.hue_interpolation,[(e.position,plain(e.color)) for e in r.elements]]
            if hasattr(n,'image') and n.image:
                im=n.image;key=im.as_pointer()
                if key not in image_cache:
                    if im.packed_file:h=hashlib.sha256(im.packed_file.data).hexdigest()
                    else:
                        a=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(a);h=hashlib.sha256(a.tobytes()).hexdigest()
                    image_cache[key]=[h,list(im.size),im.colorspace_settings.name,im.alpha_mode]
                data['image']=image_cache[key]
            nodes.append(data)
    return digest({'material':rna_values(m,('name','name_full','is_updated','is_updated_data','is_evaluated','users','use_fake_user','is_embedded_data','is_library_indirect','is_missing','is_editable','session_uid','preview_render_type','show_transparent_back')),
                   'nodes':sorted(nodes,key=lambda n:n['id']),
                   'links':sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in nt.links) if nt else []})

def snapshot():
    bpy.context.view_layer.update()
    image_cache={}; mats={m.as_pointer():material_signature(m,image_cache) for m in bpy.data.materials}
    mesh_cache={}; out={}
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        me=ob.data;k=me.as_pointer()
        if k not in mesh_cache:
            geometry=hashlib.sha256();surface=hashlib.sha256()
            for group,prop,count,typ in [(me.vertices,'co',3,np.float32),(me.edges,'vertices',2,np.int32),(me.loops,'vertex_index',1,np.int32),(me.polygons,'loop_start',1,np.int32),(me.polygons,'loop_total',1,np.int32)]:
                a=np.empty(len(group)*count,typ);group.foreach_get(prop,a);geometry.update(a.tobytes())
            for prop,typ in [('material_index',np.int32),('use_smooth',np.bool_)]:
                a=np.empty(len(me.polygons),typ);me.polygons.foreach_get(prop,a);surface.update(a.tobytes())
            for uv in me.uv_layers:
                a=np.empty(len(uv.data)*2,np.float32);uv.data.foreach_get('uv',a);surface.update(uv.name.encode());surface.update(a.tobytes())
            mesh_cache[k]=[geometry.hexdigest(),surface.hexdigest(),len(me.vertices),len(me.polygons)]
        out[ob.name]={'geometry':mesh_cache[k][0],'surface':mesh_cache[k][1], 'vertices':mesh_cache[k][2],'faces':mesh_cache[k][3],
                     'matrix':plain(ob.matrix_world),'materials':[mats.get(m.as_pointer()) if m else None for m in me.materials],
                     # Appending a datablock changes its library-override status, not its geometry.
                     'modifiers':[{'type':m.type,'values':rna_values(m,('execution_time','is_override_data'))} for m in ob.modifiers],
                     'hide_render':ob.hide_render,'hide_viewport':ob.hide_viewport,'hide_set':ob.hide_get(),
                     'properties':props(ob)}
    return out

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
