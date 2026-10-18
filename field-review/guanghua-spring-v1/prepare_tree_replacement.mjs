import fs from 'node:fs';
import {NodeIO} from '../../.local/model-tools/node_modules/@gltf-transform/core/dist/index.js';
import {ALL_EXTENSIONS} from '../../.local/model-tools/node_modules/@gltf-transform/extensions/dist/index.js';
import {MeshoptDecoder} from '../../.local/model-tools/node_modules/meshoptimizer/index.js';
import {Matrix4,Vector3} from '../../web/node_modules/three/build/three.module.js';
await MeshoptDecoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
const doc=await io.read('web/public/models/landscape/guanghua-closeout.glb');
const n=doc.getRoot().listNodes().find(n=>n.getExtras().feature_id==='TREE_CANOPY_V6'&&n.getExtras().sources?.includes('V6 East spreading 01 wood'));
const m=new Matrix4().fromArray(n.getWorldMatrix()),primitives=[];
for(const p of n.getMesh().listPrimitives()){
 const a=p.getAttribute('POSITION'),ix=p.getIndices(),centers=[],v=[];
 for(let i=0;i<ix.getCount();i+=3){const c=new Vector3();for(let j=0;j<3;j++)c.add(new Vector3(...a.getElement(ix.getScalar(i+j),v)).applyMatrix4(m));c.multiplyScalar(1/3);centers.push([(c.x-117.86666870117188)*1.5,(-c.z-122.80000305175781)*1.5,c.y*1.5]);}
 primitives.push({triangles:ix.getCount()/3,centers});
}
fs.writeFileSync('field-review/guanghua-spring-v1/old-wood-batch.json',JSON.stringify({node:n.getName(),sources:n.getExtras().sources.split('; '),primitives}));
console.log('Prepared exact source batch',n.getName(),primitives.map(p=>p.triangles));
