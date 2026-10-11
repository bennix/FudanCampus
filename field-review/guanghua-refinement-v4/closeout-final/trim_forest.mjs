// Remove only triangles entering the unified landscape envelope; retain exact outside triangles.
import {NodeIO} from '../../../.local/model-tools/node_modules/@gltf-transform/core/dist/index.js';
import {ALL_EXTENSIONS} from '../../../.local/model-tools/node_modules/@gltf-transform/extensions/dist/index.js';
import {prune} from '../../../.local/model-tools/node_modules/@gltf-transform/functions/dist/index.js';
import {MeshoptDecoder} from '../../../.local/model-tools/node_modules/meshoptimizer/index.js';
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {createHash} from 'node:crypto';
const out=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(out,'../../..'),pub=path.join(root,'web/public');
const report=JSON.parse(fs.readFileSync(path.join(out,'export-conversion.json'))),s=report.scale,[tx,ty]=report.translation_blender;
const old=path.join(pub,'models/shared/05-guanghua-v3.glb'),io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
const doc=await io.read(old);let removed=0,retained=0;const altered=[];
function inside(p,m){const x=(m[0]*p[0]+m[4]*p[1]+m[8]*p[2]+m[12]-tx)/s,y=(-m[2]*p[0]-m[6]*p[1]-m[10]*p[2]-m[14]-ty)/s;return x>-90+.004&&x<112.30211756-.004&&y>-9+.004&&y<124-.004;}
for(const node of doc.getRoot().listNodes().filter(n=>n.getMesh())){
 const mesh=node.getMesh(),world=node.getWorldMatrix(),changes=[];
 for(const primitive of mesh.listPrimitives()){
  const pos=primitive.getAttribute('POSITION'),index=primitive.getIndices(),kept=[];let cut=0;
  for(let i=0;i<(index?.getCount()||pos.getCount());i+=3){const ids=[0,1,2].map(j=>index?index.getScalar(i+j):i+j);if(ids.some(k=>inside(pos.getElement(k,[]),world)))cut++;else kept.push(...ids);}
  removed+=cut;retained+=kept.length/3;changes.push({primitive,kept,cut});
 }
 if(!changes.some(x=>x.cut))continue;
 const copy=doc.createMesh(mesh.getName()+' closeout boundary');node.setMesh(copy);altered.push(node.getName());
 for(const {primitive,kept} of changes){
  if(!kept.length)continue;const p=primitive.clone(),used=[...new Set(kept)],map=new Map(used.map((k,i)=>[k,i]));
  for(const semantic of primitive.listSemantics()){
   const a=primitive.getAttribute(semantic),oldArray=a.getArray(),width=a.getElementSize(),data=new oldArray.constructor(used.length*width);
   for(let i=0;i<used.length;i++)data.set(oldArray.subarray(used[i]*width,(used[i]+1)*width),i*width);
   const accessor=doc.createAccessor(a.getName()).setType(a.getType()).setNormalized(a.getNormalized()).setArray(data).setBuffer(a.getBuffer());p.setAttribute(semantic,accessor);
  }
  p.setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint32Array(kept.map(k=>map.get(k)))).setBuffer(primitive.getAttribute('POSITION').getBuffer()));copy.addPrimitive(p);
 }
}
await doc.transform(prune());const output=path.join(out,'05-guanghua-closeout.glb');await io.write(output,doc);
const result={source:'models/shared/05-guanghua-v3.glb',source_sha256:createHash('sha256').update(fs.readFileSync(old)).digest('hex'),bytes:fs.statSync(output).size,removedTriangles:removed,retainedTriangles:retained,alteredNodes:altered,method:'Discard only triangles with a referenced vertex entering the inherited interior envelope; all retained attributes and world transforms are unchanged'};
fs.writeFileSync(path.join(out,'forest-boundary-trim.json'),JSON.stringify(result,null,2));console.log(result);
