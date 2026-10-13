import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {NodeIO} from '../../.local/model-tools/node_modules/@gltf-transform/core/dist/index.js';
import {ALL_EXTENSIONS} from '../../.local/model-tools/node_modules/@gltf-transform/extensions/dist/index.js';
import {mergeDocuments} from '../../.local/model-tools/node_modules/@gltf-transform/functions/dist/index.js';
import {MeshoptEncoder,MeshoptDecoder} from '../../.local/model-tools/node_modules/meshoptimizer/index.js';
import {Matrix4} from '../../web/node_modules/three/build/three.module.js';
const out=path.dirname(fileURLToPath(import.meta.url)),pub=path.resolve(out,'../../web/public');
const hash=x=>createHash('sha256').update(x).digest('hex'),sha=p=>hash(fs.readFileSync(p));
const native=JSON.parse(fs.readFileSync(path.join(out,'photo-v3-native-validation.json')));
const manifestPath=path.join(pub,'campus-manifest.json');
const current=JSON.parse(fs.readFileSync(manifestPath));
const before=current.shared.find(a=>a.id==='guanghua-landscape').url==='models/landscape/guanghua-spring-photo-v3.glb'?JSON.parse(fs.readFileSync(path.join(out,'photo-v3-manifest-before.json'))):current;
const asset=before.shared.find(a=>a.id==='guanghua-landscape');
assert.equal(asset.url,'models/landscape/guanghua-spring-branch-led-v2.glb');
const base=path.join(pub,asset.url),baseSha=sha(base);
await Promise.all([MeshoptEncoder.ready,MeshoptDecoder.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
const doc=await io.read(base),part=await io.read(path.join(out,'cherry-photo-v3-native.glb'));
const target=n=>n.getExtras().source_object===native.target_tree+' leaves'||n.getExtras().source_object===native.target_tree+' wood';
function fingerprints(d){
 const result={};
 for(const n of d.getRoot().listNodes()){
  if(target(n))continue;
  const h=createHash('sha256');h.update(JSON.stringify({name:n.getName(),matrix:n.getMatrix(),extras:n.getExtras(),children:n.listChildren().map(x=>x.getName())}));
  for(const p of n.getMesh()?.listPrimitives()??[]){
   h.update(JSON.stringify({mode:p.getMode(),material:p.getMaterial()?.getName()}));
   for(const semantic of p.listSemantics()){const a=p.getAttribute(semantic);h.update(semantic);h.update(Buffer.from(a.getArray().buffer,a.getArray().byteOffset,a.getArray().byteLength));}
   const a=p.getIndices();if(a)h.update(Buffer.from(a.getArray().buffer,a.getArray().byteOffset,a.getArray().byteLength));
   const m=p.getMaterial();if(m){h.update(JSON.stringify({color:m.getBaseColorFactor(),rough:m.getRoughnessFactor(),metal:m.getMetallicFactor(),alpha:m.getAlphaMode(),cutoff:m.getAlphaCutoff(),double:m.getDoubleSided(),emissive:m.getEmissiveFactor()}));for(const t of [m.getBaseColorTexture(),m.getNormalTexture(),m.getEmissiveTexture(),m.getOcclusionTexture(),m.getMetallicRoughnessTexture()])if(t?.getImage())h.update(t.getImage());}
  }
  assert(!result[n.getName()],'Duplicate node name');result[n.getName()]=h.digest('hex');
 }
 return result;
}
const protectedBefore=fingerprints(doc);
const oldWood=doc.getRoot().listNodes().find(n=>n.getExtras().source_object===native.target_tree+' wood');
const lods=doc.getRoot().listNodes().filter(n=>n.getExtras().source_object===native.target_tree+' leaves');
assert(oldWood);assert.equal(lods.length,3);
const partWood=part.getRoot().listNodes().find(n=>n.getExtras().source_object===native.target_tree+' wood');
const partFlowers=part.getRoot().listNodes().find(n=>n.getExtras().source_object===native.target_tree+' leaves');
assert(partWood&&partFlowers);assert.equal(part.getRoot().listNodes().filter(n=>n.getMesh()).length,2);
const world=n=>new Matrix4().makeTranslation(117.86666870117188,0,-122.80000305175781).multiply(new Matrix4().makeScale(2/3,2/3,2/3)).multiply(new Matrix4().fromArray(n.getWorldMatrix()));
const flowerWorld=world(partFlowers),map=mergeDocuments(doc,part),importedWood=map.get(partWood),importedFlowers=map.get(partFlowers);
for(const s of part.getRoot().listScenes())map.get(s).dispose();
oldWood.setMesh(importedWood.getMesh()).setExtras({...oldWood.getExtras(),source_sha256:native.source_sha256,photo_revision:'v3 broad crown and dense terminal blossom sprays'});
const buffer=doc.getRoot().listBuffers()[0],tex=doc.createTexture('Photo v3 cherry blossom atlas').setImage(fs.readFileSync(path.join(out,'spring-blossom-atlas.png'))).setMimeType('image/png');
const factors={'Cherry blossoms ivory':[1,.98,.97,1],'Cherry blossoms blush':[1,.91,.94,1],'Cherry blossoms rose shadow':[.92,.80,.84,1]};
for(const p of importedFlowers.getMesh().listPrimitives()){
 const key=p.getMaterial().getName().replace(/\.\d+$/,'');assert(factors[key],key);
 p.setMaterial(doc.createMaterial(key+' photo v3 web').setBaseColorFactor(factors[key]).setBaseColorTexture(tex).setMetallicFactor(0).setRoughnessFactor(.72).setAlphaMode('MASK').setAlphaCutoff(.30).setDoubleSided(true));
}
for(const node of lods){
 const level=node.getExtras().closeout_lod,step=level==='near'?1:level==='middle'?2:3,mesh=doc.createMesh('Photo v3 cherry flowers '+level);
 for(const p of importedFlowers.getMesh().listPrimitives()){
  const ix=p.getIndices(),data=[];assert.equal(ix.getCount()%6,0);
  for(let i=0;i<ix.getCount();i+=6)if((i/6)%step===0)for(let k=0;k<6;k++)data.push(ix.getScalar(i+k));
  mesh.addPrimitive(p.clone().setIndices(doc.createAccessor('Photo v3 '+level+' indices',buffer).setType('SCALAR').setArray(new Uint32Array(data))));
 }
 let local=flowerWorld.clone();const parent=node.getParentNode();if(parent)local.premultiply(new Matrix4().fromArray(parent.getWorldMatrix()).invert());
 node.setMesh(mesh).setMatrix(local.elements).setExtras({...node.getExtras(),source_sha256:native.source_sha256,twig_anchor_sites:native.twig_anchor_sites,photo_revision:'v3'});
}
importedWood.dispose();importedFlowers.dispose();
assert.deepEqual(fingerprints(doc),protectedBefore,'Non-target GLB changed');
for(const a of doc.getRoot().listAccessors())a.setBuffer(buffer);for(const b of doc.getRoot().listBuffers().slice(1))b.dispose();
const relative='models/landscape/guanghua-spring-photo-v3.glb',dest=path.join(pub,relative);await io.write(dest,doc);
const reopened=await io.read(dest);assert.deepEqual(fingerprints(reopened),protectedBefore,'Saved GLB changed neighboring scene');assert.equal(sha(base),baseSha);
const manifest=JSON.parse(JSON.stringify(before)),updated=manifest.shared.find(a=>a.id==='guanghua-landscape');
updated.url=relative;updated.revision=sha(dest).slice(0,12);updated.bytes=fs.statSync(dest).size;updated.closeoutReport='field-review/guanghua-spring-v1/photo-v3-integration.json';
for(let i=0;i<manifest.shared.length;i++)if(manifest.shared[i].id!=='guanghua-landscape')assert.deepEqual(manifest.shared[i],before.shared[i]);assert.deepEqual(manifest.buildings,before.buildings);
const old=JSON.parse(fs.readFileSync(path.join(out,'integration.json')));
const report={...old,source:native.source,source_sha256:native.source_sha256,landscape:{url:updated.url,revision:updated.revision,bytes:updated.bytes},derivation:{baseline_glb:asset.url,baseline_glb_sha256:baseSha,target_tree:native.target_tree,non_target_glb_nodes_preserved:Object.keys(protectedBefore).length,non_target_native_meshes_preserved:native.non_target_meshes_preserved,branch_paths:native.branch_paths,blossom_cards:native.blossom_cards,blossom_anchor_sites:native.twig_anchor_sites,neighbor_geometry_materials_transforms_preserved:true,all_other_manifest_entries_preserved:true},validation_status:'Tree-only photo revision, awaiting browser visual review'};
fs.writeFileSync(path.join(out,'photo-v3-manifest-before.json'),JSON.stringify(before,null,2));fs.writeFileSync(path.join(out,'photo-v3-integration.json'),JSON.stringify(report,null,2));fs.writeFileSync(manifestPath,JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({asset:updated,protectedNodes:Object.keys(protectedBefore).length,branches:native.branch_paths,blossomCards:native.blossom_cards}));
