import * as THREE from 'three';
import type {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {HeadSimulation} from './head-simulation';
import {observationPoints,type ObservationKey} from './immersive-policy';
import {summarizeFrames,type FrameSample} from './frame-metrics';

type Options={ready:()=>boolean;beforeEnter:()=>void;changed:()=>void;activity:(active:boolean)=>void;quality:string;lodState:()=>unknown};
type ExperimentOptions={culling?:boolean;shadows?:boolean;warmupMs?:number;sampleMs?:number};
export type Capture={dataUrl:string;metadata:Record<string,unknown>};
export function saveFile(name:string,content:Blob|string){
 const url=typeof content==='string'?content:URL.createObjectURL(content),a=document.createElement('a');a.href=url;a.download=name;a.click();
 if(typeof content!=='string')setTimeout(()=>URL.revokeObjectURL(url),1000);
}
/** A desktop simulator and an actual WebXR entry share evidence/metrics, never evidence labels. */
export class CampusLab{
 readonly simulation:HeadSimulation;
 readonly panel=document.createElement('details');
 private renderer:THREE.WebGLRenderer;private scene:THREE.Scene;private camera:THREE.PerspectiveCamera;private controls:OrbitControls;private options:Options;
 private point:ObservationKey='teaching4';private disposed=false;private pointer?:number;private xrBusy=false;
 private culling=true;private shadows:boolean;private originalCulling=new WeakMap<THREE.Object3D,boolean>();
 private message=document.createElement('p');private simulateButton=document.createElement('button');private vrButton=document.createElement('button');
 private savedXR?:{position:THREE.Vector3;quaternion:THREE.Quaternion;target:THREE.Vector3;fov:number;near:number;enabled:boolean;rotate:boolean};
 private rig=new THREE.Group();private pendingCapture=false;private xrCapture?:Capture;
 private experiment?:{warmupEnd:number;end:number;previous:number;frames:FrameSample[];resolve:(value:Record<string,unknown>)=>void;reject:(error:Error)=>void;metadata:Record<string,unknown>;settings:ExperimentOptions};
 private previousControlsEnabled=true;
 constructor(renderer:THREE.WebGLRenderer,scene:THREE.Scene,camera:THREE.PerspectiveCamera,controls:OrbitControls,options:Options){
  this.renderer=renderer;this.scene=scene;this.camera=camera;this.controls=controls;this.options=options;this.shadows=renderer.shadowMap.enabled;
  this.simulation=new HeadSimulation(camera,controls);renderer.xr.enabled=true;renderer.xr.setReferenceSpaceType('local-floor');
  this.panel.className='campus-lab';this.panel.setAttribute('aria-label','沉浸视角与性能实验');
  const title=document.createElement('summary');title.textContent='沉浸视角与性能实验';this.panel.appendChild(title);
  const note=document.createElement('p');note.textContent='无设备：模拟原地转头；模拟图不代表真实头显实测。';this.panel.appendChild(note);
  const select=document.createElement('select');select.setAttribute('aria-label','沉浸观察点');
  for(const [key,point] of Object.entries(observationPoints)){const option=document.createElement('option');option.value=key;option.textContent=point.name;select.appendChild(option);}
  select.onchange=()=>{if(this.busy){select.value=this.point;return;}this.point=select.value as ObservationKey;if(this.simulation.active)this.simulation.enter(this.point);options.changed();};this.panel.appendChild(select);
  const row=document.createElement('div');row.className='lab-actions';this.panel.appendChild(row);
  const button=(text:string,action:()=>void)=>{const b=document.createElement('button');b.textContent=text;b.type='button';b.onclick=action;row.appendChild(b);return b;};
  this.simulateButton=button('开始头显模拟',()=>{try{this.simulate(!this.simulation.active);}catch(e){this.say(String(e));}});
  button('视角复位',()=>{if(!this.busy)this.simulation.reset();});
  button('保存视角图',()=>{try{const shot=this.capture();this.downloadCapture(shot);}catch(e){this.say(String(e));}});
  this.vrButton=button('检测 WebXR…',()=>void this.toggleXR());this.vrButton.disabled=true;
  button('结束后保存XR图',()=>{this.pendingCapture=true;this.say('进入真实XR后等待5秒取图；退出后自动下载。');});
  const culling=document.createElement('input');culling.type='checkbox';culling.checked=true;culling.onchange=()=>{if(this.busy){culling.checked=this.culling;return;}this.configure({culling:culling.checked});};
  const shadow=document.createElement('input');shadow.type='checkbox';shadow.checked=this.shadows;shadow.onchange=()=>{if(this.busy){shadow.checked=this.shadows;return;}this.configure({shadows:shadow.checked});};
  for(const [input,text] of [[culling,'视锥裁剪'],[shadow,'缓存阴影']] as const){const label=document.createElement('label');label.appendChild(input);label.appendChild(document.createTextNode(text));this.panel.appendChild(label);}
  button('采集20秒并导出',()=>{void this.run({culling:this.culling,shadows:this.shadows}).then(data=>saveFile(`campus-${this.point}-metrics.json`,new Blob([JSON.stringify(data,null,2)],{type:'application/json'}))).catch(e=>this.say(String(e)));});
  this.message.setAttribute('role','status');this.panel.appendChild(this.message);this.say('拖动场景模拟转头；Esc退出模拟。');
  renderer.domElement.addEventListener('pointerdown',this.down);renderer.domElement.addEventListener('pointermove',this.move);renderer.domElement.addEventListener('pointerup',this.up);renderer.domElement.addEventListener('pointercancel',this.up);renderer.domElement.addEventListener('webglcontextlost',this.contextLost);window.addEventListener('keydown',this.key);document.addEventListener('visibilitychange',this.visibility);
  renderer.xr.addEventListener('sessionstart',this.xrStart);renderer.xr.addEventListener('sessionend',this.xrEnd);
  if(!isSecureContext)this.vrButton.textContent='WebXR需要HTTPS或localhost';
  else if(!navigator.xr)this.vrButton.textContent='本浏览器无WebXR';
  else void navigator.xr.isSessionSupported('immersive-vr').then(supported=>{if(this.disposed)return;this.vrButton.disabled=!supported;this.vrButton.textContent=supported?'进入真实VR':'未连接VR设备';}).catch(()=>{if(!this.disposed)this.vrButton.textContent='WebXR检测失败';});
 }
 private say(text:string){if(!this.disposed)this.message.textContent=text;}
 get active(){return this.simulation.active||this.renderer.xr.isPresenting||this.xrBusy;}
 get busy(){return !!this.experiment||this.renderer.xr.isPresenting||this.xrBusy;}
 get measuring(){return !!this.experiment;}
 get forceRender(){return this.active||!!this.experiment;}
 get ready(){return !this.disposed&&!this.renderer.getContext().isContextLost()&&this.options.ready();}
 observe(point:ObservationKey){if(this.busy)throw Error('请先结束实验或XR会话');this.point=point;const select=this.panel.querySelector('select')!;select.value=point;if(this.simulation.active)this.simulation.enter(point);}
 simulate(enabled:boolean){
  if(this.busy)throw Error('请先结束实验或XR会话');
  if(enabled){if(!this.ready)throw Error('请等待校园与LOD加载稳定');this.options.beforeEnter();this.simulation.enter(this.point);}
  else this.simulation.exit();this.simulateButton.textContent=enabled?'退出头显模拟':'开始头显模拟';this.options.activity(this.active);this.options.changed();
 }
 private down=(event:PointerEvent)=>{if(!this.simulation.active||this.experiment)return;this.pointer=event.pointerId;this.renderer.domElement.setPointerCapture(event.pointerId);};
 private move=(event:PointerEvent)=>{if(this.pointer!==event.pointerId||!this.simulation.active||this.experiment)return;this.simulation.setHead(this.simulation.yaw-event.movementX*.004,this.simulation.pitch-event.movementY*.004);};
 private up=()=>{this.pointer=undefined;};
 private key=(event:KeyboardEvent)=>{if(event.code==='Escape'&&this.simulation.active&&!this.busy)this.simulate(false);};
 private visibility=()=>{if(document.hidden)this.cancel('页面进入后台，实验取消');};
 private contextLost=()=>{this.cancel('WebGL上下文丢失，实验取消');this.say('图形上下文丢失；请等待恢复或刷新网页后重试。');};
 configure(settings:ExperimentOptions){
  if(settings.culling!==undefined)this.culling=settings.culling;if(settings.shadows!==undefined)this.shadows=settings.shadows;
  this.renderer.shadowMap.enabled=this.shadows;this.renderer.shadowMap.needsUpdate=true;this.options.changed();this.applyCulling();
 }
 prepare(group:THREE.Object3D){group.traverse(object=>{if(object instanceof THREE.Mesh){if(!this.originalCulling.has(object))this.originalCulling.set(object,object.frustumCulled);object.frustumCulled=this.culling?this.originalCulling.get(object)!:false;}});}
 private applyCulling(){this.prepare(this.scene);this.scene.traverse(object=>{if(object instanceof THREE.DirectionalLight)object.castShadow=this.shadows;});}
 tick(dt:number){this.simulation.update(dt);}
 private async toggleXR(){
  if(this.renderer.xr.isPresenting){await this.renderer.xr.getSession()?.end();return;}
  if(!this.ready||this.experiment||this.xrBusy){this.say('请等待加载或实验结束');return;}
  this.xrBusy=true;this.options.activity(true);this.vrButton.disabled=true;let session:XRSession|undefined;
  try{session=await navigator.xr!.requestSession('immersive-vr',{requiredFeatures:['local-floor']});if(this.disposed){await session.end();return;}await this.renderer.xr.setSession(session);}
  catch(error){await session?.end().catch(()=>{});this.say(`进入VR失败：${String(error)}`);}
  finally{this.xrBusy=false;if(!this.disposed){this.vrButton.disabled=false;this.options.activity(this.active);}}
 }
 private xrCaptureAt=0;
 private xrStart=()=>{
  if(this.disposed)return;this.options.beforeEnter();this.simulation.exit();
  const c=this.camera;this.savedXR={position:c.position.clone(),quaternion:c.quaternion.clone(),target:this.controls.target.clone(),fov:c.fov,near:c.near,enabled:this.controls.enabled,rotate:this.controls.autoRotate};
  const point=observationPoints[this.point];this.rig.position.fromArray(point.position);
  this.rig.rotation.y=Math.atan2(point.position[0]-point.target[0],point.position[2]-point.target[2]);
  this.scene.add(this.rig);this.rig.add(c);this.rig.updateMatrixWorld(true);c.position.set(0,0,0);c.quaternion.identity();c.near=.08;c.updateProjectionMatrix();
  this.controls.enabled=false;this.controls.autoRotate=false;this.vrButton.textContent='退出真实VR';this.xrCaptureAt=performance.now()+5000;
  this.options.activity(true);this.say('真实XR会话：姿态由运行时逐帧追踪；请在原地观察。');
 };
 private xrEnd=()=>{
  this.cancel('XR会话结束，未完成的实验已取消');
  if(this.savedXR){const saved=this.savedXR;this.camera.removeFromParent();this.rig.removeFromParent();this.camera.position.copy(saved.position);this.camera.quaternion.copy(saved.quaternion);this.camera.fov=saved.fov;this.camera.near=saved.near;this.camera.updateProjectionMatrix();this.controls.target.copy(saved.target);this.controls.enabled=saved.enabled;this.controls.autoRotate=saved.rotate;this.savedXR=undefined;}
  if(!this.disposed){this.simulateButton.textContent='开始头显模拟';this.vrButton.textContent='进入真实VR';this.options.activity(false);this.options.changed();if(this.xrCapture){this.downloadCapture(this.xrCapture);this.xrCapture=undefined;}}
 };
 metadata(){
  const gl=this.renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');const size=this.renderer.getDrawingBufferSize(new THREE.Vector2());
  return {timestamp:new Date().toISOString(),mode:this.renderer.xr.isPresenting?'webxr-device-session':this.simulation.active?'desktop-headset-simulation':'desktop-orbit',deviceClaim:'浏览器会话模式不能证明实际物理头显；真实设备型号由实验者另填',userAgent:navigator.userAgent,hardwareConcurrency:navigator.hardwareConcurrency,gpu:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'未公开',webgl:gl.getParameter(gl.VERSION),viewport:[innerWidth,innerHeight],drawingBuffer:size.toArray(),pixelRatio:this.renderer.getPixelRatio(),quality:this.options.quality,point:this.point,observation:observationPoints[this.point],cameraPosition:this.camera.getWorldPosition(new THREE.Vector3()).toArray(),cameraQuaternion:this.camera.getWorldQuaternion(new THREE.Quaternion()).toArray(),projectionMatrix:this.camera.projectionMatrix.toArray(),culling:this.culling,shadows:this.shadows,lod:this.options.lodState(),xrFrameRate:this.renderer.xr.getSession()?.frameRate??null,scope:'桌面帧间隔/JS提交时间；非GPU计时，非真实头显延迟'};
 }
 run(settings:ExperimentOptions={}):Promise<Record<string,unknown>>{
  if(this.experiment)return Promise.reject(Error('已有实验正在运行'));
  if(!this.ready)return Promise.reject(Error('模型尚未加载稳定'));
  if(!this.active)return Promise.reject(Error('请先选择观察点并开始头显模拟或真实XR'));
  const warmup=settings.warmupMs??5000,duration=settings.sampleMs??15000;
  if(!Number.isFinite(warmup)||!Number.isFinite(duration)||warmup<0||duration<100)return Promise.reject(Error('无效采样时长'));
  this.configure(settings);this.previousControlsEnabled=this.controls.enabled;this.controls.enabled=false;
  const now=performance.now();this.say('实验进行中：预热后连续采样，请保持视角与窗口不变。');
  return new Promise((resolve,reject)=>{this.experiment={warmupEnd:now+warmup,end:now+warmup+duration,previous:0,frames:[],resolve,reject,metadata:this.metadata(),settings:{...settings,warmupMs:warmup,sampleMs:duration}};});
 }
 afterRender(now:number,submitMs:number){
  if(this.pendingCapture&&this.renderer.xr.isPresenting&&now>=this.xrCaptureAt){this.pendingCapture=false;try{this.xrCapture=this.capture();}catch(error){this.say(String(error));}}
  const experiment=this.experiment;if(!experiment)return;
  if(this.renderer.getContext().isContextLost()){this.cancel('WebGL上下文丢失，实验取消');return;}
  if(document.hidden){this.cancel('页面进入后台，实验无效，请重新采集');return;}
  if(now<experiment.warmupEnd)return;
  const info=this.renderer.info.render;
  if(experiment.previous)experiment.frames.push({intervalMs:now-experiment.previous,submitMs,calls:info.calls,triangles:info.triangles});
  experiment.previous=now;
  if(now>=experiment.end){this.experiment=undefined;this.controls.enabled=this.previousControlsEnabled;
   if(!experiment.frames.length){experiment.reject(Error('无有效帧'));return;}
   const result={version:1,...experiment.metadata,settings:experiment.settings,summary:summarizeFrames(experiment.frames),frames:experiment.frames,endedAt:new Date().toISOString(),lodAtEnd:this.options.lodState()};
   this.say(`采样完成：${result.summary.fps.toFixed(1)}提交帧/秒；平均${result.summary.meanCalls.toFixed(0)}次绘制调用。`);experiment.resolve(result);
  }
 }
 cancel(reason:string){if(this.experiment){this.controls.enabled=this.previousControlsEnabled;this.experiment.reject(Error(reason));this.experiment=undefined;this.say(reason);}}
 capture():Capture{
  if(!this.active)throw Error('请先进入模拟或XR');if(this.experiment)throw Error('采样期间不截图，避免污染帧统计');if(this.renderer.getContext().isContextLost())throw Error('图形上下文已丢失');
  const xr=this.renderer.xr.isPresenting;const source=xr?this.renderer.xr.getCamera().cameras[0]:this.camera;if(!source)throw Error('没有有效XR眼相机');
  const camera=new THREE.PerspectiveCamera();camera.projectionMatrix.copy(source.projectionMatrix);camera.projectionMatrixInverse.copy(source.projectionMatrixInverse);source.matrixWorld.decompose(camera.position,camera.quaternion,camera.scale);camera.updateMatrixWorld(true);
  const width=1280,height=Math.round(width*source.projectionMatrix.elements[0]/source.projectionMatrix.elements[5]);
  const target=new THREE.WebGLRenderTarget(width,height);target.texture.colorSpace=THREE.SRGBColorSpace;
  const oldTarget=this.renderer.getRenderTarget(),enabled=this.renderer.xr.enabled;const pixels=new Uint8Array(width*height*4);let dataUrl:string;
  try{this.renderer.xr.enabled=false;this.renderer.setRenderTarget(target);this.renderer.render(this.scene,camera);this.renderer.readRenderTargetPixels(target,0,0,width,height,pixels);
   const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;const ctx=canvas.getContext('2d')!,image=ctx.createImageData(width,height);
   for(let y=0;y<height;y++)image.data.set(pixels.subarray((height-y-1)*width*4,(height-y)*width*4),y*width*4);ctx.putImageData(image,0,0);
   ctx.fillStyle='#102b24dd';ctx.fillRect(0,height-42,width,42);ctx.fillStyle='#ffffff';ctx.font='18px sans-serif';ctx.fillText(`${observationPoints[this.point].name} | ${xr?'WebXR会话单眼重渲染（设备信息见JSON）':'头显视角模拟渲染 · 非真实设备实测'}`,18,height-15);dataUrl=canvas.toDataURL('image/png');
  }finally{this.renderer.setRenderTarget(oldTarget);this.renderer.xr.enabled=enabled;target.dispose();this.options.changed();}
  return {dataUrl,metadata:{...this.metadata(),captureWidth:width,captureHeight:height,captureMethod:'同一场景、当前相机投影的离屏重渲染；不包含XR合成器畸变/时间扭曲，不是光学镜片实拍',eye:xr?'first-view':'simulation',projectionMatrix:source.projectionMatrix.toArray()}};
 }
 private downloadCapture(shot:Capture){saveFile(`campus-${this.point}-view.png`,shot.dataUrl);saveFile(`campus-${this.point}-view.json`,new Blob([JSON.stringify(shot.metadata,null,2)],{type:'application/json'}));}
 dispose(){
  this.disposed=true;this.cancel('页面已卸载');this.simulation.exit();this.renderer.xr.removeEventListener('sessionstart',this.xrStart);this.renderer.xr.removeEventListener('sessionend',this.xrEnd);this.xrEnd();void this.renderer.xr.getSession()?.end().catch(()=>{});
  this.renderer.domElement.removeEventListener('pointerdown',this.down);this.renderer.domElement.removeEventListener('pointermove',this.move);this.renderer.domElement.removeEventListener('pointerup',this.up);this.renderer.domElement.removeEventListener('pointercancel',this.up);this.renderer.domElement.removeEventListener('webglcontextlost',this.contextLost);window.removeEventListener('keydown',this.key);document.removeEventListener('visibilitychange',this.visibility);this.panel.remove();
 }
}
