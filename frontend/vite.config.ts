import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import alias from '@rollup/plugin-alias';
import path from 'path';
import fs from 'fs';

// https://vitejs.dev/config/
// Use LOCAL_GTARS env var to point to local gtars-wasm build:
//   LOCAL_GTARS=../../gtars/gtars-wasm/pkg npm run dev
const localGtarsPath = process.env.LOCAL_GTARS
  ? path.resolve(process.env.LOCAL_GTARS)
  : null;

// When developing against a LOCAL gtars build (via LOCAL_GTARS or
// `npm link @databio/gtars`), the package resolves to a real path OUTSIDE this
// project root, so Vite's fs security blocks serving its .wasm. Collect those
// real paths to add to server.fs.allow below. The DEFAULT (published
// @databio/gtars installed normally into node_modules) needs none of this — it
// lives inside the project root and Vite serves it out of the box.
const localGtarsAllow = (() => {
  const allow = [];
  if (localGtarsPath) allow.push(localGtarsPath);
  try {
    // npm-link case ONLY: node_modules/@databio/gtars is a symlink pointing at
    // a build outside the project. A normal (published) install is a real
    // directory inside node_modules, so leave it alone.
    const pkgPath = path.resolve('node_modules/@databio/gtars');
    if (fs.lstatSync(pkgPath).isSymbolicLink()) {
      allow.push(fs.realpathSync(pkgPath));
    }
  } catch {
    // not installed/linked; ignore
  }
  return allow;
})();

export default defineConfig({
  plugins: [react()],
  server: localGtarsAllow.length ? {
    fs: { allow: ['.', ...localGtarsAllow] }
  } : {},
  resolve: {
    alias: localGtarsPath ? {
      '@databio/gtars': localGtarsPath
    } : {}
  },
  optimizeDeps: {
    exclude: ['@databio/gtars']  // Exclude WASM from optimization
  },
  build: {
    target: 'esnext'  // Required for WASM
  },
  worker: {
    format: 'es',  // ES modules for workers
    plugins: () => localGtarsPath ? [
      alias({
        entries: [{ find: '@databio/gtars', replacement: localGtarsPath }]
      })
    ] : []
  }
});
