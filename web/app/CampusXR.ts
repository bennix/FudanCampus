import * as THREE from 'three';

// Reviewed outdoor points. Teleport never accepts arbitrary roofs or flower beds.
export const teleportStops = [
 {id:'46',name:'第一教学楼',position:[-167.2,.56,-99] as const},
 {id:'51',name:'综合楼入口',position:[-139,.56,-61] as const},
 {id:'court',name:'综合楼西侧庭院',position:[-185,.56,-69] as const},
];

export function teleportRig(rig:THREE.Group, head:THREE.Vector3, target:THREE.Vector3){
 rig.position.x+=target.x-head.x;rig.position.z+=target.z-head.z;
 rig.position.y=target.y;rig.updateMatrixWorld(true);
}

export function visibleInHierarchy(object:THREE.Object3D){
 for(let n:THREE.Object3D|null=object;n;n=n.parent)if(!n.visible)return false;
 return true;
}

export function pickTeleport(ray:THREE.Raycaster, targets:THREE.Object3D[], obstacles:THREE.Object3D[]){
 const hit=ray.intersectObjects(targets,false)[0];
 if(!hit)return undefined;
 const wall=ray.intersectObjects(obstacles.filter(visibleInHierarchy),false)[0];
 return wall&&wall.distance<hit.distance-.05?undefined:hit.object;
}

