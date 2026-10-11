"""Export visible meshes and evaluated lettering without changing editable fonts."""
import bpy


def export_visible_glb(filepath, **options):
    scene = bpy.context.scene
    view_layer = bpy.context.view_layer
    view_layer.update()
    # selected_objects omits hidden selections. Preserve the stored per-object
    # state so an export cannot change the editable scene, even on failure.
    original_state = [(obj, obj.hide_get(view_layer=view_layer),
                       obj.select_get(view_layer=view_layer))
                      for obj in view_layer.objects]
    active = view_layer.objects.active
    copies = []
    records = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    try:
        for obj in list(scene.objects):
            if obj.type != 'FONT' or obj.hide_render:
                continue
            name = obj.name
            mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
            # Register resources immediately, before any operation that may fail.
            temporary = [obj, None, mesh, name]
            copies.append(temporary)
            if not mesh.vertices or not mesh.polygons:
                raise ValueError('Empty lettering: ' + name)
            record = dict(name=name, body=obj.data.body, font=obj.data.font.filepath,
                          feature_id=obj.get('feature_id'), vertices=len(mesh.vertices),
                          polygons=len(mesh.polygons), matrix=[list(row) for row in obj.matrix_world])
            obj.name = name + '__editable_export_source'
            copy = bpy.data.objects.new(name, mesh)
            temporary[1] = copy
            scene.collection.objects.link(copy)
            copy.matrix_world = obj.matrix_world.copy()
            for key in obj.keys():
                copy[key] = obj[key]
            records.append(record)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in scene.objects:
            if obj.type == 'MESH' and not obj.hide_render:
                obj.hide_set(False)
                obj.select_set(True)
        view_layer.update()
        bpy.ops.export_scene.gltf(filepath=str(filepath), export_format='GLB',
                                  use_selection=True, export_extras=True, **options)
        return records
    finally:
        try:
            for original, copy, mesh, name in copies:
                if copy is not None:
                    bpy.data.objects.remove(copy, do_unlink=True)
                bpy.data.meshes.remove(mesh)
                original.name = name
        finally:
            # Direct object methods also restore selections on hidden objects.
            # Restore visibility first because hiding may clear selection.
            for obj, hidden, _selected in original_state:
                obj.hide_set(hidden, view_layer=view_layer)
            for obj, _hidden, selected in original_state:
                obj.select_set(selected, view_layer=view_layer)
            view_layer.objects.active = active
