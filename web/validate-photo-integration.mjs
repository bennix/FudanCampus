import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {NodeIO} from '@gltf-transform/core';
import {fileURLToPath} from 'node:url';
const pub=new URL('./public/',import.meta.url),out=new URL('../field-review/campus-photo-integration/',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(p)),before=read(new URL('manifest-before.json',out)),current=read(new URL('campus-manifest.json',pub)),cleanup=read(new URL('cleanup.json',out)),placements=read(new URL('placement.json',out));
const hash=b=>createHash('sha256').update(b).digest('hex').slice(0,12);
// Building 17 now has its own subsequent photo-refinement validation.
// Keep the original snapshot intact and continue protecting every other module.
assert.deepEqual(current.buildings.map(a=>a.id),before.buildings.map(a=>a.id),'Building membership changed');
assert.deepEqual(current.buildings.filter(a=>a.id!=='17'),before.buildings.filter(a=>a.id!=='17'),'Other building modules changed');
const teaching4=current.buildings.find(a=>a.id==='17'),oldTeaching4=before.buildings.find(a=>a.id==='17');
for(const key of ['position','rotation','orientationBaked','url'])assert.deepEqual(teaching4[key],oldTeaching4[key],`Teaching4 placement changed: ${key}`);
const teaching4Bytes=fs.readFileSync(new URL(teaching4.url,pub));
assert.equal(hash(teaching4Bytes),teaching4.revision);assert.equal(teaching4Bytes.length,teaching4.bytes);
await import('./validate-teaching4.mjs');
for(const a of before.shared){
 const expected=cleanup.find(r=>r.before.url===a.url)?.after??a;
 assert.deepEqual(current.shared.find(b=>b.id===a.id),expected,`Unexpected source change ${a.id}`);
 const b=fs.readFileSync(new URL(a.url,pub));if(!a.url.endsWith('.parts.json'))assert.equal(hash(b),a.revision,'Previous source was overwritten');
}
const io=new NodeIO();
for(const key of ['xiyuan','yeyaozhen','teaching3']){
 const a=current.shared.find(a=>a.id==='photo-'+key);assert(a);const bytes=fs.readFileSync(new URL(a.url,pub));assert.equal(hash(bytes),a.revision);assert.equal(bytes.length,a.bytes);
 const doc=await io.read(fileURLToPath(new URL(a.url,pub)));const nodes=doc.getRoot().listNodes();assert(nodes.some(n=>n.getMesh()));
 assert(!nodes.some(n=>n.getName().includes('annex exterior stairs')||n.getName().includes('annex stair rail')));
 if(key==='teaching3'){
  const sphere=nodes.find(n=>n.getName().replaceAll('_',' ')==='metal sphere sculpture');assert(sphere,'Metal sphere missing');
  const p=sphere.getMesh().listPrimitives()[0].getAttribute('POSITION');const lo=p.getMin([]),hi=p.getMax([]);const d=lo.map((v,i)=>hi[i]-v);assert(Math.max(...d)-Math.min(...d)<.0001,`Sculpture flattened: ${d}`);
  assert(Math.abs((lo[0]+hi[0])/2-30.4)<.01);assert(Math.abs((lo[2]+hi[2])/2+94.7)<.01);
 }
}
for(const id of ['00','02']){
 const a=current.shared.find(a=>a.id===id),doc=await io.read(fileURLToPath(new URL(a.url,pub)));
 assert(!doc.getRoot().listNodes().some(n=>['60','75'].includes(String(n.getExtras().building_id))||n.getName().includes('曦园')),'Old placeholder remains');
}
assert.deepEqual(placements.map(a=>a.key).sort(),['teaching3','xiyuan','yeyaozhen']);
console.log('PASS: three photo studies placed; other original modules/sources preserved; teaching4 independently verified; old placeholders removed; sphere is round; rejected stair absent');
