const {chromium}=require('C:/Users/Lumin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
(async()=>{
 const tag=process.argv[2]||'baseline',out=__dirname,root=path.resolve(out,'../../..');
 const integration=JSON.parse(fs.readFileSync(path.join(out,'integration.json'))),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try {
 const context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 const page=await context.newPage(),errors=[],failed=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failed.push({url:r.url(),status:r.status()})});
 const t=Date.now();await page.goto('http://localhost:5188/?closeoutMetrics=1');
 await page.waitForFunction(()=>window.__campusCloseout?.ready(),{},{timeout:180000});
 const load=Date.now()-t,views=[];
 for(const index of [2,3,1]){
  await page.evaluate(i=>window.__campusCloseout.view(i),index);await page.waitForTimeout(4000);
  await page.evaluate(()=>window.__campusCloseout.reset());await page.waitForTimeout(10000);
  const m=await page.evaluate(()=>window.__campusCloseout.metrics());const f=m.frames.filter(v=>v>0).sort((a,b)=>a-b);
  views.push({...m,presetIndex:index,frames:undefined,frameCount:f.length,medianFrameMs:f[Math.floor(f.length*.5)],p95FrameMs:f[Math.floor(f.length*.95)],medianFps:1000/f[Math.floor(f.length*.5)]});
  await page.screenshot({path:path.join(out,`${tag}-campus-view-${index}.png`)});
 }
 await page.evaluate(()=>window.__campusCloseout.trees(false));await page.waitForTimeout(1000);
 await page.screenshot({path:path.join(out,`${tag}-campus-no-trees.png`)});
 await page.evaluate(()=>window.__campusCloseout.trees(true));
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(1500);
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
 await page.screenshot({path:path.join(out,`${tag}-campus-narrow.png`)});
 const production_assets=[integration.landscape,integration.building,integration.vegetation_reused].map(a=>({...a,sha256:sha(path.join(root,'web/public',a.url))}));
 const result={tag,source_sha256:integration.source_sha256,page_tsx_sha256:sha(path.join(root,'web/app/page.tsx')),production_assets,browser:await browser.version(),headless:true,loading:'Fresh browser context, local HTTP; operating-system cache unspecified',coldContextLocalLoadMs:load,network:'loopback; no public-network bandwidth claim',resolution:[1920,1080],pixelRatio:1,measurementSeconds:10,views,errors,failed,narrowOverflow:overflow};
 fs.writeFileSync(path.join(out,`${tag}-performance.json`),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result,null,2));if(errors.length||failed.length||overflow)process.exitCode=1;
 } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1)});
