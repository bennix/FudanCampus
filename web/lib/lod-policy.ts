export type Tier = 0 | 1 | 2;
export type Candidate = {id:string;distance:number;current:Tier;priority?:number;nearDistance:number;mediumDistance:number;triangles:number[]};
export function desiredTier(item:Candidate, mobile:boolean):Tier {
 const scale=mobile ? .7 : 1;
 if(item.distance<item.nearDistance*scale*(item.current===2?1.25:1))return 2;
 if(item.distance<item.mediumDistance*scale*(item.current>=1?1.25:1))return 1;
 return 0;
}
/** All overview tiers remain available. Spend the remaining budget nearest-first. */
export function allocateTiers(items:Candidate[],mobile:boolean):Map<string,Tier> {
 const result=new Map<string,Tier>(items.map(i=>[i.id,0]));
 let remaining=(mobile?3_500_000:5_000_000)-items.reduce((n,i)=>n+i.triangles[0],0);
 let slots=mobile?3:6;
 let treeSlots=mobile?16:32;
 let shrubSlots=mobile?8:16;
 for(const item of [...items].sort((a,b)=>(a.priority??a.distance)-(b.priority??b.distance))) {
  const tree=item.id.startsWith('landscape-tree-')||item.id.startsWith('campus-tree-'),shrub=item.id.startsWith('landscape-shrub-');
  if(shrub?!shrubSlots:tree?!treeSlots:!slots)continue;
  let tier=desiredTier(item,mobile);
  while(tier>0 && (item.triangles[tier]-item.triangles[0]>remaining || (mobile && item.triangles[tier]>(item.id==='guanghua-cherry'?750_000:shrub?500_000:180_000))))tier=(tier-1) as Tier;
  if(tier>0){result.set(item.id,tier);remaining-=item.triangles[tier]-item.triangles[0];if(shrub)shrubSlots--;else if(tree)treeSlots--;else slots--;}
 }
 return result;
}
