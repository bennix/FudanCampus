import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const html=new URL('./论文更新稿_三联图对比分析.html',import.meta.url),pdf=new URL('./论文更新稿_三联图对比分析.pdf',import.meta.url);
const tab=await(await fetch('http://localhost:9226/json/new?'+encodeURIComponent(html.href),{method:'PUT'})).json();
const socket=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
let id=0;const waiting=new Map();socket.onmessage=({data})=>{const m=JSON.parse(data);if(!m.id)return;const p=waiting.get(m.id);waiting.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);};
socket.onclose=event=>{for(const task of waiting.values())task.reject(Error(`CDP closed ${event.code}: ${event.reason}`));waiting.clear();};
const send=(method,params={})=>new Promise((resolve,reject)=>{const key=++id;waiting.set(key,{resolve,reject});socket.send(JSON.stringify({id:key,method,params}));});
try{
 await send('Page.enable');await send('Runtime.enable');
 for(let n=0;n<60;n++){const r=await send('Runtime.evaluate',{expression:"document.readyState==='complete'&&Array.from(document.images).every(i=>i.complete)",returnByValue:true});if(r.result.value)break;await new Promise(r=>setTimeout(r,500));}
 await send('Runtime.evaluate',{expression:'document.fonts.ready',awaitPromise:true});
 const result=await send('Page.printToPDF',{printBackground:true,preferCSSPageSize:true,displayHeaderFooter:false,transferMode:'ReturnAsStream'});
 const chunks=[];while(true){const chunk=await send('IO.read',{handle:result.stream,size:65536});chunks.push(Buffer.from(chunk.data,chunk.base64Encoded?'base64':'utf8'));if(chunk.eof)break;}await send('IO.close',{handle:result.stream});
 const bytes=Buffer.concat(chunks);await fs.writeFile(pdf,bytes);
 console.log(JSON.stringify({path:fileURLToPath(pdf),bytes:bytes.length,pages:(bytes.toString('latin1').match(/\/Type\s*\/Page\b/g)||[]).length,method:'浏览器阅读预览，非Word原生排版导出'}));
}finally{await send('Page.close').catch(()=>{});socket.close();}
