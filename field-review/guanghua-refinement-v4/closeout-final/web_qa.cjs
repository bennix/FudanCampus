/* Independent closeout QA. Production assets and renderer are read-only here. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');
const {chromium}=require('C:/Users/Lumin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=__dirname,root=path.resolve(out,'../../..'),pub=path.join(root,'web/public');
const args=process.argv.slice(2),mode=args[0]||'visual',frozen=args.includes('--frozen');
const json=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const save=(name,v)=>fs.writeFileSync(path.join(out,name),JSON.stringify(v,null,2)+'\n');
function provenance(){
 const r=json(path.join(out,'integration.json'));
 const assets=[r.landscape,r.building,r.vegetation_reused].map(a=>{const p=path.join(pub,a.url),digest=sha(p);return {...a,sha256:digest,actual_bytes:fs.statSync(p).size,matches_registered_bytes_and_revision:fs.statSync(p).size===a.bytes&&digest.startsWith(a.revision)};});
 return {source_sha256:sha(r.source),source_matches_export:sha(r.source)===r.source_sha256,
  page_sha256:sha(path.join(root,'web/app/page.tsx')),assets,
  frozen,warning:frozen?undefined:'Preparation run only; final production QA requires --frozen after the parent confirms no competing GPU workload.'};
}
function merge(key,value){const p=path.join(out,'web-checks.json'),r=fs.existsSync(p)?json(p):{};r[key]=value;save('web-checks.json',r);}
function nativeToThree(p,conversion){const s=conversion.scale,[x,y,z]=conversion.translation_blender;return [x+p[0]*s,z+p[2]*s,-y-p[1]*s];}
function cameraViews(){
 const c=json(path.join(out,'export-conversion.json')),p=json(path.join(out,'glb-validation.json')).textNodes.find(t=>t.body==='驢背詩思');
 const target=p.min.map((v,i)=>(v+p.max[i])/2),front=[-.1391731054,0,.9902680516];
 return [
  {id:'garage-wb1',p:nativeToThree([-85,48,2.3],c),t:nativeToThree([-74.5,48,.7],c),fov:42},
  {id:'garage-wb2',p:nativeToThree([-85,70,2.3],c),t:nativeToThree([-74.5,70,.7],c),fov:42},
  {id:'garage-wb1-glyphs',p:nativeToThree([-80.7,48,2.07],c),t:nativeToThree([-74.65,48,2.07],c),fov:34},
  {id:'garage-wb2-glyphs',p:nativeToThree([-80.7,70,2.07],c),t:nativeToThree([-74.65,70,2.07],c),fov:34},
  {id:'fudan',p:nativeToThree([24.5,-1.2,2],c),t:nativeToThree([24.5,9.7,1.15],c),fov:38},
  {id:'plaque-front',p:target.map((v,i)=>v+front[i]*3.05+(i===1?.08:0)),t:target,fov:14},
  {id:'plaque-oblique',p:target.map((v,i)=>v+front[i]*3.15+[.8,.35,0][i]),t:target,fov:18},
 ];
}
async function build(){
 const {spawnSync}=require('node:child_process'),web=path.join(root,'web');
 const typecheck=spawnSync('D:/nodejs/node.exe',[path.join(web,'node_modules/typescript/bin/tsc'),'--noEmit','-p','tsconfig.campus.json'],{cwd:web,encoding:'utf8'});
 const production=spawnSync('powershell.exe',['-NoProfile','-Command',"& 'D:/nodejs/npm.cmd' run build:pages"],{cwd:web,encoding:'utf8'});
 fs.writeFileSync(path.join(out,'web-build.log'),[typecheck.stdout,typecheck.stderr,production.stdout,production.stderr].filter(Boolean).join('\n'));
 const result={...provenance(),typecheck:{command:'tsc --noEmit -p tsconfig.campus.json',exitCode:typecheck.status},productionBuild:{command:'npm run build:pages',exitCode:production.status,log:'web-build.log',log_sha256:sha(path.join(out,'web-build.log'))},pass:typecheck.status===0&&production.status===0};
 merge(frozen?'build':'preparation_build',result);console.log(JSON.stringify(result,null,2));if(!result.pass)process.exitCode=1;
}
async function decode(){
 const {NodeIO}=await import(pathToFileURL(path.join(root,'.local/model-tools/node_modules/@gltf-transform/core/dist/index.js')));
 const {ALL_EXTENSIONS}=await import(pathToFileURL(path.join(root,'.local/model-tools/node_modules/@gltf-transform/extensions/dist/index.js')));
 const {MeshoptDecoder}=await import(pathToFileURL(path.join(root,'.local/model-tools/node_modules/meshoptimizer/index.js')));
 await MeshoptDecoder.ready;
 const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
 const report=json(path.join(out,'integration.json')),source=path.join(pub,report.landscape.url),d=await io.read(source),r=d.getRoot();
 const used=r.listExtensionsUsed().map(e=>e.extensionName);
 if(!used.includes('EXT_meshopt_compression'))throw Error('Expected production meshopt encoding absent');
 const meshopt=r.listExtensionsUsed().find(e=>e.extensionName==='EXT_meshopt_compression');meshopt.dispose();
 const decoded=path.join(out,'qa-decoded-reimport.glb');await io.write(decoded,d);
 const texts=[],bounds={min:[Infinity,Infinity,Infinity],max:[-Infinity,-Infinity,-Infinity]};let triangles=0,nonfinite=0;
 // Bounds are evaluated from decoded accessor elements, not compressed extrema.
 for(const n of r.listNodes()){
  const mesh=n.getMesh();if(!mesh)continue;const matrix=n.getWorldMatrix(),extra=n.getExtras(),b={min:[Infinity,Infinity,Infinity],max:[-Infinity,-Infinity,-Infinity]};
  let count=0;for(const p of mesh.listPrimitives()){
   const a=p.getAttribute('POSITION');count+=(p.getIndices()?.getCount()||a.getCount())/3;const v=[];
   for(let k=0;k<a.getCount();k++){
    a.getElement(k,v);const q=[matrix[0]*v[0]+matrix[4]*v[1]+matrix[8]*v[2]+matrix[12],matrix[1]*v[0]+matrix[5]*v[1]+matrix[9]*v[2]+matrix[13],matrix[2]*v[0]+matrix[6]*v[1]+matrix[10]*v[2]+matrix[14]];
    const z=[q[0],-q[2],q[1]];for(let i=0;i<3;i++){if(!Number.isFinite(z[i]))nonfinite++;b.min[i]=Math.min(b.min[i],z[i]);b.max[i]=Math.max(b.max[i],z[i]);bounds.min[i]=Math.min(bounds.min[i],z[i]);bounds.max[i]=Math.max(bounds.max[i],z[i]);}
   }
  }
  triangles+=count;if(extra.text_content)texts.push({name:n.getName(),body:extra.text_content,feature:extra.feature_id,bounds_blender:b,triangles:count});
 }
 if(texts.length!==4||nonfinite)throw Error('Decoded text count or coordinates failed');
 const record={...provenance(),compressed_production:source,production_sha256:sha(source),decoded_qa_file:decoded,decoded_sha256:sha(decoded),decoded_bytes:fs.statSync(decoded).size,
  method:'NodeIO loads and decodes EXT_meshopt_compression; only that encoding extension is disposed before writing an equivalent QA derivative. Blender imports the derivative because its production meshopt support is not assumed.',
  temporary_derivative_is_not_a_production_asset:true,extensions_before:used,extensions_after:r.listExtensionsUsed().map(e=>e.extensionName),triangles,nonfinite,bounds_blender:bounds,texts};
 save('decoded-reimport-reference.json',record);console.log(JSON.stringify({decoded,triangles,texts:texts.length,nonfinite}));
}
async function browserQA(){
 if(mode==='performance'&&!frozen)throw Error('Performance requires explicit --frozen after parent confirms isolation.');
 const proof=provenance();if(!proof.source_matches_export)throw Error('Source changed after export');
 if(!proof.assets.every(a=>a.matches_registered_bytes_and_revision))throw Error('A production asset differs from its registered bytes or revision');
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1}),page=await context.newPage(),errors=[],failed=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failed.push({url:r.url(),status:r.status()});});
 const start=Date.now();await page.goto('http://localhost:5188/?closeoutMetrics=1');await page.waitForFunction(()=>window.__campusCloseout?.ready(),null,{timeout:180000});
 const loadMs=Date.now()-start;await page.getByRole('combobox',{name:'建筑标签显示'}).selectOption('off');
 const records=[];const quantile=(a,q)=>a[Math.min(a.length-1,Math.floor(a.length*q))];
 async function measure(id,pose){
  if(typeof pose==='number')await page.evaluate(i=>window.__campusCloseout.view(i),pose);
  else await page.evaluate(v=>window.__campusCloseout.pose(v.p,v.t,v.fov),pose);
  await page.waitForTimeout(4000);
  if(mode==='performance'){await page.evaluate(()=>window.__campusCloseout.reset());await page.waitForTimeout(10000);}
  const m=await page.evaluate(()=>window.__campusCloseout.metrics());const row={id,...m};
  if(mode==='performance'){const a=m.frames.filter(v=>v>0).sort((a,b)=>a-b);row.frameCount=a.length;row.medianFrameMs=quantile(a,.5);row.p95FrameMs=quantile(a,.95);row.medianFps=1000/row.medianFrameMs;}
  delete row.frames;const image=`${frozen?'web-final':'web-preparation'}-${id}.png`;await page.screenshot({path:path.join(out,image)});row.image=image;row.image_sha256=sha(path.join(out,image));records.push(row);
 }
 if(mode==='performance')for(const i of [2,3,1])await measure(`view-${i}`,i);
 for(const view of cameraViews())await measure(view.id,view);
 const before=await page.evaluate(()=>window.__campusCloseout.metrics());await page.getByRole('button',{name:/^树木\s*开$/}).click();await page.waitForTimeout(1000);
 const hidden=await page.evaluate(()=>window.__campusCloseout.metrics());await page.screenshot({path:path.join(out,`${frozen?'web-final':'web-preparation'}-no-vegetation.png`)});
 await page.getByRole('button',{name:/^树木\s*关$/}).click();await page.waitForTimeout(1000);
 const restored=await page.evaluate(()=>window.__campusCloseout.metrics());
 await page.locator('nav').getByRole('button',{name:/光华楼草坪/}).click();await page.waitForTimeout(4000);
 const selectedViewCamera=await page.evaluate(()=>window.__campusCloseout.camera());
 const navigationPass=Math.max(...selectedViewCamera.position.map((v,i)=>Math.abs(v-[236,115,-47][i])))<.05;
 const vegetationTogglePass=before.trees&&hidden.trees===false&&restored.trees&&hidden.triangles<before.triangles&&restored.triangles===before.triangles;
 await page.screenshot({path:path.join(out,`${frozen?'web-final':'web-preparation'}-navigation.png`)});
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(1500);
 const narrowOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);await page.screenshot({path:path.join(out,`${frozen?'web-final':'web-preparation'}-narrow.png`)});
 const result={...proof,date_utc:new Date().toISOString(),browser:await browser.version(),headless:true,resolution:[1920,1080],pixelRatio:1,
  measurementSeconds:mode==='performance'?10:0,load:{fresh_browser_context_local_ms:loadMs,network:'loopback; OS cache unspecified; no public bandwidth claim'},records,
  vegetationToggle:{before,hidden,restored,pass:vegetationTogglePass},navigation:{pass:navigationPass,selectedViewCamera,uiButton:'光华楼草坪'},errors,failed,narrowOverflow,visualReview:'Screenshots require explicit visual inspection; readable glyphs are not asserted by this script.'};
 if(mode==='performance'){
  const baseline=json(path.join(out,'baseline-performance.json'));
  result.environmentMatchesBaseline={browser:result.browser===baseline.browser,resolution:JSON.stringify(result.resolution)===JSON.stringify(baseline.resolution),pixelRatio:result.pixelRatio===baseline.pixelRatio,gpu:records.every(r=>r.gpu===baseline.views[0].gpu)};
  const comparisons=records.filter(r=>r.id.startsWith('view-')).map(r=>{const id=+r.id.split('-')[1],old=baseline.views[[2,3,1].indexOf(id)];return {view:id,medianFrameRegression:r.medianFrameMs/old.medianFrameMs-1,medianPass:r.medianFps>=30,p95Pass:r.p95FrameMs<=50,trianglePass:r.triangles<=(id===1?6000000:3000000),regressionPass:r.medianFrameMs/old.medianFrameMs<=1.2,drawTargetPass:r.drawCalls<=500};});
  result.comparisons=comparisons;result.requiredPass=Object.values(result.environmentMatchesBaseline).every(Boolean)&&comparisons.every(c=>c.medianPass&&c.p95Pass&&c.trianglePass&&c.regressionPass)&&records.every(r=>r.medianFps>=30&&r.p95FrameMs<=50&&r.triangles<=6000000)&&!errors.length&&!failed.length&&!narrowOverflow&&vegetationTogglePass&&navigationPass;
 }
 merge(frozen?mode:`preparation_${mode}`,result);await browser.close();console.log(JSON.stringify({mode,frozen,records:records.map(r=>({id:r.id,triangles:r.triangles,drawCalls:r.drawCalls,medianFps:r.medianFps,p95FrameMs:r.p95FrameMs})),errors,failed,narrowOverflow,requiredPass:result.requiredPass},null,2));
 if(errors.length||failed.length||narrowOverflow||!vegetationTogglePass||!navigationPass||result.requiredPass===false)process.exitCode=1;
}
(mode==='decode'?decode():mode==='build'?build():browserQA()).catch(e=>{console.error(e);process.exit(1)});
