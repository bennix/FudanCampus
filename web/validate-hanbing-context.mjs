import assert from 'node:assert/strict';
import { NodeIO, getBounds } from '@gltf-transform/core';
import { fileURLToPath } from 'node:url';
import { ROAD_REPLACEMENTS, APRON, triangleVertices, insideFootprint } from './hanbing-context.mjs';
const io = new NodeIO();
const dir = fileURLToPath(new URL('./public/', import.meta.url));
const load = relative => io.read(dir + relative);
const old = await load('models/shared/01.glb');
const current = await load('models/shared/01-hanbing-v14.glb');
const oldRoads = await load('models/shared/00-hanbing-baseline.glb');
const roads = await load('models/shared/00-hanbing-v14.glb');
const accepted = await load('hanbing-final-v14/campus.glb');
const footprint = { min: [-271.601, 0, -184.801], max: [-245.199, 20, -168.799] };
const counts = new Map([
  ['Walkway stone details.004', 48], ['Window frames and coping details.004', 504],
  ['Dark blue grey glazing details.004', 492], ['Charcoal grey roof tiles details.002', 12],
]);
function compareNode(a, b, trimmed = false) {
  assert(b, `Missing ${a.getName()}`);
  assert.deepEqual(a.getWorldMatrix(), b.getWorldMatrix(), a.getName());
  assert.deepEqual(a.getExtras(), b.getExtras());
  const ap = a.getMesh()?.listPrimitives() ?? [], bp = b.getMesh()?.listPrimitives() ?? [];
  assert.equal(ap.length, bp.length);
  ap.forEach((p, i) => {
    assert.deepEqual(p.listSemantics(), bp[i].listSemantics());
    for (const semantic of p.listSemantics()) {
      let expectedAttribute = p.getAttribute(semantic).getArray();
      assert.deepEqual(expectedAttribute, bp[i].getAttribute(semantic).getArray(), `${a.getName()}: ${semantic}`);
    }
    assert.equal(p.getMaterial()?.getName(), bp[i].getMaterial()?.getName());
    assert.deepEqual(p.getMaterial()?.getBaseColorFactor(), bp[i].getMaterial()?.getBaseColorFactor());
    let expected = Array.from(p.getIndices().getArray());
    if (trimmed) {
      expected = [];
      for (let offset = 0; offset < p.getIndices().getCount(); offset += 3) {
        if (!triangleVertices(a, p, offset).every(v => insideFootprint(v, footprint))) {
          for (let j = 0; j < 3; j++) expected.push(p.getIndices().getScalar(offset + j));
        }
      }
      assert.equal((p.getIndices().getCount() - expected.length) / 3, counts.get(a.getName()));
    }
    assert.deepEqual(Array.from(bp[i].getIndices().getArray()), expected, `${a.getName()}: unexpected triangles changed`);
  });
}
assert.equal(current.getRoot().listNodes().length, old.getRoot().listNodes().length - 2);
for (const node of old.getRoot().listNodes()) {
  const next = current.getRoot().listNodes().find(n => n.getName() === node.getName());
  if (node.getName().startsWith('寒冰馆（500号）')) { assert(!next); continue; }
  compareNode(node, next, counts.has(node.getName()));
}
assert.equal(roads.getRoot().listNodes().length, oldRoads.getRoot().listNodes().length + 1);
for (const node of oldRoads.getRoot().listNodes()) {
  if (ROAD_REPLACEMENTS.some(([name]) => name === node.getName())) {
    assert(!roads.getRoot().listNodes().some(n => n.getName() === node.getName())); continue;
  }
  compareNode(node, roads.getRoot().listNodes().find(n => n.getName() === node.getName()));
}
for (const name of ROAD_REPLACEMENTS.map(([, name]) => name)) {
  compareNode(accepted.getRoot().listNodes().find(n => n.getName() === name), roads.getRoot().listNodes().find(n => n.getName() === name));
}
const apron=roads.getRoot().listNodes().find(n=>n.getName()===APRON);
const sourceApron=accepted.getRoot().listNodes().find(n=>n.getName()===APRON);
assert.deepEqual(apron.getExtras(),sourceApron.getExtras());
const apronBox=getBounds(apron),sourceBox=getBounds(sourceApron);
for(const k of ['min','max'])for(const axis of [0,2])assert(Math.abs(apronBox[k][axis]-sourceBox[k][axis])<.0001);
assert(apronBox.min[1]>=-.086&&apronBox.max[1]<=sourceBox.max[1]+.0001);
const ap=apron.getMesh().listPrimitives()[0],edges=new Map();let area=0;
for(let i=0;i<ap.getIndices().getCount();i+=3){
  const [a,b,c]=triangleVertices(apron,ap,i);
  const signed=(b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]);
  assert(signed>0,'Folded ground triangle');area+=signed/2;
  for(const [j,k] of [[0,1],[1,2],[2,0]]){
    const key=[ap.getIndices().getScalar(i+j),ap.getIndices().getScalar(i+k)].sort((a,b)=>a-b).join(':');
    edges.set(key,(edges.get(key)??0)+1);
  }
}
assert(Math.abs(area-(apronBox.max[0]-apronBox.min[0])*(apronBox.max[2]-apronBox.min[2]))<.001,'Overlapping ground coverage');
for(const [key,count] of edges){
  assert(count===1||count===2,'Non-manifold ground');
  if(count===1){
    const [a,b]=key.split(':').map(Number).map(i=>ap.getAttribute('POSITION').getElement(i,[]));
    const localBounds=ap.getAttribute('POSITION');const lo=localBounds.getMin([]),hi=localBounds.getMax([]);
    assert([0,2].some(axis=>[lo[axis],hi[axis]].some(edge=>Math.abs(a[axis]-edge)<1e-5&&Math.abs(b[axis]-edge)<1e-5)),'Interior crack in ground');
  }
}
// Project road triangles onto the ground and clip against the building envelope.
// A positive intersection area detects roads passing through the building even
// when none of the original triangle vertices lies inside it.
function overlapArea(vertices) {
  let polygon = vertices.map(v => [v[0], v[2]]);
  for (const [axis, value, sign] of [[0,-278.05,1],[0,-238.75,-1],[1,-183.35,1],[1,-168.64,-1]]) {
    const clipped = [];
    for (let i = 0; i < polygon.length; i++) {
      const a = polygon[i], b = polygon[(i + 1) % polygon.length];
      const da = (a[axis] - value) * sign, db = (b[axis] - value) * sign;
      if (da >= 0) clipped.push(a);
      if ((da >= 0) !== (db >= 0)) {
        const t = da / (da - db); clipped.push(a.map((v, j) => v + t * (b[j] - v)));
      }
    }
    polygon = clipped;
  }
  return Math.abs(polygon.reduce((sum, a, i) => {
    const b = polygon[(i + 1) % polygon.length]; return sum + a[0] * b[1] - b[0] * a[1];
  }, 0)) / 2;
}
for (const node of roads.getRoot().listNodes().filter(n => /road|Pedestrian connection/.test(n.getName()))) {
  for (const p of node.getMesh().listPrimitives()) for (let i = 0; i < p.getIndices().getCount(); i += 3) {
    assert(overlapArea(triangleVertices(node, p, i)) < .0001, `${node.getName()}: road still crosses building`);
  }
}
console.log('PASS: old body/roof and 1056 batched detail triangles removed; other historic geometry unchanged; '
  + 'two roads match accepted context; apron has no folded faces/interior cracks; no road crosses the building envelope');
