'use client';
import {lazy,Suspense,useEffect,useState} from 'react';

const CampusScene=lazy(()=>import('./campus-scene'));
export default function Home(){
 const [exploring,setExploring]=useState<boolean|null>(null);
 useEffect(()=>{
   const params=new URLSearchParams(location.search);
   setExploring(params.has('walk')||params.has('view'));
 },[]);
 if(exploring===null)return null;
 if(exploring)return <Suspense fallback={<p role="status">正在载入校园场景…</p>}><CampusScene/></Suspense>;
 return <main className="campus-entry">
   <img className="entry-photo" src="./campus-gate.webp" srcSet="./campus-gate-small.webp 720w, ./campus-gate.webp 1800w" sizes="100vw" alt="复旦大学邯郸校区校门实景" fetchPriority="high"/>
   <div className="entry-content"><div className="entry-campus">复旦大学 · 邯郸校区</div>
   <h1>校园漫游</h1><p>从化学楼门前出发，沿校园道路探索建筑，随时对照实景照片。</p>
   <div className="entry-links"><a href="?walk">开始步行漫游 <span aria-hidden="true">→</span></a><a href="?view=overview">校园鸟瞰</a></div></div>
 </main>;
}
