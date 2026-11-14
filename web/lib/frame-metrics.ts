export type FrameSample={intervalMs:number;submitMs:number;calls:number;triangles:number};
export function summarizeFrames(frames:FrameSample[]){
 if(!frames.length||frames.some(f=>!Number.isFinite(f.intervalMs)||f.intervalMs<=0||!Number.isFinite(f.submitMs)))throw Error('没有有效帧样本');
 const values=frames.map(f=>f.intervalMs).sort((a,b)=>a-b);
 const mean=(key:keyof FrameSample)=>frames.reduce((sum,f)=>sum+f[key],0)/frames.length;
 const quantile=(p:number)=>values[Math.min(values.length-1,Math.ceil(p*values.length)-1)];
 return {samples:frames.length,fps:1000/mean('intervalMs'),meanIntervalMs:mean('intervalMs'),medianIntervalMs:quantile(.5),p95IntervalMs:quantile(.95),p99IntervalMs:quantile(.99),meanSubmitMs:mean('submitMs'),meanCalls:mean('calls'),meanTriangles:mean('triangles')};
}
