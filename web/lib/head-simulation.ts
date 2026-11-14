import * as THREE from 'three';
import {observationPoints,smoothHead,type ObservationKey} from './immersive-policy';
type Controls={target:THREE.Vector3;enabled:boolean;autoRotate:boolean};
export class HeadSimulation{
 active=false;
 private camera:THREE.PerspectiveCamera;
 private controls:Controls;
 private saved?:{position:THREE.Vector3;rotation:THREE.Quaternion;target:THREE.Vector3;fov:number;near:number;enabled:boolean;autoRotate:boolean};
 private base=new THREE.Quaternion();
 private target=new THREE.Quaternion();
 private baseYaw=0;private basePitch=0;
 private key:ObservationKey='teaching4';
 yaw=0;pitch=0;
 constructor(camera:THREE.PerspectiveCamera,controls:Controls){this.camera=camera;this.controls=controls;}
 enter(key:ObservationKey){
  if(!this.active){this.saved={position:this.camera.position.clone(),rotation:this.camera.quaternion.clone(),target:this.controls.target.clone(),fov:this.camera.fov,near:this.camera.near,enabled:this.controls.enabled,autoRotate:this.controls.autoRotate};}
  this.active=true;this.key=key;this.controls.enabled=false;this.controls.autoRotate=false;
  const point=observationPoints[key];this.camera.position.fromArray(point.position);this.camera.position.y+=point.eyeHeight;
  this.camera.lookAt(new THREE.Vector3(...point.target));this.base.copy(this.camera.quaternion);const euler=new THREE.Euler().setFromQuaternion(this.base,'YXZ');this.baseYaw=euler.y;this.basePitch=euler.x;
  this.camera.near=.08;this.camera.fov=70;this.camera.updateProjectionMatrix();this.reset();
 }
 setHead(yaw:number,pitch:number){this.yaw=THREE.MathUtils.clamp(yaw,-Math.PI,Math.PI);this.pitch=THREE.MathUtils.clamp(pitch,-1.3,1.3);this.target.setFromEuler(new THREE.Euler(THREE.MathUtils.clamp(this.pitch+this.basePitch,-1.45,1.45),this.yaw+this.baseYaw,0,'YXZ'));}
 reset(){this.setHead(0,0);this.camera.quaternion.copy(this.base);}
 update(dt:number){if(this.active)smoothHead(this.camera.quaternion,this.target,dt);}
 get point(){return this.key;}
 exit(){
  if(!this.active||!this.saved)return;const saved=this.saved;this.active=false;
  this.camera.position.copy(saved.position);this.camera.quaternion.copy(saved.rotation);this.camera.fov=saved.fov;this.camera.near=saved.near;this.camera.updateProjectionMatrix();
  this.controls.target.copy(saved.target);this.controls.enabled=saved.enabled;this.controls.autoRotate=saved.autoRotate;this.saved=undefined;
 }
}
