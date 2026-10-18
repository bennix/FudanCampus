import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {Document,NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dequantize,prune,meshopt,getBounds} from '@gltf-transform/functions';
import {MeshoptDecoder,MeshoptEncoder} from 'meshoptimizer';
import {Vector3,Matrix4} from 'three';
import sharp from 'sharp';
const pub=new URL('./public/',import.meta.url),path=new URL('campus-lod.json',pub),lod=JSON.parse(fs.readFileSync(path));
const asset=JSON.parse(fs.readFileSync(new URL('campus-manifest.json',pub))).shared.find(a=>a.id==='05');
await Promise.all([MeshoptDecoder.ready,MeshoptEncoder.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder,'meshopt.encoder':MeshoptEncoder});
const source=await io.read(new URL(asset.url,pub).pathname);await source.transform(dequantize());
const tiles=new Map();let crowns=0;
for(const node of [...source.getRoot().listNodes()]){
 if(!/Canopy/i.test(node.getName())||!node.getMesh())continue;
 const matrix=new Matrix4().fromArray(node.getWorldMatrix());
 for(const p of node.getMesh().listPrimitives()){
  const pos=p.getAttribute('POSITION').getArray(),idx=p.getIndices().getArray(),keys=new Map(),verts=[],parent=[],canonical=[];
  for(let i=0;i<pos.length;i+=3){const v=new Vector3(pos[i],pos[i+1],pos[i+2]).applyMatrix4(matrix),key=[v.x,v.y,v.z].map(x=>Math.round(x*10000)).join(',');let id=keys.get(key);if(id===undefined){id=verts.length;keys.set(key,id);verts.push(v);parent.push(id);}canonical.push(id);}
  const root=i=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
  for(let i=0;i<idx.length;i+=3){const a=root(canonical[idx[i]]);parent[root(canonical[idx[i+1]])]=a;parent[root(canonical[idx[i+2]])]=a;}
  const parts=new Map();for(let i=0;i<verts.length;i++){const r=root(i),a=parts.get(r)??[];a.push(verts[i]);parts.set(r,a);}
  for(const points of parts.values()){
   const lo=new Vector3(Infinity,Infinity,Infinity),hi=new Vector3(-Infinity,-Infinity,-Infinity);for(const v of points){lo.min(v);hi.max(v);}const center=lo.clone().add(hi).multiplyScalar(.5),radius=hi.clone().sub(lo).multiplyScalar(.5);
   const key=`${Math.floor(center.x/80)}_${Math.floor(center.z/80)}`,a=tiles.get(key)??[];a.push({center,radius,color:p.getMaterial().getBaseColorFactor(),seed:crowns++});tiles.set(key,a);
  }
 }
 node.dispose();
}
await source.transform(prune(),meshopt({encoder:MeshoptEncoder,level:'medium',quantizePosition:16}));
const trunkBytes=await io.writeBinary(source),trunkUrl='models/lod/shared-05-trunks.glb';fs.writeFileSync(new URL(trunkUrl,pub),trunkBytes);
let trunkTriangles=0;for(const n of source.getRoot().listNodes())for(const p of n.getMesh()?.listPrimitives()??[])trunkTriangles+=p.getIndices().getCount()/3;
const trunkTier={url:trunkUrl,bytes:trunkBytes.length,revision:createHash('sha256').update(trunkBytes).digest('hex').slice(0,12),triangles:trunkTriangles};lod.assets.find(a=>a.id==='shared-05').tiers=[trunkTier,trunkTier,trunkTier];
let svg='<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128">';for(const [x,y,r]of [[22,32,-35],[47,22,20],[77,30,50],[101,50,30],[31,64,-50],[67,61,25],[92,83,60],[46,96,-20],[72,108,10]])svg+=`<ellipse cx="${x}" cy="${y}" rx="10" ry="20" transform="rotate(${r} ${x} ${y})" fill="white"/>`;svg+='</svg>';const png=await sharp(Buffer.from(svg)).png().toBuffer();
lod.assets=lod.assets.filter(a=>!a.id.startsWith('campus-tree-'));
for(const [key,clusters]of tiles){
 const id='campus-tree-'+key,tiers=[];let bounds;
 for(const [level,count]of [['far',32],['middle',72],['near',128]]){
  const doc=new Document(),buffer=doc.createBuffer(),scene=doc.createScene();const texture=doc.createTexture('Leaf clusters').setImage(png).setMimeType('image/png');const material=doc.createMaterial('Natural campus foliage').setBaseColorTexture(texture).setAlphaMode('MASK').setAlphaCutoff(.45).setDoubleSided(true).setRoughnessFactor(1);
  const ps=[],ns=[],uv=[],cs=[],indices=[];
  for(const c of clusters){let seed=c.seed+123;const rand=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
   for(let i=0;i<count;i++){
    const z=rand()*2-1,a=rand()*Math.PI*2,rr=Math.sqrt(1-z*z),rad=.35+.65*Math.cbrt(rand());const center=new Vector3(Math.cos(a)*rr*c.radius.x*rad,z*c.radius.y*rad,Math.sin(a)*rr*c.radius.z*rad).add(c.center);
    const normal=new Vector3(rand()-.5,rand()*.75+.2,rand()-.5).normalize(),right=new Vector3().crossVectors(normal,new Vector3(0,0,1)).normalize(),up=new Vector3().crossVectors(normal,right).normalize();const size=(level==='far'?.92:level==='middle'?.72:.58)*(.8+rand()*.4),shade=.72+rand()*.55,base=ps.length/3;
    for(const [x,y,u,v]of [[-1,-1,0,0],[1,-1,1,0],[1,1,1,1],[-1,1,0,1]]){const point=center.clone().addScaledVector(right,x*size).addScaledVector(up,y*size);ps.push(...point.toArray());ns.push(...normal.toArray());uv.push(u,v);cs.push(...c.color.slice(0,3).map(v=>Math.min(1,v*shade)));}
    indices.push(base,base+1,base+2,base,base+2,base+3);
   }
  }
  const acc=(type,a)=>doc.createAccessor().setType(type).setArray(a).setBuffer(buffer);
  const prim=doc.createPrimitive().setAttribute('POSITION',acc('VEC3',new Float32Array(ps))).setAttribute('NORMAL',acc('VEC3',new Float32Array(ns))).setAttribute('TEXCOORD_0',acc('VEC2',new Float32Array(uv))).setAttribute('COLOR_0',acc('VEC3',new Float32Array(cs))).setIndices(acc('SCALAR',new Uint32Array(indices))).setMaterial(material);
  scene.addChild(doc.createNode('Campus leaf canopy').setMesh(doc.createMesh().addPrimitive(prim)).setExtras({campusVegetation:true}));bounds=getBounds(scene);
  await doc.transform(meshopt({encoder:MeshoptEncoder,level:'medium',quantizePosition:16}));const bytes=await io.writeBinary(doc),url=`models/lod/${id}-${level}.glb`;fs.writeFileSync(new URL(url,pub),bytes);tiers.push({url,bytes:bytes.length,triangles:indices.length/3,revision:createHash('sha256').update(bytes).digest('hex').slice(0,12)});
 }
 lod.assets.push({id,sourceId:'shared-05',name:'校园树木 '+key,sourceRevision:asset.revision,position:asset.position??[0,0,0],rotation:asset.rotation??[0,0,0],bounds,nearDistance:80,mediumDistance:200,tiers});
}
fs.writeFileSync(path,JSON.stringify(lod,null,2)+'\n');console.log('CAMPUS_TREES',crowns,tiles.size);
