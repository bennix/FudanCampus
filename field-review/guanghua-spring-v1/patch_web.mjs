import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {NodeIO} from '../../.local/model-tools/node_modules/@gltf-transform/core/dist/index.js';
import {ALL_EXTENSIONS} from '../../.local/model-tools/node_modules/@gltf-transform/extensions/dist/index.js';
import {MeshoptEncoder,MeshoptDecoder} from '../../.local/model-tools/node_modules/meshoptimizer/index.js';
import {Matrix4,Vector3} from '../../web/node_modules/three/build/three.module.js';
const out=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(out,'../..'),pub=path.join(root,'web/public');
const sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const native=JSON.parse(fs.readFileSync(path.join(out,'native-validation.json'))),base=path.join(pub,'models/landscape/guanghua-closeout.glb'),baselineHash=sha(base);
const manifestPath=path.join(pub,'campus-manifest.json'),manifest=JSON.parse(fs.readFileSync(manifestPath));
if(!fs.existsSync(path.join(out,'campus-manifest-before.json')))fs.writeFileSync(path.join(out,'campus-manifest-before.json'),JSON.stringify(manifest,null,2));
await Promise.all([MeshoptEncoder.ready,MeshoptDecoder.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
const doc=await io.read(base),buffer=doc.getRoot().listBuffers()[0],changes=[];
const tex=doc.createTexture('Spring cherry blossom cluster').setImage(fs.readFileSync(path.join(out,'spring-blossom-atlas.png'))).setMimeType('image/png');
const blossom=doc.createMaterial('Spring cherry pale pink-white blossom clusters').setBaseColorTexture(tex).setBaseColorFactor([1,1,1,1]).setAlphaMode('MASK').setAlphaCutoff(.32).setDoubleSided(true).setRoughnessFactor(.8).setMetallicFactor(0);
const whitewash=doc.createMaterial('Spring cherry whitewashed lower trunk').setBaseColorFactor([.72,.72,.67,1]).setRoughnessFactor(.96).setMetallicFactor(0);
let lods=0,whiteTriangles=0,heartVertices=0;
const target='V6 East spreading 01';
for(const node of doc.getRoot().listNodes()){
 const extras=node.getExtras(),mesh=node.getMesh();if(!mesh)continue;
 if(extras.source_object===target+' leaves'){
  const copy=doc.createMesh(mesh.getName()+' spring full bloom');
  for(const p of mesh.listPrimitives()){
   const a=p.getAttribute('POSITION'),ix=p.getIndices(),parents=Int32Array.from({length:a.getCount()},(_,i)=>i),used=new Set();
   const find=x=>{while(parents[x]!==x){parents[x]=parents[parents[x]];x=parents[x];}return x;};
   for(let i=0;i<ix.getCount();i+=3){const ids=[ix.getScalar(i),ix.getScalar(i+1),ix.getScalar(i+2)];for(const id of ids)used.add(id);parents[find(ids[1])]=find(ids[0]);parents[find(ids[2])]=find(ids[0]);}
   const cards=new Map();for(const id of used){const key=find(id),ids=cards.get(key)||[];ids.push(id);cards.set(key,ids);}
   const data=new Float32Array(a.getCount()*3),v=[];for(let i=0;i<a.getCount();i++)data.set(a.getElement(i,v),i*3);
   console.log('Blossom card topology',extras.closeout_lod,JSON.stringify([...cards.values()].reduce((counts,ids)=>{counts[ids.length]=(counts[ids.length]||0)+1;return counts;},{})));
   for(const ids of cards.values()){assert([3,4].includes(ids.length),'Expected independent complete blossom cards');const c=[0,0,0];for(const id of ids)for(let j=0;j<3;j++)c[j]+=data[id*3+j]/ids.length;for(const id of ids)for(let j=0;j<3;j++)data[id*3+j]=c[j]+(data[id*3+j]-c[j])*1.38;}
   const position=doc.createAccessor('Full bloom card positions',buffer).setType('VEC3').setArray(data);
   copy.addPrimitive(p.clone().setAttribute('POSITION',position).setMaterial(blossom));
  }
  node.setMesh(copy).setExtras({...extras,season:'spring full bloom',blossom_spray_scale:1.38,reference:'reference-spring-cherry.jpg',source_sha256:native.source_sha256});lods++;changes.push(node.getName());
 }
 if(extras.feature_id==='SIGN'&&extras.sources?.includes('SIGN__continuous-heart__FIN_red')){
  const matrix=new Matrix4().fromArray(node.getWorldMatrix()),inv=matrix.clone().invert(),origin=new Vector3(0,0,0).applyMatrix4(inv),delta=new Vector3(0,0,-.32*2/3).applyMatrix4(inv).sub(origin);
  for(const p of mesh.listPrimitives())if(p.getMaterial()?.getName()==='WEB FIN_red'){
   const a=p.getAttribute('POSITION'),data=new Float32Array(a.getCount()*3),v=[];for(let i=0;i<a.getCount();i++){a.getElement(i,v);data.set([v[0]+delta.x,v[1]+delta.y,v[2]+delta.z],i*3);}p.setAttribute('POSITION',doc.createAccessor('Heart behind chair position',buffer).setType('VEC3').setArray(data));heartVertices+=a.getCount();
  }node.setExtras({...extras,heart_translation_blender:[0,.32,0],heart_clearance_web:native.heart_clearance_web});changes.push(node.getName());
 }
 if(extras.feature_id==='TREE_CANOPY_V6'&&extras.sources?.includes(target+' wood')){
  const matrix=new Matrix4().fromArray(node.getWorldMatrix());
  for(const p of [...mesh.listPrimitives()]){
   const a=p.getAttribute('POSITION'),ix=p.getIndices(),keep=[],paint=[],v=[];
   for(let i=0;i<ix.getCount();i+=3){let center=new Vector3();const ids=[ix.getScalar(i),ix.getScalar(i+1),ix.getScalar(i+2)];for(const id of ids){a.getElement(id,v);center.add(new Vector3(...v).applyMatrix4(matrix));}center.multiplyScalar(1/3);
    const isBase=Math.hypot(center.x-163.133336385,center.z+153.800003052)<.55&&center.y<1.025&&center.y>-.04;(isBase?paint:keep).push(...ids);
   }
   if(paint.length){const newIndices=arr=>doc.createAccessor('Cherry trunk indices',buffer).setType('SCALAR').setArray(new Uint32Array(arr));p.setIndices(newIndices(keep));mesh.addPrimitive(p.clone().setIndices(newIndices(paint)).setMaterial(whitewash));whiteTriangles+=paint.length/3;}
  }node.setExtras({...extras,spring_whitewash_target:target});changes.push(node.getName());
 }
}
console.log('Changed target counts',JSON.stringify({lods,whiteTriangles,heartVertices}));
assert.equal(lods,3);assert(whiteTriangles>=8);assert(heartVertices>100);
const dest=path.join(pub,'models/landscape/guanghua-spring-full-bloom.glb');await io.write(dest,doc);assert.equal(sha(base),baselineHash);
const asset=manifest.shared.find(a=>a.id==='guanghua-landscape');asset.url='models/landscape/guanghua-spring-full-bloom.glb';asset.revision=sha(dest).slice(0,12);asset.bytes=fs.statSync(dest).size;asset.name='Guanghua full spring blossom and corrected heart chair';asset.closeoutReport='field-review/guanghua-spring-v1/integration.json';
const old=JSON.parse(fs.readFileSync(path.join(root,'field-review/guanghua-refinement-v4/closeout-final/integration.json')));
const report={...old,source:native.source,source_sha256:native.source_sha256,landscape:{url:asset.url,revision:asset.revision,bytes:asset.bytes},derivation:{baseline_glb:'models/landscape/guanghua-closeout.glb',baseline_glb_sha256:baselineHash,baseline_native_sha256:native.baseline_sha256,changed_nodes:changes,flower_lods:lods,whitewash_triangles:whiteTriangles,heart_vertices:heartVertices,heart_clearance_web:native.heart_clearance_web,method:'Scene-aware incremental GLB derivative; untouched accessor arrays and transforms preserved'},validation_status:'Local seasonal derivative awaiting browser review'};
assert(asset.bytes+report.building.bytes+report.vegetation_reused.bytes<=150*1024*1024);
fs.writeFileSync(path.join(out,'integration.json'),JSON.stringify(report,null,2));fs.writeFileSync(manifestPath,JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({asset,flower_lods:lods,whitewash_triangles:whiteTriangles,heart_vertices:heartVertices,heart_clearance_web:native.heart_clearance_web}));
