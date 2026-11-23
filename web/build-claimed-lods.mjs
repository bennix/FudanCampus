/** Rebuild the map-aligned local context without changing upstream source assets. */
import fs from 'node:fs';
import {contextIds} from './lib/claimed-area.mjs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {NodeIO} from '@gltf-transform/core';
import {prune,weld,simplify,meshopt,getBounds,compactPrimitive} from '@gltf-transform/functions';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {MeshoptEncoder,MeshoptDecoder,MeshoptSimplifier} from 'meshoptimizer';
await Promise.all([MeshoptEncoder.ready,MeshoptDecoder.ready,MeshoptSimplifier.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
const pub=new URL('./public/',import.meta.url),read=p=>JSON.parse(fs.readFileSync(new URL(p,pub)));
const manifest=read('campus-manifest.json'),lod=read('campus-lod.json'),offset=[-167.2,.5,-116];
const hash=b=>createHash('sha256').update(b).digest('hex').slice(0,12);
const triangles=d=>d.getRoot().listNodes().reduce((n,node)=>n+(node.getMesh()?.listPrimitives().reduce((s,p)=>s+p.getIndices().getCount()/3,0)??0),0);
const output='map-review/runtime';fs.mkdirSync(new URL(output+'/',pub),{recursive:true});
for(const id of ['46','51','landscape']){
 const landscape=id==='landscape';
 const contextSource=new URL('map-review/components/context-landscape.glb',pub).pathname;
 const source=landscape?(process.argv[2]??(fs.existsSync(contextSource)?contextSource:new URL(`${output}/landscape-near.glb`,pub).pathname)):new URL(`map-review/components/${id}.glb`,pub).pathname;
 const original=await io.read(source);
 if(landscape){
  for(const node of [...original.getRoot().listNodes()]){
   // Neighbouring buildings retain their upstream geometry and coordinates.
   if(contextIds.includes(String(node.getExtras().building_id??''))){node.dispose();continue;}
   if(/^\d+$/.test(String(node.getExtras().building_id??'')))node.setExtras({...node.getExtras(),mapContext:true});
   else if(/Tree|树干|叶片|花簇|竹/.test(node.getName()))node.setExtras({...node.getExtras(),campusVegetation:true});
  }
  await original.transform(prune());
 }
 const bounds=getBounds(original.getRoot().listScenes()[0]);
 const url=landscape?`${output}/landscape-near.glb`:`map-review/components/${id}.glb`;
 const raw=landscape?await io.writeBinary(original):fs.readFileSync(source);
 if(landscape)fs.writeFileSync(new URL(url,pub),raw);
 const tiers=[];
 for(const [level,sample] of [['far',32],['medium',16],['near',1]]){
  const doc=await io.readBinary(raw);
  if(landscape&&sample>1){
   for(const node of [...doc.getRoot().listNodes()])for(const prim of node.getMesh()?.listPrimitives()??[]){
    if(!/叶片|花簇/.test(prim.getMaterial()?.getName()??''))continue;
    const ix=prim.getIndices(),src=ix.getArray(),out=[];
    // Keep leaf cards across the whole crown, increasing their coverage as
    // density falls. Sparse branches alone must not become a winter canopy.
    const positions=prim.getAttribute('POSITION'),lo=positions.getMin([]),hi=positions.getMax([]),scale=level==='far'?4:3;
    for(let i=0;i<src.length;i+=6*sample){
     const ids=[...new Set(Array.from(src.slice(i,i+6)))];
     const centre=[0,1,2].map(k=>ids.reduce((s,id)=>s+positions.getElement(id,[])[k],0)/ids.length);
     for(const id of ids){const p=positions.getElement(id,[]);positions.setElement(id,p.map((v,k)=>Math.max(lo[k],Math.min(hi[k],centre[k]+(v-centre[k])*scale))));}
     for(let j=0;j<6&&i+j<src.length;j++)out.push(src[i+j]);
    }
    prim.setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint32Array(out)).setBuffer(ix.getBuffer()));compactPrimitive(prim);
   }
   await doc.transform(weld(),simplify({simplifier:MeshoptSimplifier,ratio:level==='far'?.2:.7,error:.005}),prune());
  }
  if(level!=='near')await doc.transform(meshopt({encoder:MeshoptEncoder,level:'medium',quantizePosition:16}));
  const file=level==='near'?url:`${output}/${id}-${level}.glb`,bytes=level==='near'?raw:await io.writeBinary(doc);
  if(landscape&&level==='medium'&&bytes.length>1024*1024)throw Error('The context medium tier must remain usable on a constrained connection');
  if(level!=='near')fs.writeFileSync(new URL(file,pub),bytes);
  tiers.push({url:file,bytes:bytes.length,revision:hash(bytes),triangles:triangles(doc)});
 }
 const entry={id:landscape?'claimed-46-51-landscape':id,name:landscape?'46/51 实拍景观与道路':id==='46'?'第一教学楼':'综合办公楼',url,bytes:raw.length,revision:hash(raw),position:offset,rotation:[0,0,0],bounds};
 if(!landscape){entry.labelPosition=id==='46'?[-167.2,14.75,-116]:[-165.6,24,-65.6];entry.overview={url,bytes:raw.length,revision:hash(raw)};entry.overviewMode='full';entry.loadDistance=240;}
 const category=landscape?'shared':'buildings';manifest[category]=manifest[category].filter(a=>a.id!==entry.id);manifest[category].push(entry);
 const assetId=category+'-'+entry.id;
 lod.assets=lod.assets.filter(a=>a.id!==assetId);lod.assets.push({id:assetId,name:entry.name,sourceRevision:entry.revision,labelPosition:entry.labelPosition??null,position:offset,rotation:[0,0,0],bounds:{min:bounds.min.map((x,i)=>x+offset[i]),max:bounds.max.map((x,i)=>x+offset[i])},nearDistance:landscape?70:100,mediumDistance:landscape?180:340,tiers});
 console.log(assetId,tiers.map(t=>[t.bytes,t.triangles]));
}
fs.writeFileSync(new URL('campus-manifest.json',pub),JSON.stringify(manifest,null,2)+'\n');
fs.writeFileSync(new URL('campus-lod.json',pub),JSON.stringify(lod,null,2)+'\n');
