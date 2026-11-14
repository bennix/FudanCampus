import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const python=process.platform==='win32'?'python':'python3';
const result=spawnSync(python,[fileURLToPath(new URL('../scripts/validate_lods.py',import.meta.url))],{
  stdio:'inherit',env:{...process.env,PYTHONUTF8:'1'},
});
if(result.error)console.error(result.error.message);
process.exit(result.status??1);
