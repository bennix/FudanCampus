import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {smoothHead, observationPoints, shouldRenderFrame} from '../lib/immersive-policy.ts';
import {summarizeFrames} from '../lib/frame-metrics.ts';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
let source=await readFile(new URL('../lib/head-simulation.ts',import.meta.url),'utf8');
source=source.replace("'three'",JSON.stringify(import.meta.resolve('three'))).replace("'./immersive-policy'",JSON.stringify(new URL('../lib/immersive-policy.ts',import.meta.url).href));
const {HeadSimulation}=await import('data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText).toString('base64'));

test('模拟旋转平滑在30/60/90Hz下具有相同收敛结果，采用四元数最短路径',()=>{
 const target=new THREE.Quaternion().setFromEuler(new THREE.Euler(.3,Math.PI-.01,0,'YXZ'));
 const results=[30,60,90].map(hz=>{const q=new THREE.Quaternion();for(let i=0;i<hz;i++)smoothHead(q,target,1/hz);return q;});
 assert.ok(results[0].angleTo(results[2])<1e-7);
 const q=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),-Math.PI+.01);
 smoothHead(q,target,1);assert.ok(q.angleTo(target)<.001);
});
test('XR/实验每帧提交，不受桌面30/60Hz限帧或脏帧影响',()=>{
 assert.equal(shouldRenderFrame(true,false,false,1,30),true);
 assert.equal(shouldRenderFrame(false,true,false,1,60),true);
 assert.equal(shouldRenderFrame(false,false,false,20,60),false);
 assert.equal(shouldRenderFrame(false,false,true,1,60),false);
 assert.equal(shouldRenderFrame(false,false,true,20,60),true);
});
test('观察点为米制站立地面坐标，无遮挡建筑外侧',()=>{
 assert.deepEqual(Object.keys(observationPoints),['teaching4','chemistry']);
 for(const point of Object.values(observationPoints)){assert.equal(point.position[1],0);assert.equal(point.eyeHeight,1.65);}
});
test('帧统计拒绝无效值并保留可复核口径，不把平均瞬时FPS当整体FPS',()=>{
 const result=summarizeFrames([{intervalMs:10,submitMs:1,calls:10,triangles:100},{intervalMs:30,submitMs:3,calls:30,triangles:300}]);
 assert.equal(result.fps,50);assert.equal(result.meanIntervalMs,20);assert.equal(result.p95IntervalMs,30);assert.equal(result.meanCalls,20);
 assert.equal(result.meanSubmitMs,2);assert.equal(result.samples,2);
 assert.throws(()=>summarizeFrames([]));
 assert.throws(()=>summarizeFrames([{intervalMs:NaN,submitMs:1,calls:1,triangles:1}]));
});
test('模拟进入/退出恢复相机、目标和控制器状态；复位不累计偏移',()=>{
 const camera=new THREE.PerspectiveCamera(43,1,1,4500);camera.position.set(5,10,20);camera.lookAt(0,3,0);
 const original=camera.clone();const controls={target:new THREE.Vector3(0,3,0),enabled:true,autoRotate:true};
 const sim=new HeadSimulation(camera,controls);
 sim.enter('teaching4');assert.equal(controls.enabled,false);assert.equal(camera.position.y,1.65);
 sim.setHead(1,.4);sim.update(.1);const moved=camera.quaternion.clone();
 sim.reset();assert.ok(camera.quaternion.angleTo(moved)>.1);
 sim.exit();assert.deepEqual(camera.position.toArray(),original.position.toArray());
 assert.ok(camera.quaternion.angleTo(original.quaternion)<1e-7);assert.equal(camera.fov,43);assert.equal(camera.near,1);
 assert.equal(controls.enabled,true);assert.equal(controls.autoRotate,true);sim.exit();
});
test('仰视建筑后纯水平转头不引入地平线侧倾',()=>{
 const camera=new THREE.PerspectiveCamera(),controls={target:new THREE.Vector3(),enabled:true,autoRotate:false};const sim=new HeadSimulation(camera,controls);
 sim.enter('teaching4');sim.setHead(Math.PI/2,0);sim.update(3);
 const euler=new THREE.Euler().setFromQuaternion(camera.quaternion,'YXZ');assert.ok(Math.abs(euler.z)<1e-6);sim.exit();
});
