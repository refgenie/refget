// Web Worker for streaming FASTA digest computation.
// Runs in background thread to avoid freezing UI.
// Uses streaming API for files of any size.

import type { WorkerScope } from '../../types';
import { errorMessage } from '../../utils/errors';

// The DOM and WebWorker type libraries cannot both be loaded into one program,
// so this file names the slice of the worker global it actually uses.
const ctx = self as unknown as WorkerScope;

type Gtars = typeof import('@databio/gtars');

interface RunStats {
  chunks: number;
  totalBytes: number;
  startTime: number;
  elapsedMs?: number;
  avgChunkSize?: number;
}

const PROGRESS_INTERVAL_MS = 200;  // Max 5 updates/sec
let lastProgressTime = 0;
let wasmModule: Gtars | null = null;
let cancelled = false;

async function initWasm(): Promise<Gtars> {
  if (wasmModule) return wasmModule;

  const gtars = await import('@databio/gtars');
  await gtars.default();
  wasmModule = gtars;
  return wasmModule;
}

ctx.onmessage = async (e: MessageEvent) => {
  const { type } = e.data;

  if (type === 'cancel') {
    cancelled = true;
    return;
  }

  const { file } = e.data as { file: File };
  cancelled = false;

  const stats: RunStats = { chunks: 0, totalBytes: 0, startTime: Date.now() };

  try {
    ctx.postMessage({ type: 'status', message: 'Loading WASM module...' });
    const gtars = await initWasm();

    // Create streaming hasher
    const hasher = gtars.fastaHasherNew();

    try {
      ctx.postMessage({ type: 'status', message: 'Processing file...' });

      // Stream file chunks to WASM
      const stream = file.stream();
      const reader = stream.getReader();

      let bytesProcessed = 0;
      const totalSize = file.size;

      while (true) {
        if (cancelled) {
          reader.cancel();
          gtars.fastaHasherFree(hasher);
          ctx.postMessage({ type: 'cancelled' });
          return;
        }

        const { done, value } = await reader.read();
        if (done) break;

        try {
          gtars.fastaHasherUpdate(hasher, value);
        } catch (err) {
          gtars.fastaHasherFree(hasher);
          const msg = err instanceof Error ? errorMessage(err) : String(err);
          if (msg.toLowerCase().includes('fasta') || msg.toLowerCase().includes('parse')) {
            ctx.postMessage({ type: 'error', message: `Invalid FASTA format: ${msg}`, category: 'parse' });
          } else {
            ctx.postMessage({ type: 'error', message: `WASM processing error: ${msg}`, category: 'wasm' });
          }
          return;
        }

        stats.chunks++;
        bytesProcessed += value.length;
        stats.totalBytes = bytesProcessed;

        const now = Date.now();
        if (now - lastProgressTime >= PROGRESS_INTERVAL_MS) {
          lastProgressTime = now;
          ctx.postMessage({
            type: 'progress',
            bytesProcessed,
            totalSize,
            percent: Math.round(100 * bytesProcessed / totalSize)
          });
        }
      }

      // Send final progress to ensure 100%
      ctx.postMessage({ type: 'progress', bytesProcessed: totalSize, totalSize, percent: 100 });

      // Finalize and get result
      ctx.postMessage({ type: 'status', message: 'Computing final digests...' });
      const result = gtars.fastaHasherFinish(hasher);

      stats.elapsedMs = Date.now() - stats.startTime;
      stats.avgChunkSize = stats.chunks > 0 ? Math.round(stats.totalBytes / stats.chunks) : 0;
      ctx.postMessage({ type: 'result', result, stats });

    } catch (err) {
      gtars.fastaHasherFree(hasher);  // Cleanup on error
      throw err;
    }

  } catch (error) {
    const msg = (error instanceof Error && errorMessage(error)) || 'Processing failed';
    let category = 'unknown';
    if (msg.toLowerCase().includes('gzip') || msg.toLowerCase().includes('decompress') || msg.toLowerCase().includes('corrupt')) {
      category = 'gzip';
      ctx.postMessage({ type: 'error', message: `File appears corrupted or is not valid gzip: ${msg}`, category });
    } else if (msg.toLowerCase().includes('stream') || msg.toLowerCase().includes('read')) {
      category = 'stream';
      ctx.postMessage({ type: 'error', message: `Error reading file: ${msg}`, category });
    } else {
      ctx.postMessage({ type: 'error', message: msg, category });
    }
  }
};
