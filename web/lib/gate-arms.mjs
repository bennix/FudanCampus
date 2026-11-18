import * as THREE from 'three';

// World coordinates of the two hinges from scripts/gate_geometry.py, landmark 65.
const centreX=-40, hingeZ=-9.16, height=1.15;

// Includes the white beam and its surface stripes, excludes the red motor housings.
export function isArmVertex(x,y,z){
 const dx=Math.abs(x-centreX);
 return dx>.28 && dx<4.07 && Math.abs(y-height)<.077 && Math.abs(z-hingeZ)<.09;
}

export function removeBakedArms(group){
 group.updateMatrixWorld(true);
 const vertex=new THREE.Vector3();
 group.traverse(mesh=>{
  if(!mesh.isMesh || !/Gate[ _](white[ _]concrete|red[ _]lettering)/i.test(mesh.name))return;
  const geometry=mesh.geometry,positions=geometry.attributes.position,index=geometry.index;
  const mask=Array.from({length:positions.count},(_,i)=>{
   vertex.fromBufferAttribute(positions,i).applyMatrix4(mesh.matrixWorld);
   return isArmVertex(vertex.x,vertex.y,vertex.z);
  });
  const remaining=[];
  for(let i=0;i<(index?.count??positions.count);i+=3){
   const a=index?index.getX(i):i,b=index?index.getX(i+1):i+1,c=index?index.getX(i+2):i+2;
   if(!(mask[a]&&mask[b]&&mask[c]))remaining.push(a,b,c);
  }
  geometry.setIndex(remaining);
 });
}

export function createGateArms(){
 const group=new THREE.Group();
 const beamGeometry=new THREE.BoxGeometry(3.75,.13,.09);
 const stripeGeometry=new THREE.BoxGeometry(.22,.085,.095);
 const white=new THREE.MeshStandardMaterial({color:0xe9e8de});
 const red=new THREE.MeshStandardMaterial({color:0xc94534});
 for(const side of [-1,1]){
  const pivot=new THREE.Group();
  pivot.position.set(centreX+side*4.055,height,hingeZ);
  const beam=new THREE.Mesh(beamGeometry,white);beam.position.x=-side*1.875;
  beam.castShadow=true;pivot.add(beam);
  for(let i=0;i<9;i++){
   const stripe=new THREE.Mesh(stripeGeometry,red);
   stripe.position.x=side*(.45+i*.4-4.055);pivot.add(stripe);
  }
  group.add(pivot);
 }
 let open=false,angle=0;
 function update(eye,dt){
  open=!!eye && Math.abs(eye.x-centreX)<(open?7:5.2) && Math.abs(eye.z-hingeZ)<(open?10:8);
  const target=open?Math.PI*.48:0;
  const next=THREE.MathUtils.clamp(target,angle-dt*1.2,angle+dt*1.65);
  if(next===angle)return false;
  angle=next;group.children[0].rotation.z=angle;group.children[1].rotation.z=-angle;
  return true;
 }
 return {group,update};
}
