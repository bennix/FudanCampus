import assert from 'node:assert/strict';
import { getBounds } from '@gltf-transform/core';
import { copyToDocument, prune, unpartition } from '@gltf-transform/functions';
import { Matrix4, Vector3, BufferGeometry, Float32BufferAttribute } from 'three';

// The old generator batched windows, frames, steps and roof trims by material,
// without building IDs. Ownership must therefore be checked in world space.
export function triangleVertices(node, primitive, offset) {
  const positions = primitive.getAttribute('POSITION');
  const indices = primitive.getIndices();
  const matrix = new Matrix4().fromArray(node.getWorldMatrix());
  return [0, 1, 2].map(i => new Vector3().fromArray(positions.getElement(indices ? indices.getScalar(offset + i) : offset + i, []))
    .applyMatrix4(matrix).toArray());
}
export function insideFootprint(point, box) {
  return point[0] >= box.min[0] && point[0] <= box.max[0] && point[2] >= box.min[2] && point[2] <= box.max[2];
}
export const ROAD_REPLACEMENTS = [
  ['Campus east west road.009', 'HB42_CONTEXT_Campus east west road.001'],
  ['Pedestrian connection.022', 'HB42_CONTEXT_Pedestrian connection.005'],
];
export const APRON = 'HB42_CONTEXT_GradedApron';

export function surfaceHeight(vertices, x, z) {
  const [a,b,c] = vertices;
  const den=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2]);
  if(Math.abs(den)<1e-8)return null;
  const u=((b[2]-c[2])*(x-c[0])+(c[0]-b[0])*(z-c[2]))/den;
  const v=((c[2]-a[2])*(x-c[0])+(a[0]-c[0])*(z-c[2]))/den;
  return u>=-1e-7&&v>=-1e-7&&u+v<=1.0000001 ? u*a[1]+v*b[1]+(1-u-v)*c[1] : null;
}
function repairApron(document, node) {
  // v14's exchanged long elevations left folded/overlapping rim triangles.
  // Resample its existing upper surface as one continuous height field. Keep
  // the footprint and heights, with 15mm clearance above the terrain plane.
  const box=getBounds(node), triangles=[];
  for(const p of node.getMesh().listPrimitives())for(let i=0;i<p.getIndices().getCount();i+=3)
    triangles.push(triangleVertices(node,p,i));
  const vertices=[],uv=[],indices=[],inverse=new Matrix4().fromArray(node.getWorldMatrix()).invert();
  const nx=48,nz=24;
  for(let row=0;row<=nz;row++)for(let col=0;col<=nx;col++){
    const x=box.min[0]+(box.max[0]-box.min[0])*col/nx;
    const z=box.min[2]+(box.max[2]-box.min[2])*row/nz;
    let y=-.085;
    for(const t of triangles){const h=surfaceHeight(t,x,z);if(h!==null)y=Math.max(y,h);}
    vertices.push(...new Vector3(x,y,z).applyMatrix4(inverse).toArray());uv.push(col/2,row/2);
    if(row<nz&&col<nx){const a=row*(nx+1)+col,b=a+1,c=a+nx+1,d=c+1;indices.push(a,c,b,b,c,d);}
  }
  const geometry=new BufferGeometry();geometry.setAttribute('position',new Float32BufferAttribute(vertices,3));
  geometry.setIndex(indices);geometry.computeVertexNormals();
  const p=node.getMesh().listPrimitives()[0],buffer=document.getRoot().listBuffers()[0];
  for(const semantic of p.listSemantics())p.setAttribute(semantic,null);
  const accessor=(type,array)=>document.createAccessor().setType(type).setArray(array).setBuffer(buffer);
  p.setAttribute('POSITION',accessor('VEC3',new Float32Array(vertices)));
  p.setAttribute('NORMAL',accessor('VEC3',geometry.getAttribute('normal').array));
  p.setAttribute('TEXCOORD_0',accessor('VEC2',new Float32Array(uv)));
  p.setIndices(accessor('SCALAR',new Uint32Array(indices)));geometry.dispose();
}

export async function repairContext(io, publicDir) {
  const historic = await io.read(`${publicDir}/models/shared/01.glb`);
  const roads = await io.read(`${publicDir}/models/shared/00.glb`);
  const accepted = await io.read(`${publicDir}/hanbing-final-v14/campus.glb`);
  const body = historic.getRoot().listNodes().find(n => String(n.getExtras().building_id) === '42');
  assert(body, 'Missing original Hanbing body');
  const oldBox = getBounds(body);
  const footprint = { min: [oldBox.min[0] - 2.0, 0, oldBox.min[2] - 2.0],
    max: [oldBox.max[0] + 2.0, 20, oldBox.max[2] + 2.0] };
  const removedNodes = [];
  const trimmed = [];
  for (const node of [...historic.getRoot().listNodes()]) {
    if (node === body || node.getName().startsWith('寒冰馆（500号） hipped tiled roof')) {
      removedNodes.push(node.getName()); node.dispose(); continue;
    }
    if (!node.getName().includes(' details')) continue;
    for (const primitive of node.getMesh()?.listPrimitives() ?? []) {
      const indices = primitive.getIndices();
      assert(indices, 'Expected indexed batch');
      const kept = [];
      let removedTriangles = 0;
      for (let offset = 0; offset < indices.getCount(); offset += 3) {
        const flags = triangleVertices(node, primitive, offset).map(p => insideFootprint(p, footprint));
        assert(flags.every(Boolean) || flags.every(v => !v), `Ambiguous ownership at ${node.getName()}`);
        if (flags.every(Boolean)) removedTriangles++;
        else for (let i = 0; i < 3; i++) kept.push(indices.getScalar(offset + i));
      }
      if (removedTriangles) {
        assert(kept.length, 'Do not remove the entire shared batch');
        primitive.setIndices(historic.createAccessor().setType('SCALAR')
          .setArray(new Uint32Array(kept)).setBuffer(indices.getBuffer()));
        trimmed.push({ name: node.getName(), removedTriangles });
      }
    }
  }
  assert.equal(removedNodes.length, 2, 'Remove both old body and separate roof');
  assert(trimmed.some(x => x.name.startsWith('Window frames')));
  assert(trimmed.some(x => x.name.startsWith('Dark blue grey')));
  // Bring back only the two accepted clipped road segments and the entrance apron.
  // Importing the whole accepted campus would revert unrelated upstream changes.
  const scene = roads.getRoot().listScenes()[0];
  for (const [oldName, acceptedName] of [...ROAD_REPLACEMENTS, [null, APRON]]) {
    const source = accepted.getRoot().listNodes().find(n => n.getName() === acceptedName);
    assert(source && !source.getParentNode(), `Missing root context node: ${acceptedName}`);
    if (oldName) {
      const oldNode = roads.getRoot().listNodes().find(n => n.getName() === oldName);
      assert(oldNode, `Missing road: ${oldName}`); oldNode.dispose();
    }
    const copied = copyToDocument(roads, accepted, [source]).get(source);
    if (acceptedName === APRON) {
      repairApron(roads,copied);
    }
    scene.addChild(copied);
  }
  await historic.transform(prune({ keepExtras: true, keepLeaves: true, keepAttributes: true, keepSolidTextures: true }));
  await roads.transform(prune({ keepExtras: true, keepLeaves: true, keepAttributes: true, keepSolidTextures: true }));
  await roads.transform(unpartition());
  return { historic: Buffer.from(await io.writeBinary(historic)), roads: Buffer.from(await io.writeBinary(roads)),
    report: { footprint, removedNodes, trimmed, roads: ROAD_REPLACEMENTS, apron: APRON } };
}


