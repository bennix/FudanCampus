import * as THREE from 'three';

// Dimensions in metres, relative to the centre used by chemistry_geometry.py.
export function buildingDetails(id: string) {
  if (!['buildings-20', 'buildings-55', 'buildings-56'].includes(id)) return;
  const parts: THREE.Matrix4[] = [];
  const box = (
    x: number,
    y: number,
    z: number,
    w: number,
    h: number,
    d: number,
  ) => {
    parts.push(new THREE.Matrix4().makeScale(w, h, d).setPosition(x, y, z));
  };
  if (id === 'buildings-20') {
    for (let x = -42; x <= 42; x += 6)
      for (let level = 0; level < 5; level++) {
        if (Math.abs(x) < 3 && !level) continue;
        box(
          x,
          0.78 + level * 3.45,
          Math.abs(x) < 7 ? 7.8 : 7.14,
          3.82,
          0.12,
          0.48,
        );
      }
  } else if (id === 'buildings-56') {
    for (const x of [-29, -23.8, -16.4, -11.3, 3, 8.3, 13.6, 23.8, 29]) {
      box(x, 5.59, -8.32, 3.8, 0.12, 0.44);
      if (x < 0 || x > 20) box(x, 0.87, -8.32, 3.8, 0.12, 0.44);
    }
  } else {
    for (const [left, right, z] of [
      [-17.2, 17.2, 5],
      [-32.8, -17.2, 16.4],
      [17.2, 32.8, 16.4],
    ]) {
      const bays = Math.floor((right - left) / 4.7);
      for (let i = 0; i < bays; i++) {
        for (const y of [2.6, 6.6, 10.3])
          box(
            left + ((i + 0.5) * (right - left)) / bays,
            y - 1.36,
            z + 0.19,
            2.96,
            0.12,
            0.42,
          );
      }
    }
    for (const z of [-11, -6, 0, 6, 11]) {
      for (const y of [2.6, 6.6, 10.3]) {
        if (z || y > 3) box(33, y - 1.36, z, 0.42, 0.12, 2.96);
      }
    }
    for (const [x, w, d] of [
      [-25, 15.6, 32.8],
      [25, 15.6, 32.8],
      [0, 34.4, 10],
    ]) {
      for (const sign of [-1, 1]) {
        box(x, 12.68, (sign * d) / 2, w + 0.18, 0.16, 0.24);
        if (x) box(x + (sign * w) / 2, 12.68, 0, 0.24, 0.16, d);
      }
    }
  }
  const stoneCount = parts.length;
  if (id === 'buildings-55')
    for (const z of [-1.7, 0, 1.7]) {
      box(33.55, 1.45, z + 0.48, 0.035, 0.48, 0.035);
      for (const y of [1.24, 1.66]) box(33.49, y, z + 0.48, 0.13, 0.035, 0.035);
    }
  const group = new THREE.Group();
  for (const [start, end, color, metalness] of [
    [0, stoneCount, 0xbebbb1, 0.06],
    [stoneCount, parts.length, 0x858b89, 0.78],
  ]) {
    if (start === end) continue;
    const mesh = new THREE.InstancedMesh(
      new THREE.BoxGeometry(),
      new THREE.MeshStandardMaterial({
        color,
        metalness,
        roughness: metalness > 0.5 ? 0.32 : 0.78,
      }),
      end - start,
    );
    parts.slice(start, end).forEach((matrix, i) => mesh.setMatrixAt(i, matrix));
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    group.add(mesh);
  }
  return group;
}

// Object-space coordinates keep the surface grain aligned on models without UVs.
export function detailSurface(m: THREE.MeshStandardMaterial) {
  if (/glass|glazing|玻璃/i.test(m.name)) {
    m.metalness = Math.max(0.22, m.metalness);
    m.envMapIntensity = 0.64;
    m.roughness = 0.23;
    return;
  }
  const brick = /brick|红砖/i.test(m.name);
  if (!brick && !/asphalt|concrete|pavement|plaster|stucco|沥青/i.test(m.name))
    return;
  m.customProgramCacheKey = () => (brick ? 'campus-brick' : 'campus-grain');
  m.onBeforeCompile = (shader) => {
    shader.vertexShader =
      'varying vec3 facadePosition;\n' +
      shader.vertexShader.replace(
        '#include <begin_vertex>',
        '#include <begin_vertex>\nfacadePosition=position;',
      );
    shader.fragmentShader =
      'varying vec3 facadePosition;\n' +
      shader.fragmentShader.replace(
        '#include <color_fragment>',
        `
      #include <color_fragment>
      vec3 p=facadePosition;
      vec3 grain=floor(p*75.);
      float noiseValue=fract(sin(dot(mod(grain,197.),vec3(12.9898,78.233,39.425)))*43758.5453);
      diffuseColor.rgb*=1.+(noiseValue-.5)*.14*(1.-smoothstep(.008,.035,length(fwidth(p))));
      ${
        brick
          ? `vec2 course=vec2((p.x+p.z)/.23,p.y/.085);
      course.x+=.5*mod(floor(course.y),2.);
      vec2 edge=.5-abs(fract(course)-.5);
      vec2 seam=smoothstep(vec2(.018,.048),vec2(.055,.12)+fwidth(course)*.5,edge);
      float nearFade=1.-smoothstep(.1,.6,length(fwidth(course)));
      diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.39,.34,.29),.43*(1.-min(seam.x,seam.y))*nearFade);`
          : ''
      }
    `,
      );
  };
}

export function daylightSky() {
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 256;
  const ctx = canvas.getContext('2d')!;
  const gradient = ctx.createLinearGradient(0, 0, 0, 256);
  for (const [y, color] of [
    [0, '#4275a2'],
    [0.29, '#82abc8'],
    [0.5, '#dbe1db'],
    [1, '#b9bdaf'],
  ] as const)
    gradient.addColorStop(y, color);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 256);
  const sky = new THREE.CanvasTexture(canvas);
  sky.mapping = THREE.EquirectangularReflectionMapping;
  sky.colorSpace = THREE.SRGBColorSpace;
  return sky;
}
