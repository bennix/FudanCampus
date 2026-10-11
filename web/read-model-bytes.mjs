import fs from 'node:fs';
import {createHash} from 'node:crypto';
export function readModelBytes(url){
 if(!url.pathname.endsWith('.parts.json'))return fs.readFileSync(url);
 const descriptor=JSON.parse(fs.readFileSync(url));
 const parts=descriptor.parts.map(part=>{const bytes=fs.readFileSync(new URL(part.url,url));if(bytes.length!==part.bytes||createHash('sha256').update(bytes).digest('hex')!==part.sha256)throw Error(`Model part changed: ${part.url}`);return bytes;});
 const bytes=Buffer.concat(parts);
 if(bytes.length!==descriptor.bytes||createHash('sha256').update(bytes).digest('hex')!==descriptor.sha256)throw Error('Reassembled model differs');
 return bytes;
}
