const {chromium}=require('C:/Users/Lumin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const errors=[],browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1400,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8771/field-review/guanghua-refinement-v4/forecourt-v2/review.html');
 await page.waitForFunction(()=>window.__ready||window.__error,null,{timeout:180000});
 const result=await page.evaluate(()=>({ready:window.__ready,error:window.__error,meshCount:window.__meshCount,render:window.__renderInfo}));if(!result.ready)throw Error(JSON.stringify(result));
 for(const v of ['entry','top','plaza','edge','statue','statueBack','overall']){
  await page.locator(`[data-view="${v}"]`).click();
  await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  if(['entry','statue','overall'].includes(v))await page.locator('canvas').screenshot({path:path.join(__dirname,`web-${v}.png`)});
 }
 await page.locator('#toggle').click();await page.waitForFunction(()=>document.querySelector('#toggle').textContent==='显示树叶');await page.locator('#toggle').click();
 const ids=await page.evaluate(()=>{let ids=new Set;window.__scene.traverse(o=>{if(o.userData.feature_id)ids.add(o.userData.feature_id)});return [...ids]});
 if(!ids.includes('POET_DONKEY')||!ids.includes('E_ENTRY'))throw Error('New feature IDs absent');
 await page.setViewportSize({width:390,height:844});const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 fs.writeFileSync(path.join(__dirname,'browser-validation.json'),JSON.stringify({...result,errors,overflow,views:7,foliageToggle:true,featureIds:ids},null,2));
 await browser.close();if(errors.length||overflow)throw Error('Browser validation failed');console.log('FORECOURT_BROWSER_OK');
})().catch(e=>{console.error(e);process.exit(1)});
