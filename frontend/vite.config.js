import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import alias from '@rollup/plugin-alias';
import path from 'path';

// https://vitejs.dev/config/
// Use LOCAL_GTARS env var to point to local gtars-wasm build:
//   LOCAL_GTARS=../../gtars/gtars-wasm/pkg npm run dev
const localGtarsPath = process.env.LOCAL_GTARS
  ? path.resolve(process.env.LOCAL_GTARS)
  : null;

export default defineConfig({
  plugins: [react()],
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
