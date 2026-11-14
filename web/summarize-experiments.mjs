import fs from 'node:fs/promises';
import {summarizeFrames} from './lib/frame-metrics.ts';
const root=new URL('../field-review/webxr-2026-11-14/',import.meta.url);
const results=JSON.parse(await fs.readFile(new URL('results.json',root),'utf8'));
const groups=[];
for(const point of ['teaching4','chemistry'])for(const variant of ['no-culling','cached-shadow','no-shadow']){
 const trials=results.filter(r=>r.point===point&&r.variant===variant);
 if(trials.length!==3)throw Error(`Expected three trials: ${point}/${variant}`);
 for(const trial of trials){
  if(trial.lod.ready!==trial.lod.assets||trial.lod.pending!==0)throw Error('Incomplete initial LOD');
  if(JSON.stringify(trial.lod)!==JSON.stringify(trial.lodAtEnd))throw Error('LOD changed while sampling');
  const check=summarizeFrames(trial.frames);if(Math.abs(check.fps-trial.summary.fps)>1e-8)throw Error('Summary not reproducible');
 }
 const summary=summarizeFrames(trials.flatMap(r=>r.frames));
 groups.push({point,variant,trials:3,...summary,roundFps:trials.map(t=>t.summary.fps)});
}
const environment={...results[0]};delete environment.frames;delete environment.summary;delete environment.lod;delete environment.lodAtEnd;
const report={environment,groups,limitations:['无界面软件渲染预实验，非物理头显性能','2秒预热/5秒采样，低帧率导致样本少，P95/P99仅作描述','固定视点与热缓存，不评价冷启动、漫游或整校园最坏视点','不同建筑视点分别对比，不将建筑之间的差异解释为优化收益']};
await fs.writeFile(new URL('summary.json',root),JSON.stringify(report,null,2));
const lines=['建筑,设置,轮数,有效帧间隔样本,提交帧率,平均帧间隔ms,P95ms,平均JS提交ms,平均绘制调用,平均提交三角形',...groups.map(g=>[g.point,g.variant,g.trials,g.samples,g.fps.toFixed(2),g.meanIntervalMs.toFixed(2),g.p95IntervalMs.toFixed(2),g.meanSubmitMs.toFixed(2),g.meanCalls.toFixed(0),g.meanTriangles.toFixed(0)].join(','))];
await fs.writeFile(new URL('summary.csv',root),'\uFEFF'+lines.join('\n'));
console.log(lines.join('\n'));
