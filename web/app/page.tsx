'use client';
import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
type LabelMode='auto'|'full'|'off';
type Building={id:string;name:string;position:[number,number,number];source:string;category:string};
const views:{name:string;p:number[];t:number[];fov?:number}[]=[
 {name:'全校鸟瞰',p:[-650,950,880],t:[-20,0,-260]},
 {name:'光华楼',p:[131.2,7,-120.8],t:[131.2,35,-224.8],fov:55},
 {name:'理科图书馆',p:[-93.8,3.5,-58.8],t:[-93.8,5.5,-89.5],fov:52},
 {name:'复旦校门',p:[-46,3,27.6],t:[-40,4,-6.4]},
 {name:'逸夫楼',p:[-89,9,-186.2],t:[-120,11,-255.2]},
 {name:'逸夫科技楼',p:[-190,8,-153.4],t:[-208,14,-198.4]},
 {name:'主校区',p:[-380,500,460],t:[30,0,-160]},
 {name:'地图俯视',p:[-20,1150,-319],t:[-20,0,-320]},
 {name:'光华楼与东区',p:[580,410,250],t:[190,20,-200]},
 {name:'北区宿舍',p:[-650,380,-50],t:[-385,0,-520]},
];
export default function Home(){
 const mount=useRef<HTMLDivElement>(null);
 const api=useRef<{view:(n:number)=>void;trees:(v:boolean)=>void;rotate:(v:boolean)=>void;labels:(v:LabelMode)=>void}|null>(null);
 const [status,setStatus]=useState('正在载入校园…');const [active,setActive]=useState(0);const [trees,setTrees]=useState(true);const [rotate,setRotate]=useState(false);const [reference,setReference]=useState<'map'|'photo'|'yifu'|'science'|'guanghua'|'library'|'gate'|null>(null);const [labelMode,setLabelMode]=useState<LabelMode>('auto');
 useEffect(()=>{if(!mount.current)return;const el=mount.current;
 const scene=new THREE.Scene();scene.background=new THREE.Color('#cdd6d6');scene.fog=new THREE.Fog('#cdd6d6',1800,3400);
 const camera=new THREE.PerspectiveCamera(43,1,1,4500);camera.position.set(-650,950,880);
 const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.7));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.2;el.appendChild(renderer.domElement);
 const layer=document.createElement('div');layer.className='building-labels';layer.setAttribute('aria-label','建筑浮动标签');el.appendChild(layer);
 const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(-20,0,-260);controls.enableDamping=true;controls.minDistance=25;controls.maxDistance=2200;controls.maxPolarAngle=Math.PI*.48;controls.autoRotateSpeed=.35;
 scene.add(new THREE.HemisphereLight(0xe8f0ff,0x73715b,2.3));const sun=new THREE.DirectionalLight(0xfff1d5,3);sun.position.set(-340,650,320);sun.castShadow=true;sun.shadow.mapSize.set(4096,4096);Object.assign(sun.shadow.camera,{left:-800,right:800,top:800,bottom:-800,near:1,far:1800});sun.shadow.bias=-.0003;scene.add(sun);sun.target.position.set(0,0,-280);scene.add(sun.target);
 let model:THREE.Group|undefined;let canceled=false;let transition:{p:THREE.Vector3;t:THREE.Vector3}|undefined;let mode:LabelMode='auto';let showTrees=true;
 const labels:{data:Building;point:THREE.Vector3;button:HTMLButtonElement}[]=[];
 const abort=new AbortController();
 Promise.all([new GLTFLoader().loadAsync('/campus.glb?v=map-v8-gate'),fetch('/buildings.json?v=map-v8-gate',{signal:abort.signal}).then(r=>{if(!r.ok)throw Error('标签文件不可用');return r.json() as Promise<{buildings:Building[]}>;})]).then(([g,data])=>{
  if(canceled)return;model=g.scene;model.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=!o.name.includes('Continuous');o.receiveShadow=true;}if(/Canopy|Trunk/.test(o.name))o.visible=showTrees;});scene.add(model);
  for(const item of data.buildings){
   const button=document.createElement('button');button.className='building-label';button.dataset.buildingId=item.id;button.dataset.category=item.category;button.title=`${item.id} · ${item.name}`;button.setAttribute('aria-label',`${item.id} ${item.name}，点击靠近`);
   const badge=document.createElement('span');badge.className='label-id';badge.textContent=item.id;
   const name=document.createElement('span');name.className='label-name';name.textContent=item.name;button.appendChild(badge);button.appendChild(name);layer.appendChild(button);
   const point=new THREE.Vector3(...item.position);
   button.onclick=()=>{transition={p:point.clone().add(new THREE.Vector3(-75,95,115)),t:point.clone().add(new THREE.Vector3(0,-8,0))};setStatus(`${item.id} · ${item.name}`);};
   labels.push({data:item,point,button});
  }
  setStatus(`已载入 ${data.buildings.filter(b=>b.category==='building').length} 栋建筑 · 点击标签靠近`);
 }).catch(e=>{if(!canceled){console.error(e);setStatus('校园或标签载入失败，请刷新页面重试');}});
 api.current={view(n){camera.fov=views[n].fov??43;camera.updateProjectionMatrix();transition={p:new THREE.Vector3(...views[n].p as [number,number,number]),t:new THREE.Vector3(...views[n].t as [number,number,number])};},trees(v){showTrees=v;model?.traverse(o=>{if(/Canopy|Trunk/.test(o.name))o.visible=v;});},rotate(v){controls.autoRotate=v;},labels(v){mode=v;}};
 const resize=()=>{camera.aspect=el.clientWidth/el.clientHeight;camera.updateProjectionMatrix();renderer.setSize(el.clientWidth,el.clientHeight);};const observer=new ResizeObserver(resize);observer.observe(el);resize();
 const projected=new THREE.Vector3();
 renderer.setAnimationLoop(()=>{
  if(transition){camera.position.lerp(transition.p,.065);controls.target.lerp(transition.t,.065);if(camera.position.distanceTo(transition.p)<.1)transition=undefined;}
  controls.update();renderer.render(scene,camera);
  for(const item of labels){
   projected.copy(item.point).project(camera);
   const visible=mode!=='off'&&projected.z>-1&&projected.z<1&&Math.abs(projected.x)<1.08&&Math.abs(projected.y)<1.08;
   item.button.hidden=!visible;if(!visible)continue;
   item.button.style.left=`${(projected.x*.5+.5)*el.clientWidth}px`;item.button.style.top=`${(-projected.y*.5+.5)*el.clientHeight}px`;
   const distance=camera.position.distanceTo(item.point);item.button.classList.toggle('expanded',mode==='full'||distance<310||['27','65','57','3'].includes(item.data.id));
   item.button.style.zIndex=String(Math.max(1,Math.round(2200-distance)));
  }
 });
 return()=>{canceled=true;abort.abort();api.current=null;observer.disconnect();renderer.setAnimationLoop(null);controls.dispose();scene.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});renderer.dispose();el.removeChild(renderer.domElement);el.removeChild(layer);};
 },[]);
 return <main><div className="viewport" ref={mount}/><header><span className="mark">复</span><div><h1>复旦 · 校园空间</h1><p>地图校正版 · 邯郸校区北部</p></div><span className="local">本地 3D 场景</span></header>
 <nav aria-label="视角">{views.map((v,i)=><button key={v.name} className={active===i?'active':''} onClick={()=>{setActive(i);api.current?.view(i);}}><span>0{i+1}</span>{v.name}</button>)}</nav>
 <aside><label className="label-control">建筑标签<select aria-label="建筑标签显示" value={labelMode} onChange={e=>{const v=e.target.value as LabelMode;setLabelMode(v);api.current?.labels(v);}}><option value="auto">自动详略</option><option value="full">全部名称</option><option value="off">关闭</option></select></label><button className={trees?'selected':''} onClick={()=>{setTrees(!trees);api.current?.trees(!trees);}}>树木 {trees?'开':'关'}</button><button className={rotate?'selected':''} onClick={()=>{setRotate(!rotate);api.current?.rotate(!rotate);}}>环绕 {rotate?'开':'关'}</button><button className={reference?'selected':''} onClick={()=>setReference(reference?null:'map')}>地图对照</button></aside>
 {reference&&<div className="reference"><div className="reference-tabs"><button className={reference==='map'?'selected':''} onClick={()=>setReference('map')}>校园地图</button><button className={reference==='photo'?'selected':''} onClick={()=>setReference('photo')}>原始照片</button><button className={reference==='yifu'?'selected':''} onClick={()=>setReference('yifu')}>逸夫楼实景</button><button className={reference==='science'?'selected':''} onClick={()=>setReference('science')}>科技楼实景</button><button className={reference==='guanghua'?'selected':''} onClick={()=>setReference('guanghua')}>光华楼实景</button><button className={reference==='library'?'selected':''} onClick={()=>setReference('library')}>图书馆实景</button><button className={reference==='gate'?'selected':''} onClick={()=>setReference('gate')}>校门实景</button><button onClick={()=>setReference(null)} aria-label="关闭参考图片">×</button></div><a href={reference==='map'?'/campus-map.png':reference==='yifu'?'/yifu-building-front.png':reference==='science'?'/yifu-science-building.png':reference==='guanghua'?'/guanghua-building.png':reference==='library'?'/science-library-facade.png':reference==='gate'?'/fudan-gate.png':'/reference.jpg'} target="_blank" rel="noreferrer"><img src={reference==='map'?'/campus-map.png':reference==='yifu'?'/yifu-building-front.png':reference==='science'?'/yifu-science-building.png':reference==='guanghua'?'/guanghua-building.png':reference==='library'?'/science-library-facade.png':reference==='gate'?'/fudan-gate.png':'/reference.jpg'} alt={reference==='map'?'复旦大学校园地图':reference==='yifu'?'逸夫楼实景照片':reference==='science'?'逸夫科技楼实景照片':reference==='guanghua'?'光华楼实景照片':reference==='library'?'理科图书馆局部立面照片':reference==='gate'?'复旦校门参考照片':'校园沙盘原始参考照片'}/></a><p>名称与位置依据所附地图；N / A 为无法辨清原编号的楼栋。点击图片可放大。</p></div>}
 <div className="label-hint">标签跟随建筑 · 悬停显示名称 · 点击靠近</div>
 <footer><span><i/>{status}</span><span>左键旋转 · 右键平移 · 滚轮缩放</span><span className="note">地图时期名称 · 高度与外观近似</span></footer></main>
}
