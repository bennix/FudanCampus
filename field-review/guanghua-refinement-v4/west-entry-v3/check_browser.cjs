const {chromium}=require('C:/Users/Lumin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const out=__dirname;
(async()=>{
 const errors=[],failedResponses=[],requests=[];
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1080}});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('/favicon.ico'))failedResponses.push({url:r.url(),status:r.status()});if(r.url().includes('.glb'))requests.push({url:r.url(),status:r.status()});});
  await page.goto('http://127.0.0.1:8772/field-review/guanghua-refinement-v4/west-entry-v3/review.html');
  await page.waitForFunction(()=>window.__ready||window.__error,null,{timeout:180000});
  assert(await page.evaluate(()=>window.__ready),await page.evaluate(()=>window.__error));
  const model=await page.evaluate(()=>{
   const counts={},urns=[],paths=[],old=[];
   window.__scene.updateMatrixWorld(true);
   window.__scene.traverse(o=>{
    if(!o.isMesh)return;const fid=o.userData.feature_id;counts[fid]=(counts[fid]||0)+1;
    if((fid==='W_ENTRY'||fid==='E_ENTRY')&&o.name.endsWith('pedestal_core')){
      o.geometry.computeBoundingBox();const bb=o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
      urns.push({name:o.name,fid,min:bb.min.toArray(),max:bb.max.toArray(),source:o.userData.source_component});
    }
    if(o.name.includes('west_garden')&&fid==='WPATH')paths.push({name:o.name,join:o.userData.west_entry_join});
    if(o.name.startsWith('FURNITURE__urn')||o.name.startsWith('W_ENTRY_recessed'))old.push(o.name);
   });
   return {file:window.__modelFile,meshCount:window.__meshCount,render:window.__renderInfo,counts,urns,paths,old};
  });
  assert.equal(model.file,'west-entry-aligned-v3.glb');assert(model.meshCount>1200);assert.equal(model.urns.length,4);assert.equal(model.old.length,0);
  for(const fid of ['W_ENTRY','E_ENTRY','WOPEN','WOPEN_S','LAWN','POET_DONKEY'])assert(model.counts[fid]>0,fid);
  for(const u of model.urns){const x=(u.min[0]+u.max[0])/2,z=(u.min[2]+u.max[2])/2;assert(Math.abs(z+79.06448215333579)<.002);if(u.fid==='W_ENTRY')assert(Math.min(Math.abs(x+30.5),Math.abs(x+23.5))<.002);}
  const heights=model.urns.map(u=>u.max[1]-u.min[1]);assert(Math.max(...heights)-Math.min(...heights)<.002);
  assert.equal(model.paths.filter(p=>p.join).length,2);
  const views=['west','westFront','westTop','join','paired','east','overall'];
  for(const view of views){
   await page.locator(`[data-view="${view}"]`).click();
   await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   assert.equal(await page.evaluate(()=>window.__view),view);
   assert((await page.evaluate(()=>window.__renderInfo.triangles))>0);
   await page.locator('canvas').screenshot({path:path.join(out,`web-${view}.png`)});
  }
  await page.locator('#toggle').click();
  assert.equal(await page.locator('#toggle').textContent(),'显示树叶');
  const hidden=await page.evaluate(()=>{let n=0;window.__scene.traverse(o=>{if(o.isMesh&&!o.visible)n++});return n});assert(hidden>0);
  await page.locator('#toggle').click();
  const images=await page.evaluate(async()=>{await Promise.all([...document.images].map(im=>im.decode().catch(()=>{})));return [...document.images].map(im=>({src:im.getAttribute('src'),width:im.naturalWidth,height:im.naturalHeight}));});
  assert(images.every(im=>im.width>0&&im.height>0));
  await page.setViewportSize({width:390,height:844});await page.locator('[data-view="west"]').click();
  await page.screenshot({path:path.join(out,'web-mobile.png')});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);assert(!overflow);
  assert.deepEqual(errors,[]);assert.deepEqual(failedResponses,[]);assert.equal(requests.length,1);assert.equal(requests[0].status,200);
  const report={reviewedAt:new Date().toISOString(),ready:true,model,views,images,foliageToggle:true,hiddenLeafMeshes:hidden,mobileWidth:390,mobileNoOverflow:true,errors,failedResponses,assetRequests:requests};
  fs.writeFileSync(path.join(out,'browser-validation.json'),JSON.stringify(report,null,2));
  console.log('WEST_ENTRY_BROWSER_OK',JSON.stringify({meshes:model.meshCount,urns:model.urns.length,views:views.length,images:images.length}));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
