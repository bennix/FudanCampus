import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const base = '/FudanCampus/';

export default defineConfig({
  base,
  plugins: [
    {
      name: 'campus-pages-asset-paths',
      enforce: 'pre',
      transform(code, id) {
        if (!id.split('?')[0].endsWith('/app/page.tsx')) return;
        // Local vinext keeps root URLs; Pages serves the same app in a subdirectory.
        return { code: code.replace(/(['"])\/(?=[a-z][a-z0-9-]*\.(?:jpg|png|glb|json))/g, `$1${base}`), map: null };
      },
    },
    react(),
  ],
  build: { outDir: 'dist-pages' },
});
