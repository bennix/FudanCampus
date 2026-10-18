import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {Document,NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {copyToDocument,dequantize,prune,meshopt,getBounds,textureCompress} from '@gltf-transform/functions';
import {MeshoptDecoder,MeshoptEncoder} from 'meshoptimizer';
import sharp from 'sharp';
import {readModelBytes} from './read-model-bytes.mjs';
const pub=new URL('./public/',import.meta.url),path=new URL('campus-lod.json',pub),lod=JSON.parse(fs.readFileSync(path));
const asset=JSON.parse(fs.readFileSync(new URL('campus-manifest.json',pub))).shared.find(a=>a.id==='guanghua-landscape');
await Promise.all([MeshoptDecoder.ready,MeshoptEncoder.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder,'meshopt.encoder':MeshoptEncoder});
const source=await io.readBinary(readModelBytes(new URL(asset.url,pub)));await source.transform(dequantize());
const groups=new Map();for(const n of source.getRoot().listNodes()){const g=n.getExtras().tree_group;if(g&&g!=='V6 East spreading 01'){const a=groups.get(g)??[];a.push(n);groups.set(g,a);}}
lod.assets=lod.assets.filter(a=>!a.id.startsWith('landscape-tree-'));
let index=0;
for(const [name,nodes] of groups){
 const id=`landscape-tree-${String(index++).padStart(2,'0')}`,tiers=[];let bounds;
 for(const [level,size]of [['far',256],['middle',512],['near',1024]]){
  const doc=new Document();for(const e of source.getRoot().listExtensionsUsed())doc.createExtension(e.constructor).setRequired(e.isRequired());
  const scene=doc.createScene(),selected=nodes.filter(n=>n.getExtras().closeout_lod===level||n.getExtras().closeout_lod==='static');
  const copied=copyToDocument(doc,source,selected);for(const n of selected){const c=copied.get(n);c.setMatrix(n.getWorldMatrix());scene.addChild(c);}
  await doc.transform(prune());bounds=getBounds(scene);
  let triangles=0;for(const n of doc.getRoot().listNodes())for(const p of n.getMesh()?.listPrimitives()??[])triangles+=p.getIndices().getCount()/3;
  await doc.transform(textureCompress({encoder:sharp,resize:[size,size]}),meshopt({encoder:MeshoptEncoder,level:'medium',quantizePosition:16}));
  const bytes=await io.writeBinary(doc),url=`models/lod/${id}-${level}.glb`;fs.writeFileSync(new URL(url,pub),bytes);tiers.push({url,bytes:bytes.length,triangles,revision:createHash('sha256').update(bytes).digest('hex').slice(0,12)});
 }
 lod.assets.push({id,sourceId:'shared-guanghua-landscape',name,sourceRevision:asset.revision,position:[0,0,0],rotation:[0,0,0],bounds,nearDistance:65,mediumDistance:180,tiers});
}
fs.writeFileSync(path,JSON.stringify(lod,null,2)+'\n');console.log('TREE_LODS',groups.size);
