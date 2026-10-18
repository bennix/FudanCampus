import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {prune,weld,simplify,dedup,instance,textureCompress,meshopt,getBounds} from '@gltf-transform/functions';
import {MeshoptDecoder,MeshoptEncoder,MeshoptSimplifier} from 'meshoptimizer';
import sharp from 'sharp';
import {readModelBytes} from './read-model-bytes.mjs';
const pub=new URL('./public/',import.meta.url),manifest=JSON.parse(fs.readFileSync(new URL('campus-manifest.json',pub)));
const asset=manifest.shared.find(a=>a.id==='guanghua-landscape');if(!asset)process.exit(0);
await Promise.all([MeshoptDecoder.ready,MeshoptEncoder.ready,MeshoptSimplifier.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder,'meshopt.encoder':MeshoptEncoder});
const bytes=readModelBytes(new URL(asset.url,pub)),tiers=[];let bounds;
for(const [level,ratio,size] of [['far',.01,128],['middle',.025,256],['near',.15,512]]){
 const doc=await io.readBinary(bytes);
 for(const ext of [...doc.getRoot().listExtensionsUsed()])if(['EXT_meshopt_compression','KHR_mesh_quantization'].includes(ext.extensionName))ext.dispose();
 for(const n of [...doc.getRoot().listNodes()]){const tag=n.getExtras().closeout_lod;if(tag&&tag!=='static'&&tag!==level)n.dispose();}
 await doc.transform(prune(),weld(),simplify({simplifier:level==='near'?MeshoptSimplifier:{...MeshoptSimplifier,simplify:(indices,positions,stride,count,error)=>MeshoptSimplifier.simplify(indices,positions,stride,count,error,['Permissive','Prune'])},ratio,error:1,lockBorder:false}),prune(),dedup(),textureCompress({encoder:sharp,resize:[size,size]}));
 // The scene contains repeated leaf prototypes. Preserve GPU instancing in the derived delivery.
 bounds??=getBounds(doc.getRoot().listScenes()[0]);
 let triangles=0;for(const n of doc.getRoot().listNodes())if(n.getMesh())for(const p of n.getMesh().listPrimitives())triangles+=(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3;
 const plants=new Set(doc.getRoot().listNodes().filter(n=>/Canop|Trunk|Tree bark/i.test(n.getName())||['near','middle','far'].includes(n.getExtras().closeout_lod)).map(n=>n.getMesh()));
 await doc.transform(instance({min:2}));
 for(const n of doc.getRoot().listNodes())if(plants.has(n.getMesh()))n.setExtras({...n.getExtras(),campusVegetation:true});
 await doc.transform(meshopt({encoder:MeshoptEncoder,level:'medium'}));
 const out=await io.writeBinary(doc),url=`models/lod/shared-guanghua-landscape-${level}.glb`;
 fs.writeFileSync(new URL(url,pub),out);tiers.push({url,revision:createHash('sha256').update(out).digest('hex').slice(0,12),bytes:out.length,triangles:Math.round(triangles)});
 console.log('LANDSCAPE_LOD',level,out.length,triangles);
}
const path=new URL('campus-lod.json',pub),lod=JSON.parse(fs.readFileSync(path));lod.assets=lod.assets.filter(a=>a.id!=='shared-guanghua-landscape');lod.assets.push({id:'shared-guanghua-landscape',name:asset.name,sourceRevision:asset.revision,position:[0,0,0],rotation:[0,0,0],bounds,nearDistance:80,mediumDistance:250,tiers});fs.writeFileSync(path,JSON.stringify(lod,null,2)+'\n');
