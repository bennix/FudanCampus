// Local-only CDP harness; connects solely to the isolated browser on localhost.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const out=fileURLToPath(new URL('../../课程论文初稿/实验记录/webxr-2026-11-14/',import.meta.url));await fs.mkdir(out,{recursive:true});
const targets=await (await fetch('http://localhost:9226/json/list')).json();
const target=targets.find(t=>t.type==='page'&&t.url.startsWith('http://localhost:5173/'));if(!target)throw Error('No local campus page');
const socket=new WebSocket(target.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
let sequence=0;const pending=new Map(),errors=[];
socket.onmessage=({data})=>{const message=JSON.parse(data);if(message.id){const task=pending.get(message.id);pending.delete(message.id);if(message.error)task.reject(Error(JSON.stringify(message.error)));else task.resolve(message.result);}else if(message.method==='Runtime.exceptionThrown')errors.push(message.params);};
const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
const evaluate=async expression=>{const result=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result.value;};
await send('Runtime.enable');await send('Page.enable');
const mode=process.argv[2]??'inspect';
try{
 if(mode==='inspect'){console.log(JSON.stringify(await evaluate('({title:document.title,lab:!!window.campusLab,ready:window.campusLab?.ready,lod:(()=>{const l=window.campusLab?.metadata().lod;return l&&{assets:l.assets,ready:l.ready,pending:l.pending,unready:l.tiers.filter(t=>!t.ready||t.tier!==t.wanted).slice(0,8)}})(),text:document.body.innerText.slice(-500)})'),null,2));}
 else if(mode==='reload'){await send('Page.reload',{ignoreCache:true});console.log('Reload requested');}
 else if(mode==='network'){console.log(JSON.stringify(await evaluate(`(async()=>{const m=await(await fetch('/campus-lod.json')).json();return Promise.all(m.assets.filter(a=>['buildings-17','buildings-55','buildings-3','shared-00'].includes(a.id)).map(async a=>{const u=a.tiers[0].url;const r=await fetch('/'+u);return {id:a.id,url:u,status:r.status,type:r.headers.get('content-type'),bytes:(await r.arrayBuffer()).byteLength};}));})()`),null,2));}
 else if(mode==='verify'){
  await send('Page.bringToFront');
  await evaluate(`(async()=>{for(let n=0;n<240;n++){if(window.campusLab?.ready)return true;await new Promise(r=>setTimeout(r,1000));}throw Error('加载超时');})()`);
  const original=await evaluate('window.campusLab.metadata().cameraPosition');
  await evaluate("window.campusLab.observe('teaching4');window.campusLab.simulate(true)");
  const before=await evaluate('window.campusLab.metadata().cameraQuaternion');
  await send('Input.dispatchMouseEvent',{type:'mousePressed',x:900,y:450,button:'left',clickCount:1});
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:1020,y:500,button:'left',buttons:1});
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:1020,y:500,button:'left',clickCount:1});
  await evaluate('new Promise(r=>setTimeout(r,800))');
  const after=await evaluate('window.campusLab.metadata().cameraQuaternion');
  const locked=await evaluate("document.querySelector('nav').inert&&document.querySelector('aside').inert");
  await evaluate('window.campusLab.simulation.reset()');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape'});
  const restored=await evaluate('({active:window.campusLab.active,position:window.campusLab.metadata().cameraPosition})');
  if(JSON.stringify(before)===JSON.stringify(after)||!locked||restored.active||original.some((v,i)=>Math.abs(v-restored.position[i])>1e-8))throw Error('Pointer/Escape/restore/lock failed');
  await evaluate(`(async()=>{for(let n=0;n<240;n++){if(window.campusLab.ready)return;await new Promise(r=>setTimeout(r,500));}throw Error('LOD timeout');})()`);
  await evaluate('window.campusLab.simulate(true)');
  await evaluate(`(async()=>{await new Promise(r=>setTimeout(r,1500));for(let n=0;n<240;n++){if(window.campusLab.ready)return;await new Promise(r=>setTimeout(r,500));}throw Error('LOD timeout');})()`);
  const visibility=await evaluate(`(async()=>{const result=window.campusLab.run().then(()=> 'unexpected completion',e=>e.message);Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));delete document.hidden;return await result;})()`);
  const context=await evaluate(`(async()=>{const result=window.campusLab.run().then(()=> 'unexpected completion',e=>e.message);const canvas=document.querySelector('.viewport canvas');canvas.dispatchEvent(new Event('webglcontextlost',{cancelable:true}));const message=await result;canvas.dispatchEvent(new Event('webglcontextrestored'));return message;})()`);
  if(!visibility.includes('后台')||!context.includes('上下文丢失'))throw Error('Invalid experiment not canceled');
  await evaluate("window.campusLab.simulate(false);document.querySelector('.campus-lab').open=true");
  const shot=await send('Page.captureScreenshot',{format:'png'});await fs.writeFile(path.join(out,'web-ui-final.png'),Buffer.from(shot.data,'base64'));
  const report={pointerChanged:true,restore:true,controlsLocked:true,visibilityCancel:visibility,syntheticContextEventCancel:context,before,after,original,restored};
  await fs.writeFile(path.join(out,'browser-interaction-verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }
 else{
  await send('Page.bringToFront');
  await evaluate(`(async()=>{for(let n=0;n<180;n++){if(window.campusLab?.ready)return true;await new Promise(r=>setTimeout(r,1000));}throw Error('模型加载超时');})()`);
  const results=[];
  for(const point of ['teaching4','chemistry']){
   await evaluate(`(async()=>{for(let n=0;n<180;n++){if(window.campusLab?.ready)return true;await new Promise(r=>setTimeout(r,1000));}throw Error('切换前LOD加载超时');})()`);
   await evaluate(`window.campusLab.observe('${point}');window.campusLab.simulate(true)`);
   // LOD transitions triggered by the new eye-level position must finish before trials.
   await evaluate(`(async()=>{await new Promise(r=>setTimeout(r,2500));for(let n=0;n<120;n++){if(window.campusLab.ready)return true;await new Promise(r=>setTimeout(r,500));}throw Error('LOD未稳定');})()`);
   if(mode==='experiment'){
    // Three paired rounds, with reversed order to reduce warm-up/order bias.
    for(let round=0;round<3;round++){
     const variants=[{name:'no-culling',culling:false,shadows:true},{name:'cached-shadow',culling:true,shadows:true},{name:'no-shadow',culling:true,shadows:false}];if(round%2)variants.reverse();
     for(const variant of variants){
      const file=path.join(out,`${point}-${round+1}-${variant.name}.json`);
      try{const existing=JSON.parse(await fs.readFile(file,'utf8'));if(existing.lod?.ready===200){existing.round=round+1;existing.variant=variant.name;results.push(existing);console.log(`Reuse ${point}/${round+1}/${variant.name}`);continue;}}catch{}
      const result=await evaluate(`window.campusLab.run(${JSON.stringify({...variant,warmupMs:2000,sampleMs:5000})})`);
      result.round=round+1;result.variant=variant.name;results.push(result);
      await fs.writeFile(file,JSON.stringify(result,null,2));
      console.log(JSON.stringify({point,round:round+1,variant:variant.name,...result.summary}));
     }
    }
   }
   await evaluate('window.campusLab.configure({culling:true,shadows:true})');
   await evaluate('new Promise(r=>setTimeout(r,1000))');
   const capture=await evaluate('window.campusLab.capture()');
   await fs.writeFile(path.join(out,`${point}-simulation.png`),Buffer.from(capture.dataUrl.split(',')[1],'base64'));
   await fs.writeFile(path.join(out,`${point}-simulation.json`),JSON.stringify(capture.metadata,null,2));
   // Verify input, smoothing and restore using the same public interactions as the page.
   const interaction=await evaluate(`(async()=>{const lab=window.campusLab;const before=lab.metadata().cameraQuaternion;lab.simulation.setHead(.6,.2);await new Promise(r=>setTimeout(r,500));const after=lab.metadata().cameraQuaternion;lab.simulation.reset();const reset=lab.metadata().cameraQuaternion;lab.simulate(false);return {before,after,reset,active:lab.active};})()`);
   if(JSON.stringify(interaction.before)===JSON.stringify(interaction.after)||interaction.active)throw Error('Simulation interaction failed');
   await fs.writeFile(path.join(out,`${point}-interaction.json`),JSON.stringify(interaction,null,2));
  }
  if(results.length)await fs.writeFile(path.join(out,'results.json'),JSON.stringify(results,null,2));
  await evaluate("document.querySelector('.campus-lab').open=true");
  const screenshot=await send('Page.captureScreenshot',{format:'png'});await fs.writeFile(path.join(out,'web-ui.png'),Buffer.from(screenshot.data,'base64'));
 }
 await fs.writeFile(path.join(out,`browser-errors-${mode}.json`),JSON.stringify(errors,null,2));
 if(errors.length)throw Error(`${errors.length} browser exceptions`);
}finally{socket.close();}
