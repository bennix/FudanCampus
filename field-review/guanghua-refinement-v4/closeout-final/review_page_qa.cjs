/* Static delivery-page verification. Does not open the 3D campus. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require('C:/Users/Lumin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=__dirname,sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{
 const url=process.argv[2]||'http://127.0.0.1:8766/field-review/guanghua-refinement-v4/closeout-final/review.html';
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),failed=[],errors=[];
 try{
  page.on('response',r=>{if(r.status()>=400)failed.push({url:r.url(),status:r.status()});});
  page.on('pageerror',e=>errors.push(e.message));await page.goto(url);
  const embedded3D=await page.locator('iframe,canvas').count();
  await page.locator('details').evaluateAll(xs=>xs.forEach(x=>x.open=true));
  await page.locator('img').evaluateAll(xs=>xs.forEach(x=>x.loading='eager'));
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete),null,{timeout:120000});
  const broken=await page.locator('img').evaluateAll(xs=>xs.filter(i=>!i.naturalWidth).map(i=>i.src));
  await page.screenshot({path:path.join(out,'review-desktop.png')});
  await page.setViewportSize({width:390,height:844});
  const narrowOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
  await page.screenshot({path:path.join(out,'review-narrow.png')});
  const result={source_sha256:sha(path.join(out,'guanghua-closeout-final.blend')),review_html_sha256:sha(path.join(out,'review.html')),url,
   browser:await browser.version(),headless:true,desktop:[1440,1000],narrow:[390,844],embedded3D,images:await page.locator('img').count(),
   cards:await page.locator('article').count(),failed,errors,broken,narrowOverflow,
   screenshots:['review-desktop.png','review-narrow.png'].map(name=>({name,sha256:sha(path.join(out,name))})),
   pass:!failed.length&&!errors.length&&!broken.length&&!narrowOverflow&&!embedded3D,
   scope:'Static review layout, all images and local HTTP requests. No 3D campus frame or performance measurement.'};
  fs.writeFileSync(path.join(out,'review-page-validation.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result,null,2));if(!result.pass)process.exitCode=1;
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
