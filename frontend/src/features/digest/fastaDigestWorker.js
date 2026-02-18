// Web Worker for streaming FASTA digest computation.
// Runs in background thread to avoid freezing UI.
// Uses streaming API for files of any size.

const PROGRESS_INTERVAL_MS = 200;  // Max 5 updates/sec
let lastProgressTime = 0;
let wasmModule = null;
let cancelled = false;

async function initWasm() {
  if (wasmModule) return wasmModule;

  const gtars = await import('@databio/gtars');
  await gtars.default();
  wasmModule = gtars;
  return wasmModule;
}

self.onmessage = async (e) => {
  const { type } = e.data;

  if (type === 'cancel') {
    cancelled = true;
    return;
  }

  const { file } = e.data;
  cancelled = false;

  const stats = { chunks: 0, totalBytes: 0, startTime: Date.now() };

  try {
    self.postMessage({ type: 'status', message: 'Loading WASM module...' });
    const gtars = await initWasm();

    // Create streaming hasher
    const hasher = gtars.fastaHasherNew();

    try {
      self.postMessage({ type: 'status', message: 'Processing file...' });

      // Stream file chunks to WASM
      const stream = file.stream();
      const reader = stream.getReader();

      let bytesProcessed = 0;
      const totalSize = file.size;

      while (true) {
        if (cancelled) {
          reader.cancel();
          gtars.fastaHasherFree(hasher);
          self.postMessage({ type: 'cancelled' });
          return;
        }

        const { done, value } = await reader.read();
        if (done) break;

        try {
          gtars.fastaHasherUpdate(hasher, value);
        } catch (err) {
          gtars.fastaHasherFree(hasher);
          const msg = err.message || '';
          if (msg.toLowerCase().includes('fasta') || msg.toLowerCase().includes('parse')) {
            self.postMessage({ type: 'error', message: `Invalid FASTA format: ${msg}`, category: 'parse' });
          } else {
            self.postMessage({ type: 'error', message: `WASM processing error: ${msg}`, category: 'wasm' });
          }
          return;
        }

        stats.chunks++;
        bytesProcessed += value.length;
        stats.totalBytes = bytesProcessed;

        const now = Date.now();
        if (now - lastProgressTime >= PROGRESS_INTERVAL_MS) {
          lastProgressTime = now;
          self.postMessage({
            type: 'progress',
            bytesProcessed,
            totalSize,
            percent: Math.round(100 * bytesProcessed / totalSize)
          });
        }
      }

      // Send final progress to ensure 100%
      self.postMessage({ type: 'progress', bytesProcessed: totalSize, totalSize, percent: 100 });

      // Finalize and get result
      self.postMessage({ type: 'status', message: 'Computing final digests...' });
      const result = gtars.fastaHasherFinish(hasher);

      stats.elapsedMs = Date.now() - stats.startTime;
      stats.avgChunkSize = stats.chunks > 0 ? Math.round(stats.totalBytes / stats.chunks) : 0;
      self.postMessage({ type: 'result', result, stats });

    } catch (err) {
      gtars.fastaHasherFree(hasher);  // Cleanup on error
      throw err;
    }

  } catch (error) {
    const msg = error.message || 'Processing failed';
    let category = 'unknown';
    if (msg.toLowerCase().includes('gzip') || msg.toLowerCase().includes('decompress') || msg.toLowerCase().includes('corrupt')) {
      category = 'gzip';
      self.postMessage({ type: 'error', message: `File appears corrupted or is not valid gzip: ${msg}`, category });
    } else if (msg.toLowerCase().includes('stream') || msg.toLowerCase().includes('read')) {
      category = 'stream';
      self.postMessage({ type: 'error', message: `Error reading file: ${msg}`, category });
    } else {
      self.postMessage({ type: 'error', message: msg, category });
    }
  }
};
