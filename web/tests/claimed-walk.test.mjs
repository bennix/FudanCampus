import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {blockedInterior} from '../lib/campus-walk.ts';
const interiors=JSON.parse(fs.readFileSync(new URL('../public/walk-interiors.json',import.meta.url)));
const point=([u,v])=>[(u-176)*.48-167.2,(v-107)*.48-116];
for(const [name,pixel,expected] of [
 ['46 courtyard remains open',[170,85],false],
 ['46 south teaching wing is sealed',[170,116],true],
 ['51 western garden remains open',[160,205],false],
 ['51 northern office wing is sealed',[165,175],true],
 ['Map archive building is sealed',[90,180],true],
 ['Former A05 placeholder passage is open',[150,148],false],
 ['Library courtyard remains open',[310,175],false],
 ['Library south wing is sealed',[310,208],true],
])test(name,()=>assert.equal(blockedInterior(...point(pixel),interiors),expected));
