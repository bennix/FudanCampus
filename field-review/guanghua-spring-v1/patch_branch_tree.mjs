import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {NodeIO} from '../../.local/model-tools/node_modules/@gltf-transform/core/dist/index.js';
import {ALL_EXTENSIONS} from '../../.local/model-tools/node_modules/@gltf-transform/extensions/dist/index.js';
import {mergeDocuments} from '../../.local/model-tools/node_modules/@gltf-transform/functions/dist/index.js';
import {MeshoptEncoder,MeshoptDecoder} from '../../.local/model-tools/node_modules/meshoptimizer/index.js';
import {Matrix4,Vector3} from '../../web/node_modules/three/build/three.module.js';
const out=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(out,'../..'),pub=path.join(root,'web/public');
const sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const native=JSON.parse(fs.readFileSync(path.join(out,'native-validation.json'))),removal=JSON.parse(fs.readFileSync(path.join(out,'wood-batch-removal.json')));
const base=path.join(pub,'models/landscape/guanghua-closeout.glb'),baseSha=sha(base),manifestPath=path.join(pub,'campus-manifest.json');
await Promise.all([MeshoptEncoder.ready,MeshoptDecoder.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
const doc=await io.read(base),part=await io.read(path.join(out,'cherry-replacement-native.glb'));
assert.equal(part.getRoot().listNodes().filter(n=>n.getMesh()).length,2,'Only the target tree may be imported');
const partWood=part.getRoot().listNodes().find(n=>n.getExtras().source_object===native.target_tree+' wood');
const partFlowers=part.getRoot().listNodes().find(n=>n.getExtras().source_object===native.target_tree+' leaves');
assert(partWood&&partFlowers);
const matrix=n=>new Matrix4().makeTranslation(117.86666870117188,0,-122.80000305175781).multiply(new Matrix4().makeScale(2/3,2/3,2/3)).multiply(new Matrix4().fromArray(n.getWorldMatrix()));
const woodMatrix=matrix(partWood),flowersMatrix=matrix(partFlowers),map=mergeDocuments(doc,part),mainScene=doc.getRoot().listScenes()[0];
const importedWood=map.get(partWood),importedFlowers=map.get(partFlowers);
for(const s of part.getRoot().listScenes())map.get(s).dispose();
const buffer=doc.getRoot().listBuffers()[0],tex=doc.createTexture('Cherry blossom spray atlas').setImage(fs.readFileSync(path.join(out,'spring-blossom-atlas.png'))).setMimeType('image/png');
const factors={'Cherry blossoms ivory':[.98,.96,.94,1],'Cherry blossoms blush':[.98,.84,.88,1],'Cherry blossoms rose shadow':[.85,.65,.72,1]};
for(const p of importedFlowers.getMesh().listPrimitives()){
 const name=p.getMaterial().getName();assert(factors[name],name);
 p.setMaterial(doc.createMaterial(name+' web').setBaseColorFactor(factors[name]).setBaseColorTexture(tex).setRoughnessFactor(.67).setAlphaMode('MASK').setAlphaCutoff(.4).setDoubleSided(true));
}
let removedTriangles=0,lods=0,heartVertices=0;
for(const node of [...doc.getRoot().listNodes()]){
 const mesh=node.getMesh(),extras=node.getExtras();if(!mesh||node===importedWood||node===importedFlowers)continue;
 if(node.getName()===removal.node){
  mesh.listPrimitives().forEach((p,j)=>{const ix=p.getIndices(),data=[],entry=removal.primitives[j];assert.equal(entry.keep.length+entry.remove.length,ix.getCount()/3);for(const i of entry.keep)for(let k=0;k<3;k++)data.push(ix.getScalar(i*3+k));p.setIndices(doc.createAccessor('Retained neighboring tree wood',buffer).setType('SCALAR').setArray(new Uint32Array(data)));removedTriangles+=entry.remove.length;});
  const sources=extras.sources.split('; ').filter(n=>n!==native.target_tree+' wood');node.setExtras({...extras,sources:sources.join('; '),source_object_count:sources.length,removed_source:native.target_tree+' wood'});
 }
 if(extras.source_object===native.target_tree+' leaves'){
  const level=extras.closeout_lod,step=level==='near'?1:level==='middle'?2:3,copy=doc.createMesh('Cherry blossom sprays '+level);
  for(const p of importedFlowers.getMesh().listPrimitives()){
   const ix=p.getIndices(),data=[];assert.equal(ix.getCount()%6,0,'Independent source blossom quads');
   for(let i=0;i<ix.getCount();i+=6)if((i/6)%step===0)for(let k=0;k<6;k++)data.push(ix.getScalar(i+k));
   copy.addPrimitive(p.clone().setIndices(doc.createAccessor('Cherry '+level+' blossom indices',buffer).setType('SCALAR').setArray(new Uint32Array(data))));
  }
  let local=flowersMatrix.clone();const parent=node.getParentNode();if(parent)local.premultiply(new Matrix4().fromArray(parent.getWorldMatrix()).invert());
  node.setMesh(copy).setMatrix(local.elements).setExtras({...extras,season:'spring branch-led bloom',source_sha256:native.source_sha256,reference:'reference-spring-cherry.jpg',twig_anchor_sites:native.twig_anchor_sites});lods++;
 }
 if(extras.feature_id==='SIGN'&&extras.sources?.includes('SIGN__continuous-heart__FIN_red')){
  const inv=new Matrix4().fromArray(node.getWorldMatrix()).invert(),delta=new Vector3(0,0,-.32*2/3).applyMatrix4(inv).sub(new Vector3().applyMatrix4(inv));
  for(const p of mesh.listPrimitives())if(p.getMaterial()?.getName()==='WEB FIN_red'){
   const a=p.getAttribute('POSITION'),data=new Float32Array(a.getCount()*3),v=[];for(let i=0;i<a.getCount();i++){a.getElement(i,v);data.set([v[0]+delta.x,v[1]+delta.y,v[2]+delta.z],i*3);}p.setAttribute('POSITION',doc.createAccessor('Heart behind chair position',buffer).setType('VEC3').setArray(data));heartVertices+=a.getCount();
  }
  node.setExtras({...extras,heart_translation_blender:[0,.32,0],heart_clearance_web:native.heart_clearance_web});
 }
}
mainScene.addChild(importedWood);importedWood.setMatrix(woodMatrix.elements).setName('Spring cherry aged branching skeleton').setExtras({...importedWood.getExtras(),closeout_lod:'static',source_sha256:native.source_sha256,campusVegetation:true});
importedFlowers.dispose();assert.equal(lods,3);assert.equal(removedTriangles,native.wood_batch_owner_counts[native.target_tree+' wood']);assert(heartVertices>100);assert.equal(sha(base),baseSha);
for(const a of doc.getRoot().listAccessors())a.setBuffer(buffer);
for(const b of doc.getRoot().listBuffers().slice(1))b.dispose();
const dest=path.join(pub,'models/landscape/guanghua-spring-branch-led-v2.glb');await io.write(dest,doc);
const manifest=JSON.parse(fs.readFileSync(manifestPath)),asset=manifest.shared.find(a=>a.id==='guanghua-landscape');
asset.url='models/landscape/guanghua-spring-branch-led-v2.glb';asset.revision=sha(dest).slice(0,12);asset.bytes=fs.statSync(dest).size;asset.name='Guanghua branch-led spring cherry and corrected heart chair';asset.closeoutReport='field-review/guanghua-spring-v1/integration.json';
const old=JSON.parse(fs.readFileSync(path.join(root,'field-review/guanghua-refinement-v4/closeout-final/integration.json')));
const report={...old,source:native.source,source_sha256:native.source_sha256,landscape:{url:asset.url,revision:asset.revision,bytes:asset.bytes},derivation:{baseline_glb:'models/landscape/guanghua-closeout.glb',baseline_glb_sha256:baseSha,baseline_native_sha256:native.baseline_sha256,target_tree:native.target_tree,flower_lods:lods,old_wood_triangles_removed:removedTriangles,old_wood_surface_assignment_ambiguities:native.wood_batch_ambiguities,heart_clearance_web:native.heart_clearance_web,blossom_anchor_sites:native.twig_anchor_sites,method:'Replace target tree meshes; preserve other source accessor arrays and transforms; source-surface attribution removes old wood from shared batch'},validation_status:'Local branch-led derivative awaiting visual review'};
assert(asset.bytes+report.building.bytes+report.vegetation_reused.bytes<=150*1024*1024);
fs.writeFileSync(path.join(out,'integration.json'),JSON.stringify(report,null,2));fs.writeFileSync(manifestPath,JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({asset,removedTriangles,lods,heartVertices,source:native.source}));
