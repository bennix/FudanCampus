import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {resolve} from 'node:path';
export default defineConfig({base:'/',plugins:[react()],server:{host:'127.0.0.1',port:5175,strictPort:true},preview:{host:'127.0.0.1',port:5175,strictPort:true},build:{outDir:'dist-hanbing-final',rollupOptions:{input:{campus:resolve(import.meta.dirname,'index.html'),hanbing:resolve(import.meta.dirname,'hanbing-final.html')}}}});
