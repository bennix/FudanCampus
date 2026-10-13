const {chromium}=require('C:/Users/Lumin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
(async()=>{
 const out=path.resolve(__dirname,'../field-review/east-garden-v2');
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[],failed=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failed.push(r.url())});
 await page.goto('http://127.0.0.1:8768/field-review/east-garden-v2/review.html',{waitUntil:'domcontentloaded',timeout:60000});
 await page.waitForFunction(()=>window.__modelReady||window.__modelError,{},{timeout:60000});
 const info=await page.evaluate(()=>({ready:window.__modelReady,error:window.__modelError,...window.__modelInfo}));
 assert(info.ready,info.error);assert(info.textured>25);assert(info.crowns>0);
 for(const id of ['ETERR','ERAMP','EPATH','ESKY','EOPEN','EOPEN_S'])assert(info.ids.includes(id));
 await page.locator('.viewer').screenshot({path:path.join(out,'web-overview.png')});
 for(const key of ['top','terrace','entry','ramp','skylight','north']){
  await page.locator(`[data-view="${key}"]`).click();assert.equal(await page.evaluate(()=>window.__activeView),key);
  if(['terrace','top'].includes(key))await page.locator('.viewer').screenshot({path:path.join(out,`web-${key}.png`)});
 }
 await page.locator('[data-view="overview"]').click();await page.locator('#trees').click();assert(await page.evaluate(()=>window.__treesVisible));
 await page.locator('.viewer').screenshot({path:path.join(out,'web-trees.png')});await page.locator('#trees').click();
 await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 fs.writeFileSync(path.join(out,'preview-validation.json'),JSON.stringify({...info,all_seven_views:true,tree_toggle:true,page_errors:errors,failed_responses:failed,mobile_no_overflow:true},null,2));
 await browser.close();console.log(info);
})().catch(e=>{console.error(e);process.exit(1)});
