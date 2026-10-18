/** Scene-aware integration. Accepted v14 files and upstream shared GLBs are read-only. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { NodeIO } from '@gltf-transform/core';
import { simplify, normals, prune, weld } from '@gltf-transform/functions';
import { MeshoptSimplifier } from 'meshoptimizer';
import * as THREE from 'three';
import { repairContext } from './hanbing-context.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const publicDir = path.join(root, 'web/public');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const readJSON = async p => JSON.parse(await fs.readFile(p, 'utf8'));
function decode(bytes) {
  assert.equal(bytes.readUInt32LE(0), 0x46546c67);
  assert.equal(bytes.readUInt32LE(4), 2);
  assert.equal(bytes.readUInt32LE(8), bytes.length);
  assert.equal(bytes.readUInt32LE(16), 0x4e4f534a);
  const end = 20 + bytes.readUInt32LE(12);
  return { json: JSON.parse(bytes.subarray(20, end).toString()), tail: bytes.subarray(end) };
}
function encode({ json, tail }) {
  let content = Buffer.from(JSON.stringify(json));
  content = Buffer.concat([content, Buffer.alloc((4 - content.length % 4) % 4, 32)]);
  const header = Buffer.alloc(20);
  [0x46546c67, 2, 20 + content.length + tail.length, content.length, 0x4e4f534a]
    .forEach((v, i) => header.writeUInt32LE(v, i * 4));
  return Buffer.concat([header, content, tail]);
}
function bounds(g) {
  const box = new THREE.Box3();
  function visit(index, parent) {
    const n = g.nodes[index];
    const local = n.matrix ? new THREE.Matrix4().fromArray(n.matrix) : new THREE.Matrix4().compose(
      new THREE.Vector3(...(n.translation ?? [0, 0, 0])),
      new THREE.Quaternion(...(n.rotation ?? [0, 0, 0, 1])),
      new THREE.Vector3(...(n.scale ?? [1, 1, 1])));
    const world = parent.clone().multiply(local);
    if (n.mesh !== undefined) for (const p of g.meshes[n.mesh].primitives) {
      const a = g.accessors[p.attributes.POSITION];
      box.union(new THREE.Box3(new THREE.Vector3(...a.min), new THREE.Vector3(...a.max)).applyMatrix4(world));
    }
    for (const child of n.children ?? []) visit(child, world);
  }
  for (const index of g.scenes[g.scene ?? 0].nodes) visit(index, new THREE.Matrix4());
  return { min: box.min.toArray(), max: box.max.toArray() };
}
const config = await readJSON(path.join(root, 'assets/protected-buildings.json'));
for (const [relative, expected] of Object.entries(config.files)) {
  let bytes = await fs.readFile(path.join(root, relative));
  if (config.textFiles?.includes(relative)) bytes = Buffer.from(bytes.toString('utf8').replace(/\r\n/g, '\n'));
  assert.equal(hash(bytes), expected, `Protected baseline changed: ${relative}`);
}
const source = config.buildings['42'];
const manifestPath = path.join(publicDir, 'campus-manifest.json');
const manifest = await readJSON(manifestPath);
// Never silently overwrite a manual edit to a previously integrated artifact.
const knownAssets = [...manifest.shared, ...manifest.buildings.flatMap(b => [b, b.overview])];
const outputs = new Map();
async function stage(url, bytes) {
  const target = path.join(publicDir, url);
  try {
    const current = await fs.readFile(target);
    const known = knownAssets.find(a => a.url === url);
    assert(known && hash(current).startsWith(known.revision), `Unreviewed output already exists: ${url}`);
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  outputs.set(url, bytes);
  return { url, revision: hash(bytes).slice(0, 12), bytes: bytes.length };
}

const detail = decode(await fs.readFile(path.join(root, source.source)));
assert.equal(detail.json.scenes.length, 1);
assert(!detail.json.skins && !detail.json.animations && !detail.json.extensionsUsed);
assert(detail.json.nodes.every(n => String(n.extras?.building_id) === '42'));
const originalRoots = [...detail.json.scenes[0].nodes];
detail.json.scenes[0].nodes = [detail.json.nodes.length];
// Counter-translate only the root: every original vertex, normal, material, image,
// node transform and evidence property stays unchanged. The viewer restores position.
detail.json.nodes.push({ name: 'Hanbing42_LocalOrigin', children: originalRoots,
  translation: source.position.map(v => -v), extras: { building_id: '42', source: source.source } });
const detailBytes = encode(detail);
const fullAsset = await stage('models/buildings/42.glb', detailBytes);
const io = new NodeIO();
const overviewDoc = await io.readBinary(detailBytes);
// Far views use material colors and the silhouette. Removing texture seams before
// simplification avoids retaining near-view facade tessellation in the overview.
for (const material of overviewDoc.getRoot().listMaterials()) {
  material.setBaseColorTexture(null).setNormalTexture(null).setOcclusionTexture(null)
    .setMetallicRoughnessTexture(null).setEmissiveTexture(null);
}
for (const mesh of overviewDoc.getRoot().listMeshes()) for (const primitive of mesh.listPrimitives()) {
  for (const semantic of primitive.listSemantics()) if (semantic !== 'POSITION') primitive.setAttribute(semantic, null);
}
await overviewDoc.transform(
  weld(),
  simplify({ simplifier: MeshoptSimplifier, ratio: .12, error: .001 }),
  normals(),
  weld(),
  prune({ keepExtras: true, keepLeaves: true }),
);
const overview = await stage('models/overview/42.glb', Buffer.from(await io.writeBinary(overviewDoc)));
assert(overview.bytes < 4_000_000, `Overview too large: ${overview.bytes}`);

const sharedIndex = manifest.shared.findIndex(a => a.id === '01');
assert(sharedIndex >= 0);
const context = await repairContext(io, publicDir);
const sharedAsset = await stage('models/shared/01-hanbing-v14.glb', context.historic);
manifest.shared[sharedIndex] = { ...manifest.shared[sharedIndex], ...sharedAsset };
const roadsIndex = manifest.shared.findIndex(a => a.id === '00');
assert(roadsIndex >= 0);
manifest.shared[roadsIndex] = { ...manifest.shared[roadsIndex],
  ...await stage('models/shared/00-hanbing-v14.glb', context.roads) };
const labels = await readJSON(path.join(publicDir, 'buildings.json'));
const label = labels.buildings.find(b => b.id === '42');
assert(label);
manifest.buildings = manifest.buildings.filter(b => b.id !== '42');
const localBounds = bounds(detail.json);
manifest.buildings.push({ id: '42', name: label.name, ...fullAsset, overview,
  position: source.position, rotation: [0, 0, 0], orientationBaked: true,
  bounds: localBounds,
  labelPosition: [source.position[0], localBounds.max[1] + 2, source.position[2]],
  loadDistance: 240, source: source.source, editableSource: source.editableSource,
  protected: true });
manifest.buildings.sort((a, b) => Number(a.id) - Number(b.id));
for (const [url, bytes] of outputs) await fs.writeFile(path.join(publicDir, url), bytes);
// Publish the manifest last, after every referenced artifact is complete.
await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
console.log(JSON.stringify({ building: '42', detailBytes: fullAsset.bytes, overviewBytes: overview.bytes,
  position: source.position, bounds: localBounds, context: context.report }, null, 2));
