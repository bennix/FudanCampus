"""7 仓库: squarer, taller industrial block (schematic; map footprint elongated)."""
def build_north_warehouse(x, y, mat, mesh, current, bpy):
    metal = mat('Warehouse metal wall', (0.54, 0.57, 0.59))
    dark = mat('Warehouse dark frame', (0.22, 0.24, 0.26))
    door = mat('Warehouse roller door', (0.48, 0.50, 0.52))
    roof = mat('Warehouse flat roof', (0.38, 0.40, 0.42))
    trim = mat('Warehouse coping', (0.62, 0.64, 0.63))

    side = 24.0
    wall_h = 10.8
    fy = side / 2 + 0.06

    buffers = {}

    def b(dx, dy, z, w, d, h, m):
        vs, fs = buffers.setdefault(m.name, ([], []))
        n = len(vs)
        vs.extend(
            [
                (x + dx + a * w / 2, y + dy + c * d / 2, z + e * h / 2)
                for a, c, e in [
                    (-1, -1, -1),
                    (-1, -1, 1),
                    (-1, 1, -1),
                    (-1, 1, 1),
                    (1, -1, -1),
                    (1, -1, 1),
                    (1, 1, -1),
                    (1, 1, 1),
                ]
            ]
        )
        fs.extend(
            [
                tuple(n + i for i in f)
                for f in [(0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4), (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6)]
            ]
        )

    b(0, 0, 0.35, side + 0.8, side + 0.8, 0.7, trim)
    b(0, 0, wall_h / 2 + 0.35, side, side, wall_h, metal)
    b(0, 0, wall_h + 0.55, side + 0.5, side + 0.5, 0.35, roof)
    b(0, 0, wall_h + 0.82, side + 0.55, side + 0.55, 0.22, trim)

    # South face: wide roller doors (primary elevation).
    for cx in (-7.5, -2.5, 2.5, 7.5):
        b(cx, -fy - 0.1, 2.8, 4.0, 0.16, 5.2, door)
        b(cx, -fy - 0.08, 2.8, 4.15, 0.1, 5.35, dark)
    b(0, -fy - 0.12, 5.6, side - 1.5, 0.12, 0.35, dark)

    # High clerestory strip on south.
    for cx in range(-10, 11, 5):
        b(cx, -fy - 0.08, 8.2, 3.2, 0.1, 1.8, dark)
        b(cx, -fy - 0.14, 8.2, 2.9, 0.06, 1.55, metal)

    # Corner pilasters for a blockier silhouette.
    for sx in (-1, 1):
        for sy in (-1, 1):
            b(sx * (side / 2 - 0.35), sy * (side / 2 - 0.35), wall_h / 2 + 0.35, 0.55, 0.55, wall_h, dark)

    label = '仓库'
    for name, (vs, fs) in buffers.items():
        ob = mesh(f'{label} · {name}', vs, fs, bpy.data.materials[name])
        ob['building_id'] = '7'
        ob['building_name'] = label
        ob['source'] = 'map anchor; squarer taller warehouse block; sides approximate'
