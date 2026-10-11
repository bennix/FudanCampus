import {NodeIO} from '../../../.local/model-tools/node_modules/@gltf-transform/core/dist/index.js';
import {ALL_EXTENSIONS} from '../../../.local/model-tools/node_modules/@gltf-transform/extensions/dist/index.js';
import {dedup,prune,meshopt} from '../../../.local/model-tools/node_modules/@gltf-transform/functions/dist/index.js';
import {MeshoptEncoder,MeshoptDecoder} from '../../../.local/model-tools/node_modules/meshoptimizer/index.js';
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {createHash} from 'node:crypto';
const out=path.dirname(fileURLToPath(import.meta.url));await MeshoptEncoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
const doc=await io.read(path.join(out,'guanghua-closeout-raw.glb'));
for(const m of doc.getRoot().listMaterials())if(m.getName().startsWith('WEB leaf '))m.setAlphaMode('MASK').setAlphaCutoff(.5).setDoubleSided(true);
// Thin roof glass uses the controlled alpha approximation in the web derivative.
// Physical transmission would redraw the entire campus into a refraction buffer.
const glassFallbacks=[];
for(const m of doc.getRoot().listMaterials())if(m.getExtension('KHR_materials_transmission')){glassFallbacks.push(m.getName());m.setExtension('KHR_materials_transmission',null);}
await doc.transform(dedup(),prune(),meshopt({encoder:MeshoptEncoder,level:'high',quantizePosition:16,quantizeNormal:10,quantizeTexcoord:14}));
const p=path.join(out,'guanghua-closeout-optimized.glb');await io.write(p,doc);
const meshes=doc.getRoot().listMeshes();const nodes=doc.getRoot().listNodes().filter(n=>n.getMesh());
const stats={source:'guanghua-closeout-raw.glb',bytes:fs.statSync(p).size,sha256:createHash('sha256').update(fs.readFileSync(p)).digest('hex'),meshCount:meshes.length,nodeCount:nodes.length,sharedMeshCount:meshes.filter(m=>nodes.filter(n=>n.getMesh()===m).length>1).length,
 trianglesByLod:{},glassFallbacks,materialLimits:'Thin web glass uses alpha blending; native transmission and procedural mineral microrelief remain in the editable source',textures:doc.getRoot().listTextures().map(t=>({name:t.getName(),size:t.getSize(),bytes:t.getImage().byteLength}))};
for(const n of nodes){const lod=n.getExtras().closeout_lod||'static';let count=0;for(const p of n.getMesh().listPrimitives())count+=(p.getIndices()?.getCount()||p.getAttribute('POSITION').getCount())/3;stats.trianglesByLod[lod]=(stats.trianglesByLod[lod]||0)+count;}
fs.writeFileSync(path.join(out,'glb-metrics.json'),JSON.stringify(stats,null,2));console.log(JSON.stringify(stats,null,2));
if(stats.bytes>150*1024*1024)throw Error('GLB size exceeds the 150 MiB closeout budget');
