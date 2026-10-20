import fs from 'node:fs';
import assert from 'node:assert/strict';
const pub=new URL('./public/',import.meta.url);
function read(url){const b=fs.readFileSync(new URL(url,pub));const end=20+b.readUInt32LE(12);return {g:JSON.parse(b.subarray(20,end)),bin:b.subarray(end+8)};}
const original=read('models/shared/02.glb'),current=read('models/shared/02-teaching4.glb');
assert.deepEqual(current.bin.subarray(0,original.bin.length),original.bin,'Original vertex and material buffers changed');
for(const key of ['materials','meshes','images','textures']){
 if(key!=='meshes')assert.deepEqual(current.g[key],original.g[key],key);
}
function values(model,index){const a=model.g.accessors[index],v=model.g.bufferViews[a.bufferView];const size={5123:2,5125:4,5126:4}[a.componentType],width=a.type==='VEC3'?3:1;
 const read={5123:'readUInt16LE',5125:'readUInt32LE',5126:'readFloatLE'}[a.componentType];
 return Array.from({length:a.count},(_,i)=>Array.from({length:width},(_,j)=>model.bin[read]((v.byteOffset??0)+(a.byteOffset??0)+i*(v.byteStride??size*width)+j*size)));}
const inside=p=>p[0]>=-175.3&&p[0]<=-133.5&&p[1]>=-.05&&p[1]<=13.1&&p[2]>=-211.3&&p[2]<=-195.7;
let removed=0;
for(const node of original.g.nodes){
 if(String(node.extras?.building_id)==='17'){assert(!current.g.nodes.some(n=>n.name===node.name));continue;}
 assert.deepEqual(current.g.nodes.find(n=>n.name===node.name),node,'Other node changed');
 if(node.mesh==null)continue;
 const a=original.g.meshes[node.mesh],b=current.g.meshes[node.mesh];assert.equal(a.primitives.length,b.primitives.length);
 for(let j=0;j<a.primitives.length;j++){
  const p=a.primitives[j],q=b.primitives[j];assert.deepEqual({...q,indices:p.indices},p);
  const indices=values(original,p.indices).flat(),positions=values(original,p.attributes.POSITION),expected=[];
  for(let k=0;k<indices.length;k+=3){const tri=indices.slice(k,k+3);if(node.extras?.building_id==null&&tri.every(i=>inside(positions[i])))removed++;else expected.push(...tri);}
  assert.deepEqual(values(current,q.indices).flat(),expected,`Non-target triangles changed: ${node.name}`);
 }
}
assert.equal(removed,2630);
const m=JSON.parse(fs.readFileSync(new URL('campus-manifest.json',pub))),a=m.buildings.find(b=>b.id==='17');
assert.deepEqual(a.position,[-154.4,0,-204]);assert(['models/shared/02-teaching4.glb','models/shared/02-teaching4-photo.glb'].includes(m.shared.find(a=>a.id==='02').url));
const model=read(a.url);for(const word of ['six storey','balcony','rear stair','flowerbed','book','clock','lettering'])assert(model.g.nodes.some(n=>n.name.includes(word)),`Missing ${word}`);
console.log('PASS: teaching4 six-storey facade, garden, books and clock present; 2630 old detail triangles removed; all other district triangles and source buffers unchanged');