export function createCampusXR(options:{scene:THREE.Scene;camera:THREE.PerspectiveCamera;
 renderer:THREE.WebGLRenderer;host:HTMLElement;ready:()=>boolean;
 obstacles:()=>THREE.Object3D[];onEnter:()=>void;onExit:()=>void;status:(s:string)=>void}){
 const {scene,camera,renderer,host}=options;
 renderer.xr.enabled=true;renderer.xr.setReferenceSpaceType('local-floor');
 // One rig transforms both the tracked head and the input rays.
 const rig=new THREE.Group();rig.name='XR viewer rig';scene.add(rig);rig.add(camera);
 const markers=new THREE.Group();markers.name='XR teleport stops';markers.visible=false;scene.add(markers);
 const targets:THREE.Mesh[]=[];const textures:THREE.Texture[]=[];
 for(const stop of teleportStops){
  const root=new THREE.Group();root.position.fromArray(stop.position);markers.add(root);
  const ring=new THREE.Mesh(new THREE.RingGeometry(.52,.7,40),new THREE.MeshBasicMaterial({color:0x4bcdb0,side:THREE.DoubleSide}));
  ring.rotation.x=-Math.PI/2;ring.position.y=.07;root.add(ring);
  const target=new THREE.Mesh(new THREE.SphereGeometry(.42,16,10),new THREE.MeshBasicMaterial({color:0x4bcdb0,transparent:true,opacity:.65}));
  target.position.y=1;target.userData.stop=stop;root.add(target);targets.push(target);
  const canvas=document.createElement('canvas');canvas.width=640;canvas.height=150;
  const ctx=canvas.getContext('2d')!;ctx.fillStyle='#173c32';ctx.fillRect(0,0,640,150);
  ctx.fillStyle='#fff';ctx.textAlign='center';ctx.font='38px sans-serif';ctx.fillText(stop.name,320,60);
  ctx.font='25px sans-serif';ctx.fillText('扳机瞬移 · 无手柄时凝视 2 秒',320,115);
  const texture=new THREE.CanvasTexture(canvas);textures.push(texture);
  const label=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,depthTest:true}));label.position.y=2;label.scale.set(3.2,.75,1);root.add(label);
 }
 const ray=new THREE.Raycaster();ray.far=90;
 const rotation=new THREE.Matrix4(),head=new THREE.Vector3();
 const controllers=[renderer.xr.getController(0),renderer.xr.getController(1)];
 const inputs=new Set<THREE.Object3D>();
 const handlers: {controller:typeof controllers[number];select:()=>void;connected:()=>void;disconnected:()=>void}[]=[];
 function aim(object:THREE.Object3D){
  object.updateWorldMatrix(true,false);rotation.extractRotation(object.matrixWorld);
  ray.ray.origin.setFromMatrixPosition(object.matrixWorld);ray.ray.direction.set(0,0,-1).applyMatrix4(rotation).normalize();
  return pickTeleport(ray,targets,options.obstacles());
 }
 function move(target:THREE.Object3D){
  const stop=target.userData.stop as typeof teleportStops[number];
  renderer.xr.getCamera().getWorldPosition(head);
  teleportRig(rig,head,new THREE.Vector3(...stop.position));
  options.status(`VR 已瞬移至${stop.name}`);gazeTarget=undefined;gazeTime=0;
 }
 for(const controller of controllers){
  rig.add(controller);
  const beam=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(),new THREE.Vector3(0,0,-1)]),new THREE.LineBasicMaterial({color:0x4bcdb0}));
  beam.scale.z=12;controller.add(beam);
  const select=()=>{if(!renderer.xr.isPresenting)return;const target=aim(controller);if(target)move(target);};
  const connected=()=>inputs.add(controller),disconnected=()=>inputs.delete(controller);
  controller.addEventListener('selectstart',select);controller.addEventListener('connected',connected);controller.addEventListener('disconnected',disconnected);
  handlers.push({controller,select,connected,disconnected});
 }
 const button=document.createElement('button');button.className='xr-entry';button.textContent='检测 VR 设备…';button.disabled=true;host.appendChild(button);
 const saved={position:new THREE.Vector3(),quaternion:new THREE.Quaternion(),near:1,fov:43};
 let disposed=false,busy=false,supported=false,gazeTarget:THREE.Object3D|undefined,gazeTime=0;
 async function detect(){
  try{supported=!!navigator.xr&&await navigator.xr.isSessionSupported('immersive-vr');}
  catch{supported=false;}
  if(disposed)return;
  button.textContent=supported?'进入 VR':'VR 需兼容头显';button.disabled=!supported;
  button.title=supported?'使用头显浏览器进入；扳机指向标记瞬移':'当前设备未提供沉浸式 VR；桌面浏览仍可用。头显须通过 HTTPS 访问。';
 }
 void detect();
 button.onclick=async()=>{
  if(busy)return;
  if(renderer.xr.isPresenting){await renderer.xr.getSession()?.end();return;}
  if(!options.ready()){options.status('校园仍在载入，请稍后进入 VR');return;}
  busy=true;button.disabled=true;
  let session:XRSession|undefined;
  try{
   session=await navigator.xr!.requestSession('immersive-vr',{requiredFeatures:['local-floor']});
   if(disposed){await session.end();return;}
   await renderer.xr.setSession(session);
  }catch(error){await session?.end().catch(()=>{});options.status(`无法进入 VR：${error instanceof Error?error.message:String(error)}`);}
  finally{busy=false;if(!disposed)button.disabled=!supported;}
 };
 const enter=()=>{
  saved.position.copy(camera.position);saved.quaternion.copy(camera.quaternion);saved.near=camera.near;saved.fov=camera.fov;
  options.onEnter();rig.position.fromArray(teleportStops[0].position);camera.position.set(0,1.65,0);camera.rotation.set(0,0,0);camera.near=.1;camera.updateProjectionMatrix();
  markers.visible=true;button.textContent='退出 VR';host.classList.add('xr-active');
  options.status('VR：头部自然观察，扳机指向青色标记瞬移；无手柄可凝视 2 秒');
 };
 const leave=()=>{
  markers.visible=false;rig.position.set(0,0,0);camera.position.copy(saved.position);camera.quaternion.copy(saved.quaternion);camera.near=saved.near;camera.fov=saved.fov;camera.updateProjectionMatrix();
  gazeTarget=undefined;gazeTime=0;button.textContent='进入 VR';host.classList.remove('xr-active');options.onExit();
 };
 renderer.xr.addEventListener('sessionstart',enter);renderer.xr.addEventListener('sessionend',leave);
 return {
  update(dt:number){
   if(!renderer.xr.isPresenting)return;
   scene.updateMatrixWorld(true);
   if(inputs.size){gazeTarget=undefined;gazeTime=0;for(const c of inputs){const target=aim(c);const beam=c.children[0] as THREE.Line;(beam.material as THREE.LineBasicMaterial).color.set(target?0xffd373:0x4bcdb0);}return;}
   const target=aim(renderer.xr.getCamera());
   if(target!==gazeTarget){gazeTarget=target;gazeTime=0;}
   else if(target){gazeTime+=dt;if(gazeTime>=2)move(target);}
  },
  position(){return renderer.xr.isPresenting?renderer.xr.getCamera().getWorldPosition(head):camera.position;},
  dispose(){disposed=true;button.remove();renderer.xr.removeEventListener('sessionstart',enter);renderer.xr.removeEventListener('sessionend',leave);void renderer.xr.getSession()?.end();
   for(const h of handlers){h.controller.removeEventListener('selectstart',h.select);h.controller.removeEventListener('connected',h.connected);h.controller.removeEventListener('disconnected',h.disconnected);}
   markers.traverse(o=>{if(o instanceof THREE.Mesh||o instanceof THREE.Sprite){if(o instanceof THREE.Mesh)o.geometry.dispose();(o.material as THREE.Material).dispose();}});textures.forEach(t=>t.dispose());markers.removeFromParent();
   controllers.forEach(c=>{c.traverse(o=>{if(o instanceof THREE.Line){o.geometry.dispose();(o.material as THREE.Material).dispose();}});c.removeFromParent();});scene.attach(camera);rig.removeFromParent();host.classList.remove('xr-active');
  }
 };
}
