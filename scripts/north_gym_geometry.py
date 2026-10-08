"""3 北区体育馆: square hall + north square track field (no photo; schematic)."""
def build_north_gym(x, y, mat, mesh, current, bpy):
    wall = mat('Gym pale panel', (0.62, 0.65, 0.68))
    trim = mat('Gym trim', (0.78, 0.80, 0.82))
    roof = mat('Gym roof metal', (0.35, 0.38, 0.42))
    glass = mat('Gym clerestory glass', (0.25, 0.40, 0.45), 0.35)
    track = mat('Gym track red', (0.62, 0.14, 0.12))
    grass = mat('Gym field grass', (0.28, 0.48, 0.24))
    line = mat('Gym track line', (0.92, 0.92, 0.90))
    fence = mat('Gym fence rail', (0.38, 0.48, 0.40))
    fence_post = mat('Gym fence post', (0.50, 0.52, 0.51))

    W, D = 40.0, 48.8
    hall = 36.0
    hall_dy = -6.0
    field_dy = 14.0
    field_size = 34.0
    inner = 22.0

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

    # Square gym hall (south portion of footprint).
    b(0, hall_dy, 6.2, hall, hall, 12.4, wall)
    b(0, hall_dy, 12.65, hall + 0.6, hall + 0.6, 0.45, trim)
    b(0, hall_dy - hall / 2 - 0.12, 6.5, hall, 0.35, 11.8, wall)
    b(0, hall_dy - hall / 2 - 0.22, 3.2, 10, 0.12, 4.8, glass)
    b(0, hall_dy - hall / 2 - 0.22, 8.8, 10, 0.12, 4.8, glass)
    b(0, hall_dy, 13.4, 22, 16, 2.2, roof)
    b(0, hall_dy, 14.6, 14, 10, 1.1, roof)

    # North square athletics field: red track + green infield.
    b(0, field_dy, 0.12, field_size + 4, field_size + 4, 0.24, grass)
    ring = (field_size - inner) / 2
    b(0, field_dy + inner / 2 + ring / 2, 0.22, field_size, ring, 0.14, track)
    b(0, field_dy - inner / 2 - ring / 2, 0.22, field_size, ring, 0.14, track)
    b(-inner / 2 - ring / 2, field_dy, 0.22, ring, inner, 0.14, track)
    b(inner / 2 + ring / 2, field_dy, 0.22, ring, inner, 0.14, track)
    b(0, field_dy, 0.28, inner, inner, 0.08, grass)
    b(0, field_dy, 0.34, inner - 1.2, 0.12, 0.04, line)
    b(0, field_dy, 0.34, 0.12, inner - 1.2, 0.04, line)

    # Perimeter fence around the field (posts + twin rails).
    fence_span = field_size + 6.0
    hf = fence_span / 2
    fh = 1.35
    z_rail_lo, z_rail_hi = 0.52, 1.08
    for sx in (-1, 1):
        for sy in (-1, 1):
            b(sx * hf, field_dy + sy * hf, fh / 2, 0.16, 0.16, fh, fence_post)
    for side in (-1, 1):
        b(0, field_dy + side * hf, z_rail_lo, fence_span, 0.09, 0.09, fence)
        b(0, field_dy + side * hf, z_rail_hi, fence_span, 0.09, 0.09, fence)
        b(side * hf, field_dy, z_rail_lo, 0.09, fence_span, 0.09, fence)
        b(side * hf, field_dy, z_rail_hi, 0.09, fence_span, 0.09, fence)
    step = 3.2
    n = int(hf / step)
    for i in range(-n, n + 1):
        px = i * step
        if abs(px) >= hf - 0.25:
            continue
        b(px, field_dy + hf, fh / 2, 0.11, 0.11, fh, fence_post)
        b(px, field_dy - hf, fh / 2, 0.11, 0.11, fh, fence_post)
        b(hf, field_dy + px, fh / 2, 0.11, 0.11, fh, fence_post)
        b(-hf, field_dy + px, fh / 2, 0.11, 0.11, fh, fence_post)

    label = '北区体育馆'
    for name, (vs, fs) in buffers.items():
        ob = mesh(f'{label} · {name}', vs, fs, bpy.data.materials[name])
        ob['building_id'] = '3'
        ob['building_name'] = label
        ob['source'] = 'map footprint; square hall + schematic track infield; no photograph'
