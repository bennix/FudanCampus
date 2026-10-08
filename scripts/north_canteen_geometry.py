"""5 北区食堂: south (front) facade from photos/食堂照片.webp; other elevations approximate grey shell."""
def build_north_canteen(x, y, mat, mesh, current, bpy):
    panel = mat('Canteen grey panel', (0.52, 0.55, 0.54))
    pale = mat('Canteen pale trim', (0.68, 0.70, 0.69))
    dark = mat('Canteen dark frame', (0.14, 0.16, 0.17))
    glass = mat('Canteen glazing', (0.22, 0.38, 0.40), 0.32)
    canopy = mat('Canteen canopy soffit', (0.46, 0.48, 0.47))
    roof = mat('Canteen roof metal', (0.28, 0.30, 0.32))
    decor = mat('Canteen X decor', (0.58, 0.60, 0.59))
    rail = mat('Canteen roof rail', (0.72, 0.74, 0.73))

    W, D = 49.6, 41.6
    fy = -D / 2 - 0.08
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

    # Placeholder volume for north / sides (no photo yet).
    b(0, 6, 6.5, W - 1.2, D * 0.52, 12.8, panel)
    b(-W * 0.48, 0, 6.5, 2.2, D - 4, 12.8, panel)
    b(W * 0.48, 0, 6.5, 2.2, D - 4, 12.8, panel)

    # South front wall plane.
    b(0, fy + 0.06, 6.5, W - 0.8, 0.35, 12.6, panel)

    # Floor slab belt between storeys.
    b(0, fy + 0.12, 6.55, W - 0.4, 0.55, 0.45, pale)

    # Ground floor curtain wall (centre bays).
    for cx in [-14, -9.5, -5, -0.5, 4, 8.5, 13, 17.5]:
        b(cx, fy - 0.12, 3.4, 3.35, 0.14, 5.2, dark)
        b(cx, fy - 0.22, 3.4, 3.05, 0.06, 4.85, glass)
        b(cx, fy - 0.26, 3.4, 3.25, 0.04, 5.05, dark)
    # Wider door leaves in centre.
    for cx in [-2.2, 2.2]:
        b(cx, fy - 0.14, 2.1, 2.0, 0.12, 3.6, glass)
        b(cx, fy - 0.22, 2.1, 2.15, 0.08, 3.75, dark)

    # Second floor windows.
    for cx in [-16, -11.5, -7, -2.5, 2, 6.5, 11, 15.5, 20]:
        b(cx, fy - 0.12, 9.8, 3.2, 0.14, 4.6, dark)
        b(cx, fy - 0.22, 9.8, 2.9, 0.06, 4.35, glass)

    # Ground-floor entrance canopy.
    b(0, fy - 1.35, 6.35, 38, 2.8, 0.35, canopy)
    b(0, fy - 2.55, 6.05, 36, 0.45, 0.28, pale)
    for cx in [-15, -7.5, 0, 7.5, 15]:
        b(cx, fy - 2.05, 5.2, 0.55, 0.55, 4.8, dark)

    # Second-floor cantilever lip.
    b(0, fy - 0.85, 12.55, 42, 1.6, 0.32, canopy)
    b(0, fy - 1.55, 12.35, 40, 0.35, 0.22, pale)

    # Roof parapet rail (photo: low grey fence above 2F).
    b(0, fy - 0.35, 13.15, 43, 0.9, 0.55, rail)
    for cx in range(-21, 22, 3):
        b(cx, fy - 0.35, 13.55, 0.12, 0.12, 0.45, dark)

    # Upper service roof block behind parapet.
    b(0, fy + 2, 14.8, 28, 18, 2.4, roof)
    b(0, fy + 1, 15.9, 26, 16, 0.35, roof)

    # East wing: raised X / honeycomb panels (photo right side).
    for row, z in enumerate([2.4, 5.6, 8.8, 11.5]):
        for col, cx in enumerate([10.5, 14.5, 18.5, 22.5]):
            if row == 3 and col == 3:
                continue
            s = 1.15
            b(cx, fy - 0.18, z, s * 1.5, 0.22, 0.18, decor)
            b(cx, fy - 0.18, z, 0.22, 0.22, s * 1.5, decor)
            b(cx - s * 0.32, fy - 0.2, z + s * 0.32, 0.38, 0.14, 0.38, decor)
            b(cx + s * 0.32, fy - 0.2, z + s * 0.32, 0.38, 0.14, 0.38, decor)
            b(cx - s * 0.32, fy - 0.2, z - s * 0.32, 0.38, 0.14, 0.38, decor)
            b(cx + s * 0.32, fy - 0.2, z - s * 0.32, 0.38, 0.14, 0.38, decor)

    b(22, fy + 0.05, 6.5, 5.5, 0.4, 12.5, panel)

    label = '北区食堂'
    for name, (vs, fs) in buffers.items():
        ob = mesh(f'{label} · {name}', vs, fs, bpy.data.materials[name])
        ob['building_id'] = '5'
        ob['building_name'] = label
        ob['source'] = 'photos/食堂照片.webp south facade; other sides placeholder'
