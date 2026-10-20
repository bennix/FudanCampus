import fs from 'node:fs';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
const pub=new URL('./public/',import.meta.url),read=p=>JSON.parse(fs.readFileSync(new URL(p,pub)));
const meta=read('walk-collision.json'),lod=read('campus-lod.json'),bytes=fs.readFileSync(new URL('walk-collision.bin',pub));
assert.deepEqual(meta.sourceRevisions,lod.assets.map(a=>[a.id,a.tiers[0].revision]),'Collision data is stale; rebuild before deployment');assert.equal(bytes.length,meta.bytes);assert.equal(bytes.length,meta.triangles*36);assert.equal(createHash('sha256').update(bytes).digest('hex'),meta.sha256);
const polygons=read('walk-interiors.json');assert(polygons.length>100);assert(polygons.some(p=>p.rings.length>1),'Courtyard holes missing');for(const p of polygons){assert(p.bounds.every(Number.isFinite));assert(p.rings.every(r=>r.length>=4&&r.every(v=>v.every(Number.isFinite))));}
console.log('PASS: fixed walk collision, source freshness, binary hash and sealed interiors with courtyard holes');
