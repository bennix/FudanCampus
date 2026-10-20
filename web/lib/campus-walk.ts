import * as THREE from 'three';
import {Octree} from 'three/addons/math/Octree.js';
import {Capsule} from 'three/addons/math/Capsule.js';
export type Interior={bounds:number[];rings:number[][][]};
function inRing(x:number,z:number,ring:number[][]){let hit=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const a=ring[i],b=ring[j];if((a[1]>z)!==(b[1]>z)&&x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])hit=!hit;}return hit;}
export function blockedInterior(x:number,z:number,polygons:Interior[],radius=.30){
 for(const p of polygons){const [x0,z0,x1,z1]=p.bounds;if(x<x0-radius||x>x1+radius||z<z0-radius||z>z1+radius)continue;
  if(inRing(x,z,p.rings[0])&&!p.rings.slice(1).some(r=>inRing(x,z,r)))return true;
  for(const ring of p.rings)for(let i=1;i<ring.length;i++){const a=ring[i-1],b=ring[i],dx=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz||1)));if(Math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)<radius)return true;}
 }return false;
}
/** Fixed collision chunks: visual LOD swaps cannot remove a wall under the walker. */
export class WalkWorld{
 private data:Float32Array;private cells=new Map<string,number[]>();private cache=new Map<string,Octree>();private global:Octree;
 readonly interiors:Interior[];
 constructor(data:Float32Array,interiors:Interior[]){this.data=data;this.interiors=interiors;const wide:number[]=[];
  for(let i=0;i<data.length;i+=9){const x0=Math.floor(Math.min(data[i],data[i+3],data[i+6])/24),x1=Math.floor(Math.max(data[i],data[i+3],data[i+6])/24),z0=Math.floor(Math.min(data[i+2],data[i+5],data[i+8])/24),z1=Math.floor(Math.max(data[i+2],data[i+5],data[i+8])/24);
   if((x1-x0+1)*(z1-z0+1)>16){wide.push(i);continue;}
   for(let x=x0;x<=x1;x++)for(let z=z0;z<=z1;z++){const key=x+','+z;const a=this.cells.get(key)??[];a.push(i);this.cells.set(key,a);}
  }this.global=this.build(wide);
 }
 private build(ids:number[]){const tree=new Octree();for(const i of ids){tree.addTriangle(new THREE.Triangle(new THREE.Vector3().fromArray(this.data,i),new THREE.Vector3().fromArray(this.data,i+3),new THREE.Vector3().fromArray(this.data,i+6)));}tree.build();return tree;}
 private nearby(p:THREE.Vector3){const trees=[this.global];for(let x=Math.floor((p.x-1)/24);x<=Math.floor((p.x+1)/24);x++)for(let z=Math.floor((p.z-1)/24);z<=Math.floor((p.z+1)/24);z++){const key=x+','+z;if(!this.cache.has(key))this.cache.set(key,this.build(this.cells.get(key)??[]));trees.push(this.cache.get(key)!);}if(this.cache.size>20){for(const [key,tree] of this.cache)if(!trees.includes(tree)){this.cache.delete(key);break;}}return trees;}
 blocked(x:number,z:number){return blockedInterior(x,z,this.interiors);}
 resolve(capsule:Capsule){let ground=false,wall=false;for(let pass=0;pass<4;pass++){let any=false;for(const tree of this.nearby(capsule.start)){const hit=tree.capsuleIntersect(capsule);if(hit&&hit.depth>1e-6){capsule.translate(hit.normal.clone().multiplyScalar(hit.depth+1e-5));ground ||= hit.normal.y>.5;wall ||= Math.abs(hit.normal.y)<.5;any=true;}}if(!any)break;}return {ground,wall};}
 floor(x:number,z:number,from=2.5){const origin=new THREE.Vector3(x,from,z),ray=new THREE.Ray(origin,new THREE.Vector3(0,-1,0));let y=-Infinity;for(const tree of this.nearby(origin)){const hit=tree.rayIntersect(ray);if(hit)y=Math.max(y,hit.position.y);}return y;}
 spawn(preferred:THREE.Vector3){for(let r=0;r<45;r+=1.5)for(let j=0;j<(r===0?1:24);j++){const x=preferred.x+Math.cos(j*Math.PI/12)*r,z=preferred.z+Math.sin(j*Math.PI/12)*r;if(this.blocked(x,z))continue;const floor=this.floor(x,z);if(!Number.isFinite(floor)||floor<-.5||floor>1.8)continue;const c=new Capsule(new THREE.Vector3(x,floor+.31,z),new THREE.Vector3(x,floor+1.41,z),.3);this.resolve(c);if(Math.hypot(c.start.x-x,c.start.z-z)<.05&&!this.blocked(c.start.x,c.start.z))return c;}throw Error('附近没有可安全落脚的位置，请切换到校门或空旷区域');}
}
export class Walker{
 readonly body:Capsule;private vertical=0;private grounded=false;private safe:Capsule;
 private world:WalkWorld;
 constructor(world:WalkWorld,start:THREE.Vector3){this.world=world;this.body=world.spawn(start);this.safe=this.body.clone();}
 eye(){return this.body.end.clone().add(new THREE.Vector3(0,.27,0));}
 move(direction:THREE.Vector3,dt:number,speed=2.5){dt=Math.min(.05,Math.max(0,dt));const steps=Math.max(1,Math.ceil(speed*dt/.075)),h=dt/steps;
  for(let i=0;i<steps;i++){
   const before=this.body.clone();const delta=direction.clone().multiplyScalar(speed*h);this.vertical=Math.max(-8,this.vertical-18*h);delta.y=this.vertical*h;
   // Axis-wise movement slides along sealed exterior boundaries and concave courtyards.
   if(!this.world.blocked(this.body.start.x+delta.x,this.body.start.z))this.body.translate(new THREE.Vector3(delta.x,0,0));
   if(!this.world.blocked(this.body.start.x,this.body.start.z+delta.z))this.body.translate(new THREE.Vector3(0,0,delta.z));
   this.body.translate(new THREE.Vector3(0,delta.y,0));const result=this.world.resolve(this.body);
   if(result.wall&&this.grounded){const raised=before.clone();raised.translate(new THREE.Vector3(delta.x,.26,delta.z));const check=this.world.resolve(raised);if(!check.wall&&!this.world.blocked(raised.start.x,raised.start.z)){const floor=this.world.floor(raised.start.x,raised.start.z,before.start.y+.27);if(floor>=before.start.y-.32&&floor<=before.start.y-.3+.26)this.body.copy(raised);}}
   if(this.world.blocked(this.body.start.x,this.body.start.z)){this.body.copy(before);this.vertical=0;}
   if(result.ground){this.vertical=0;this.safe.copy(this.body);}this.grounded=result.ground;
   if(this.body.start.y<this.safe.start.y-2||Math.abs(this.body.start.x)>1500||Math.abs(this.body.start.z)>1200){this.body.copy(this.safe);this.vertical=0;}
  }
 }
}
