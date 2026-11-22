"""Photo-informed planting in the same map frame as the buildings.

Positions and dimensions are estimates, not surveyed tree coordinates.
Entrance planting follows the user's latest close-up photos.
"""
import json
import math
import random
import bpy
from mathutils import Vector


def build_perimeter(xy, material, parts, routes, inside, output):
    rng = random.Random(23307130130)
    bark = material('周边树干褐灰', (.24, .19, .125))
    pale = material('周边树干基部白灰', (.68, .69, .61))
    colors = [(.045, .115, .025), (.085, .19, .035),
              (.16, .26, .055), (.26, .29, .085)]
    foliage = [material('周边Tree叶片' + str(i), c) for i, c in enumerate(colors)]
    buffers = {}
    polygons = [(poly, height) for blocks in parts.values() for _, poly, height in blocks]

    def blocked(p):
        pixel = (p.x / .48 + 176, 107 - p.y / .48)
        return any(p.z < height + .7 and inside(pixel, poly) for poly, height in polygons)

    def add(mat, vertices, faces):
        if any(blocked(v) for v in vertices):
            return
        vs, fs = buffers.setdefault(mat.name, ([], []))
        offset = len(vs)
        vs.extend(tuple(v) for v in vertices)
        fs.extend(tuple(offset + i for i in f) for f in faces)

    def branch(a, b, r1, r2, mat=bark):
        direction = (b-a).normalized()
        u = direction.cross(Vector((0, 1, 0))).normalized()
        v = direction.cross(u)
        vertices = [p + (u*math.cos(i*math.tau/7) + v*math.sin(i*math.tau/7))*r
                    for p, r in [(a, r1), (b, r2)] for i in range(7)]
        add(mat, vertices, [(i, (i+1)%7, (i+1)%7+7, i+7) for i in range(7)])

    def leaf(p, size=.14, width=.48):
        angle = rng.random()*math.tau
        u = Vector((math.cos(angle), math.sin(angle), rng.uniform(-.6, .6)))*size
        v = Vector((-math.sin(angle), math.cos(angle), .1))*size*width
        add(rng.choices(foliage, [3, 5, 3, 1])[0],
            [p-u, p+v, p+Vector((0, 0, .03)), p+u, p-v],
            [(0, 1, 2), (1, 3, 2), (3, 4, 2), (4, 0, 2)])

    # Map north is smaller pixel y. Heights are scaled against 3.35 m storeys.
    trees = [
        ('46', 'south', 137, 135, 12.2, 3.5, 'broadleaf', '1,2'),
        ('46', 'south', 156, 131, 11.5, 3.2, 'broadleaf', '2,4'),
        ('46', 'south', 212, 120, 12.8, 3.5, 'broadleaf', '4,5'),
        ('46', 'west', 119, 77, 11.3, 3.2, 'broadleaf', '1'),
        ('46', 'west', 120, 99, 12.0, 3.4, 'broadleaf', '1'),
        ('46', 'east', 220, 84, 11.8, 3.2, 'broadleaf', '5'),
        ('46', 'north', 145, 51, 12.8, 2.0, 'feathery', '6,7'),
        ('46', 'north', 164, 47, 13.2, 2.1, 'feathery', '6,7'),
        ('46', 'north', 183, 43, 12.4, 1.9, 'feathery', '6,7'),
        ('46', 'north', 154, 51, 5.6, 2.0, 'palm', '6,7'),
        ('46', 'north', 174, 47, 6.2, 2.1, 'palm', '6,7'),
        ('51', 'north', 139, 157, 12.5, 3.6, 'broadleaf', '7,8,9'),
        ('51', 'north', 160, 152, 13.0, 3.8, 'broadleaf', '7,8,9'),
        ('51', 'north', 195, 144, 12.1, 3.4, 'broadleaf', '7,8,9'),
    ]
    records = []

    def segment_distance(p, a, b):
        a, b = xy(a), xy(b)
        t = max(0, min(1, (p-a).dot(b-a)/(b-a).length_squared))
        return (p-a-(b-a)*t).length

    for bid, side, px, py, h, radius, kind, photos in trees:
        base = xy((px, py)); base.z = .12
        assert not blocked(base), (bid, px, py, 'inside building')
        clear = min(segment_distance(xy((px, py)), a, b)-width/2
                    for path, width in routes for a, b in zip(path, path[1:]))
        assert clear > .32, (bid, px, py, 'road clearance', clear)
        records.append(dict(building=bid, side=side, pixel=[px, py], height_m=h,
                            crown_radius_m=radius, type=kind, photos=photos,
                            road_clearance_m=round(clear, 3)))
        trunk_radius = .23 if kind == 'broadleaf' else .15
        split = h*(.38 if kind == 'broadleaf' else .86)
        trunk = [base+Vector((.10*math.sin(i), .08*math.cos(i), split*i/5)) for i in range(6)]
        for i in range(5):
            branch(trunk[i], trunk[i+1], trunk_radius*(1-i*.10), trunk_radius*(.9-i*.10))
        if kind != 'palm':
            branch(trunk[-1], base+Vector((0, 0, h*(.97 if kind == 'feathery' else .84))), trunk_radius*.4, .012)
        branch(base, base+Vector((0, 0, 1.05)), trunk_radius+.012, trunk_radius, pale)
        if kind == 'palm':
            top = trunk[-1]
            # Fan-shaped, pleated blades rather than spherical crowns.
            for i in range(15):
                angle = i*2.399
                d = Vector((math.cos(angle), math.sin(angle), 0))
                hub = top+d*radius*.52+Vector((0, 0, .35+(i%3)*.22))
                branch(top, hub, .026, .012)
                for j in range(13):
                    theta = angle+(j-6)*.115
                    tip = hub+Vector((math.cos(theta), math.sin(theta), -.24))*radius*.57
                    tangent = Vector((-math.sin(theta), math.cos(theta), .03))*.095
                    add(foliage[j%3], [hub, tip+tangent, tip+Vector((0, 0, .07)), tip-tangent],
                        [(0, 1, 2), (0, 2, 3)])
            continue
        count = 23 if kind == 'feathery' else 13
        for i in range(count):
            angle = i*2.399+rng.uniform(-.2, .2)
            z = h*(.27+.68*i/count) if kind == 'feathery' else split+rng.uniform(0, h*.25)
            reach = radius*(1-i/count)*1.05 if kind == 'feathery' else radius*rng.uniform(.65, 1)
            a = base+Vector((0, 0, z))
            b = a+Vector((math.cos(angle)*reach, math.sin(angle)*reach,
                          .3 if kind == 'feathery' else h*.20))
            branch(a, b, .045 if kind == 'feathery' else .11, .012)
            for j in range(5):
                start = a.lerp(b, .3+j*.14)
                phi = angle+(j%2*2-1)*.9
                tip = start+Vector((math.cos(phi)*reach*.36, math.sin(phi)*reach*.36, .45))
                branch(start, tip, .025, .005)
                for _ in range(36 if kind == 'feathery' else 60):
                    spread = .40 if kind == 'feathery' else .72
                    p = tip+Vector((rng.gauss(0, spread), rng.gauss(0, spread), rng.gauss(0, spread*.55)))
                    leaf(p, rng.uniform(.09, .17) if kind == 'feathery' else rng.uniform(.13, .22))

    # Low clipped planting beside the south facade; keep the central porch clear.
    hedge_points = [(x, 133-(x-137)*.196) for x in range(137, 163, 3)]
    hedge_points += [(x, 120-(x-204)*.196) for x in range(204, 226, 3)]
    # Rear groundcover below palms, not a barrier across the bicycle access.
    hedge_points += [(x, 57-(x-145)*.23) for x in range(145, 188, 3)]
    for px, py in hedge_points:
        p = xy((px, py))
        if blocked(p):
            continue
        for _ in range(130):
            q = p+Vector((rng.uniform(-.55, .55), rng.uniform(-.35, .35), rng.uniform(.18, .68)))
            leaf(q, rng.uniform(.055, .095))
    # User's additional entrance photo: bamboo at the HIGH bar's east end wall,
    # beyond the entrance lawn, not on the low bar or in the vehicle approach.
    bamboo = []
    for i in range(64):
        py = rng.uniform(162, 176)
        px = 224 + (py-161)*2/15 + rng.uniform(.7, 3.3)
        p = xy((px, py)); p.z = .1
        assert not blocked(p)
        clear = min(segment_distance(xy((px, py)), a, b)-width/2
                    for path, width in routes for a, b in zip(path, path[1:]))
        assert clear > .4
        h = rng.uniform(2.9, 4.1)
        lean = Vector((rng.uniform(-.18, .28), rng.uniform(-.22, .22), 0))
        for j in range(12):
            a = p+Vector((0, 0, h*j/12))+lean*(j/12)**2
            b = p+Vector((0, 0, h*(j+1)/12))+lean*((j+1)/12)**2
            branch(a, b, .026, .022, foliage[2])
            branch(a, a+Vector((0, 0, .035)), .031, .031, foliage[1])
            if j < 5:
                continue
            angle = j*2.399+i
            tip = b+Vector((math.cos(angle)*.45, math.sin(angle)*.45, .12))
            branch(b, tip, .009, .002, foliage[1])
            for _ in range(22):
                q = tip+Vector((rng.uniform(-.26, .26), rng.uniform(-.26, .26), rng.uniform(-.17, .22)))
                leaf(q, rng.uniform(.10, .19), .15)
        bamboo.append(dict(pixel=[round(px, 3), round(py, 3)], height_m=round(h, 2),
                           road_clearance_m=round(clear, 3)))
    # Latest user correction supersedes the earlier removal of entrance trees.
    # Isolated seed keeps all previously reviewed perimeter planting unchanged.
    rng = random.Random(23307130131)
    entrance_trees = [
        (202, 218, 7.6, 1.9, 'dense evergreen beside low end wall'),
        (204, 184, 4.0, 1.15, 'small tree beside north entrance corner'),
        (212, 195, 4.9, 1.6, 'branching ornamental tree in flower bed'),
        (219, 190, 4.3, .95, 'sparse ornamental tree behind flowers'),
        (230, 207, 12.4, 3.8, 'large roadside tree in front of lawn'),
    ]
    for px, py, height, radius, description in entrance_trees:
        p = xy((px, py)); p.z = .12
        assert not blocked(p), (description, 'building overlap')
        clear = min(segment_distance(xy((px, py)), a, b)-width/2
                    for path, width in routes for a, b in zip(path, path[1:]))
        assert clear > .4
        records.append(dict(building='51', side='east entrance', pixel=[px, py],
            height_m=height, crown_radius_m=radius, type=description,
            photos='latest three entrance detail photos', road_clearance_m=round(clear, 3)))
        thick = .30 if height > 10 else .11
        top = p+Vector((.12, -.10, height*.42))
        branch(p, top, thick, thick*.65)
        branch(top, p+Vector((.12, -.10, height*.80)), thick*.65, .012)
        if height > 10:
            branch(p, p+Vector((.02, -.02, 1.1)), thick+.01, thick, pale)
        for i in range(15):
            angle = i*2.399
            z = height*(.25+.5*i/15)
            a = p+Vector((.12, -.10, z))
            b = a+Vector((math.cos(angle)*radius*.8, math.sin(angle)*radius*.8, height*.15))
            branch(a, b, thick*.35, .012)
            for j in range(4):
                phi = angle+(j-1.5)*.52
                tip = a.lerp(b, .4+j*.18)+Vector((math.cos(phi)*radius*.3, math.sin(phi)*radius*.3, .25))
                branch(a.lerp(b, .4+j*.18), tip, .018, .004)
                density = 80 if 'dense' in description else 14 if 'sparse' in description else 70 if height > 10 else 32
                for _ in range(density):
                    spread = radius*.22
                    q = tip+Vector((rng.gauss(0, spread), rng.gauss(0, spread), rng.gauss(0, spread*.65)))
                    leaf(q, rng.uniform(.075, .13) if height < 10 else rng.uniform(.14, .22))

    # Low leaf shrubs behind a connected, softly lobed bed; no straight color strip.
    for px, py, radius in [(215, 188, .68), (222, 193, .75), (207, 208, .55)]:
        center = xy((px, py))+Vector((0, 0, radius*.7))
        for _ in range(900):
            theta = rng.random()*math.tau; z = rng.uniform(-.7, 1)
            r = radius*math.sqrt(1-z*z)*rng.uniform(.78, 1)
            leaf(center+Vector((math.cos(theta)*r, math.sin(theta)*r, z*radius*.65)), rng.uniform(.045, .08))
    petals = [material('周边Tree花簇红', (.55, .018, .035)),
              material('周边Tree花簇金黄', (.85, .59, .045)),
              material('周边Tree花簇浅粉', (.76, .52, .60))]
    soil = material('周边Tree花坛腐殖土', (.12, .085, .045))
    beds = [(210, 201, 1.35, 2.0, 0), (215, 201, 1.45, 2.15, 1),
            (219, 197, 1.5, 2.45, 2)]
    for px, py, rx, ry, color in beds:
        center = xy((px, py)); center.z = .16
        ring = [center+Vector((math.cos(i*math.tau/40)*rx, math.sin(i*math.tau/40)*ry, 0)) for i in range(40)]
        add(soil, [center]+ring, [(0, i+1, (i+1)%40+1) for i in range(40)])
        for _ in range(950):
            theta = rng.random()*math.tau; r = math.sqrt(rng.random())
            p = center+Vector((math.cos(theta)*rx*r, math.sin(theta)*ry*r,
                               .18+.16*(1-r*r)+rng.uniform(-.06, .06)))
            leaf(p-Vector((0, 0, .12)), .08)
            size = rng.uniform(.06, .085)
            # Small individual petals, varying height and orientation.
            verts = [p]+[p+Vector((math.cos(theta+i*math.tau/10)*size*(1 if i%2 else .58),
                                  math.sin(theta+i*math.tau/10)*size*(1 if i%2 else .58), .018 if i%2 else 0)) for i in range(10)]
            add(petals[color], verts, [(0, i+1, (i+1)%10+1) for i in range(10)])
    for name, (vertices, faces) in buffers.items():
        mesh = bpy.data.meshes.new(name); mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(bpy.data.materials[name])
        obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj)
        obj['campusVegetation'] = True
        obj['source'] = 'field photos 46/1,2,4,5,6,7; 51/7,8,9; approximate map placement'
    (output/'planting.json').write_text(json.dumps(dict(
        seed=23307130130, accuracy='photo-informed estimates, not surveyed',
        trees=records, bamboo=dict(location='51 high bar east end', stalks=bamboo,
            source='user entrance photo with bamboo at right end wall'),
        east_entrance_planting='latest user photos: five trees, shrubs and three flower drifts',
        entrance_vehicle_approach_kept_clear=True,
        existing_west_courtyard_preserved=True), ensure_ascii=False, indent=2))
