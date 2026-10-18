import {test} from 'node:test';
import assert from 'node:assert/strict';
import {allocateTiers,desiredTier} from '../lib/lod-policy.ts';
const item=(id,distance=10,triangles=[1000,30000,400000])=>({id,distance,current:0,nearDistance:100,mediumDistance:340,triangles});
test('mobile never allocates the heavy source statue',()=>{assert.equal(allocateTiers([item('statue')],true).get('statue'),1);});
test('desktop can display original near detail',()=>assert.equal(allocateTiers([item('statue')],false).get('statue'),2));
test('hysteresis prevents boundary thrashing',()=>{
 assert.equal(desiredTier({...item('x',110),current:2},false),2);
 assert.equal(desiredTier(item('x',110),false),1);
 assert.equal(desiredTier({...item('x',430),current:1},false),0);
});
test('budget is nearest-first and bounded across a tour',()=>{
 const items=Array.from({length:20},(_,i)=>item(String(i),i+1,[1000,80000,400000]));
 const selected=allocateTiers(items,true);
 assert.equal(selected.get('0'),1);assert.equal(selected.get('1'),1);assert.equal(selected.get('2'),1);
 assert.ok(items.reduce((sum,i)=>sum+i.triangles[selected.get(i.id)],0)<=3500000);
 const departed=allocateTiers(items.map(i=>({...i,distance:1000,current:1})),true);
 assert.ok([...departed.values()].every(t=>t===0));
});
test('an oversized overview does not trigger more detail',()=>assert.equal(allocateTiers([item('large',0,[3600000,3700000,4000000])],true).get('large'),0));

test('large overlapping districts do not starve a nearby landmark',()=>{
 const districts=Array.from({length:3},(_,i)=>({...item('district'+i,0),priority:100}));
 const statue={...item('statue',15),priority:16};
 assert.equal(allocateTiers([...districts,statue],true).get('statue'),1);
});

test("close cherry retains original blossom and branch detail on mobile",()=>{const cherry=item("guanghua-cherry",15,[150000,360000,709192]);const campus=item("campus",1000,[1300000,1300000,1300000]);assert.equal(allocateTiers([campus,cherry],true).get("guanghua-cherry"),2);});

test("nearby trees have independent detail slots",()=>{const trees=Array.from({length:10},(_,i)=>item("landscape-tree-"+i,10,[5000,26000,61000]));const selected=allocateTiers(trees,true);assert.ok([...selected.values()].every(t=>t===2));});
