import { useState } from 'react';

export default function FieldPhotos() {
 const [building, setBuilding] = useState<'46'|'51'|null>(null);
 return <section className="field-photos" aria-label="建筑实拍参考">
  <button onClick={()=>setBuilding(building==='46'?null:'46')}>一教 · 实拍 7 张</button>{' '}
  <button onClick={()=>setBuilding(building==='51'?null:'51')}>综合楼 · 实拍 11 张</button>
  {building&&<div style={{maxHeight:'55vh',overflowY:'auto'}}>
   <p>郑德泓 · 计算机拔尖人才实验班<br/>从朝校门侧开始逆时针绕行，保留拍摄编号。</p>
   {Array.from({length:building==='46'?7:11},(_,i)=>i+1).map(n=><figure key={`${building}-${n}`} style={{margin:'12px 0'}}>
    <a href={`./field-photos/${building}/${n}.jpg`} target="_blank" rel="noreferrer"><img loading="lazy" src={`./field-photos/${building}/${n}.jpg`} alt={`${building==='46'?'第一教学楼':'综合办公楼'}实拍 ${n}`} style={{width:'100%',height:'auto'}}/></a>
    <figcaption>原图 {n}{building==='51'&&n===6?'：邻楼第一教学楼与两楼间道路':''}</figcaption>
   </figure>)}
  </div>}
 </section>;
}
