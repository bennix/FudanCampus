import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'node:fs';
import path from 'node:path';

const base = '/FudanCampus/';

export default defineConfig({
  base,
  publicDir: false,
  plugins: [
    {
      name: 'campus-delivery-assets',
      closeBundle() {
        const pub = path.resolve('public');
        const out = path.resolve('dist-pages');
        const manifest = JSON.parse(fs.readFileSync(path.join(pub, 'campus-manifest.json'), 'utf8'));
        const copy = (relative: string) => {
          const source = path.resolve(pub, relative);
          if (!source.startsWith(pub + path.sep)) throw Error('Asset outside public directory');
          const destination = path.join(out, relative);
          fs.mkdirSync(path.dirname(destination), { recursive: true });
          fs.copyFileSync(source, destination);
        };
        for (const entry of fs.readdirSync(pub, { withFileTypes: true })) {
          if (entry.isFile() && !entry.name.endsWith('.glb')) copy(entry.name);
        }
        const assets = [...manifest.shared, ...manifest.buildings, ...manifest.buildings.map((asset: { overview: unknown }) => asset.overview)];
        for (const asset of assets) {
          copy(asset.url);
          if (asset.url.endsWith('.parts.json')) {
            const descriptor = JSON.parse(fs.readFileSync(path.join(pub, asset.url), 'utf8'));
            for (const part of descriptor.parts) copy(path.join(path.dirname(asset.url), part.url));
          }
        }
      },
    },
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
