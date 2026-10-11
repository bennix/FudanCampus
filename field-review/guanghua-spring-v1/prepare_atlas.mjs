import {createRequire} from 'node:module';
const sharp=createRequire(new URL('../../web/package.json',import.meta.url))('sharp');
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
const dir=fileURLToPath(new URL('./',import.meta.url));
let flowers='';
for(const [cx,cy,r,turn] of [[253,253,98,7],[139,137,80,22],[373,145,87,42],[120,360,85,15],[375,371,82,54],[255,82,62,27],[271,430,59,0]]){
 let petals='';
 for(let i=0;i<5;i++)petals+=`<ellipse cx="0" cy="${-r*.47}" rx="${r*.39}" ry="${r*.57}" transform="rotate(${i*72})" fill="url(#petal)" stroke="#e9cdd4" stroke-width="1.5"/><path d="M0 0 Q-5 ${-r*.35} 0 ${-r*.69}" transform="rotate(${i*72})" fill="none" stroke="#eccbd5" stroke-width="1.2"/>`;
 for(let i=0;i<11;i++){const a=i*Math.PI*2/11,x=Math.sin(a)*r*.20,y=Math.cos(a)*r*.20;petals+=`<path d="M0 0L${x} ${y}" stroke="#dbb085" stroke-width="1.2"/><circle cx="${x}" cy="${y}" r="2.5" fill="#d4b764"/>`;}
 flowers+=`<g transform="translate(${cx} ${cy}) rotate(${turn})">${petals}<circle r="${r*.07}" fill="#d8a4b2"/></g>`;
}
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512"><defs><radialGradient id="petal"><stop stop-color="#eac5d0"/><stop offset=".45" stop-color="#f6e5ec"/><stop offset="1" stop-color="#fffafc"/></radialGradient></defs>${flowers}</svg>`;
await sharp(Buffer.from(svg)).png().toFile(dir+'spring-blossom-atlas.png');
console.log('Prepared seven pale pink-white five-petal blossoms with transparent crown gaps.');
