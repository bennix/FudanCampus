import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
const source=process.argv[2];
if(!source)throw Error('Usage: node scripts/package_web_model.mjs path/to/model.glb');
const bytes=fs.readFileSync(source),hash=b=>createHash('sha256').update(b).digest('hex');
const sha256=hash(bytes),parts=[],partBytes=64*1024*1024;
for(let offset=0;offset<bytes.length;offset+=partBytes){const part=bytes.subarray(offset,offset+partBytes),name=`${path.basename(source)}.${sha256.slice(0,12)}.part${parts.length}.bin`;fs.writeFileSync(path.join(path.dirname(source),name),part);parts.push({url:name,bytes:part.length,sha256:hash(part)});}
const descriptor={version:1,bytes:bytes.length,sha256,parts};
fs.writeFileSync(source+'.parts.json',JSON.stringify(descriptor,null,2)+'\n');
const restored=Buffer.concat(parts.map(p=>fs.readFileSync(path.join(path.dirname(source),p.url))));
if(!restored.equals(bytes))throw Error('Packaged model differs');
console.log(JSON.stringify({descriptor:source+'.parts.json',parts:parts.map(p=>p.bytes),exactMatch:true}));
