import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {MeshoptDecoder,MeshoptEncoder} from 'meshoptimizer';
const pub=new URL('./public/',import.meta.url),out=new URL('../field-review/campus-photo-integration/',import.meta.url);
await Promise.all([MeshoptDecoder.ready,MeshoptEncoder.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder,'meshopt.encoder':MeshoptEncoder});
const manifest=JSON.parse(fs.readFileSync(new URL('manifest-before.json',out))),lod=JSON.parse(fs.readFileSync(new URL('lod-before.json',out))),report=[];
// Refuse to reset later campus work to this batch's fixed baseline.
const live=JSON.parse(fs.readFileSync(new URL('campus-manifest.json',pub)));
const priorPath=new URL('cleanup.json',out),prior=fs.existsSync(priorPath)?JSON.parse(fs.readFileSync(priorPath)):[];
if(JSON.stringify(live.buildings)!==JSON.stringify(manifest.buildings))throw Error('Campus building modules changed since photo baseline; merge before rerunning');
for(const a of live.shared.filter(a=>!a.id.startsWith('photo-'))){const b=manifest.shared.find(b=>b.id===a.id);if(!b||!(a.revision===b.revision||prior.some(r=>r.after.revision===a.revision)))throw Error('Campus shared asset changed: '+a.id);}
const regions=[[-8,53,78,118],[5,43,16,50],[59,86,11,29]];
const inside=(x,y,z,r)=>x>=r[0]&&x<=r[1]&&-z>=r[2]&&-z<=r[3];
const oldBuildings=[[-9,52,101,116],[63,83,9,26]];
async function clean(t,kind){
 const doc=await io.read(new URL(t.url,pub).pathname);let removed=0,nodes=0;
 for(const n of [...doc.getRoot().listNodes()]){
  const name=n.getName(),bid=String(n.getExtras().building_id??'');
  if((kind==='02'&&['60','75'].includes(bid))||(kind==='00'&&name.includes('曦园'))){n.dispose();nodes++;continue;}
  const mesh=n.getMesh();if(!mesh)continue;
  if(kind==='02'&&bid)continue;
  if(kind==='00')continue;
  for(const p of mesh.listPrimitives()){
   const pos=p.getAttribute('POSITION'),ix=p.getIndices();if(!pos||!ix)continue;
   const arr=ix.getArray(),kept=[],v=[0,0,0];
   for(let i=0;i<arr.length;i+=3){
    const matrix=n.getWorldMatrix();
    const verts=[0,1,2].map(j=>{const v=pos.getElement(arr[i+j],[0,0,0]);return [0,1,2].map(k=>matrix[k]*v[0]+matrix[k+4]*v[1]+matrix[k+8]*v[2]+matrix[k+12]);});
    const drop=kind==='02'?oldBuildings.some(r=>verts.every(v=>inside(...v,r))):regions.some(r=>inside(...[0,1,2].map(k=>verts.reduce((s,v)=>s+v[k],0)/3),r));
    if(drop)removed++;else kept.push(arr[i],arr[i+1],arr[i+2]);
   }
   if(kept.length!==arr.length){if(!kept.length)mesh.removePrimitive(p);else p.setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint32Array(kept)).setBuffer(ix.getBuffer()));}
  }
  if(!mesh.listPrimitives().length)n.dispose();
 }
 if(!removed&&!nodes)return t;
 const url=t.url.replace(/\.glb$/,'-photo.glb'),bytes=await io.writeBinary(doc);fs.writeFileSync(new URL(url,pub),bytes);
 const g=JSON.parse(Buffer.from(bytes).subarray(20,20+new DataView(bytes.buffer,bytes.byteOffset).getUint32(12,true)));
 const triangles=g.nodes.filter(n=>n.mesh!==undefined).reduce((s,n)=>s+g.meshes[n.mesh].primitives.reduce((s,p)=>s+g.accessors[p.indices].count/3,0),0);
 const result={...t,url,bytes:bytes.length,revision:createHash('sha256').update(bytes).digest('hex').slice(0,12)};if('triangles'in t)result.triangles=triangles;
 report.push({before:t,after:result,removedTriangles:removed,removedNodes:nodes});return result;
}
for(const id of ['00','02','05']){
 const i=manifest.shared.findIndex(a=>a.id===id);manifest.shared[i]=await clean(manifest.shared[i],id);
 for(const a of lod.assets.filter(a=>(a.sourceId??a.id)==='shared-'+id)){
  for(let j=0;j<3;j++)a.tiers[j]=await clean(a.tiers[j],id);
  a.sourceRevision=manifest.shared[i].revision;
 }
}
fs.writeFileSync(new URL('campus-manifest.json',pub),JSON.stringify(manifest,null,2)+'\n');
fs.writeFileSync(new URL('campus-lod.json',pub),JSON.stringify(lod,null,2)+'\n');
fs.writeFileSync(new URL('cleanup.json',out),JSON.stringify(report,null,2)+'\n');console.log('CLEANED',report.length,'resources');
