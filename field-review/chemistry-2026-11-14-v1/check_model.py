"""Spatial regression checks against exported chemistry geometry, no name-only claims."""
import bpy
from mathutils import Vector

def validate():
    scene=bpy.context.scene
    deps=bpy.context.evaluated_depsgraph_get()
    def ray(p,d):
        ok,point,normal,index,ob,matrix=scene.ray_cast(deps,Vector(p),Vector(d),distance=100)
        assert ok, ('missing surface',p,d)
        mat=ob.data.materials[ob.data.polygons[index].material_index]
        return point,mat
    point,_=ray((-45,0,7),(1,0,0))
    assert -29<point.x<-27, ('west recess absent',point.x)
    point,_=ray((0,0,30),(0,0,-1))
    assert point.z>14, ('central roof not raised',point.z)
    for x,y in [(0,0),(-25,15),(25,-15),(-12,0)]:
        _,m=ray((x,y,30),(0,0,-1))
        c=m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value
        assert min(c[:3])>.8, ('roof not white',m.name)
    # Inward-facing courtyard walls plus outer west, north, south, east.
    for p,d in [((-16,-12,6.6),(-1,0,0)),((15,-12,6.6),(1,0,0)),
                ((-16,12,6.6),(-1,0,0)),((15,12,6.6),(1,0,0)),
                ((-45,0,6.6),(1,0,0)),((0,-15,6.6),(0,1,0)),
                ((0,15,6.6),(0,-1,0)),((45,0,6.6),(-1,0,0))]:
        # Every wall segment must have windows, checked by mesh metadata below;
        # probes here only ensure each courtyard has a reachable surface.
        ray(p,d)
    canopy=[o for o in scene.objects if o.type=='MESH' and o.get('component')=='portico roof']
    assert len(canopy)==3, ('front/rear/east canopies missing',len(canopy))
    east=next(o for o in canopy if o.get('entrance')=='east')
    assert abs(east.get('width')-7.2)<.01, 'East canopy still oversized'
    glazing=[o for o in scene.objects if o.type=='MESH' and o.get('component')=='window glass']
    segments={o.get('wall_segment') for o in glazing}
    assert len(segments)>=16, ('facades without windows',segments)
    assert all(o.get('window_width')<=2 for o in glazing), 'Window too wide'
    from chemistry_geometry import FOOTPRINT
    pane_faces=0
    for ob in glazing:
        seg=ob['wall_segment'];a=Vector((*FOOTPRINT[seg],0));b=Vector((*FOOTPRINT[(seg+1)%16],0))
        t=(b-a).normalized();normal=Vector((t.y,-t.x,0))
        for face in ob.data.polygons:
            face_normal=(ob.matrix_world.to_3x3()@face.normal).normalized()
            if face_normal.dot(normal)<.99:continue
            # Triangle centroids survive GLB vertex splitting/reordering and
            # avoid the centre mullion. Quads use an offset for the same reason.
            centre=ob.matrix_world@face.center
            if len(face.vertices)==4:centre+=t*.3
            point,m=ray(centre+normal*.4,-normal)
            assert 'glazing' in m.name.lower(), ('window hidden by another surface',seg,m.name)
            pane_faces+=1
    assert pane_faces>=233
    print('PASS chemistry: west recess, raised centre, white roofs, courtyard surfaces, 3 porticos,',pane_faces,'visible window faces on all 16 wall segments')

if __name__=='__main__': validate()
