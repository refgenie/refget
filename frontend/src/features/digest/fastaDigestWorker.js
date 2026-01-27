// Web Worker for streaming FASTA digest computation.
// Runs in background thread to avoid freezing UI.
// Uses streaming API for files of any size.

let wasmModule = null;

async function initWasm() {
  if (wasmModule) return wasmModule;

  const gtars = await import('@databio/gtars');
  await gtars.default();
  wasmModule = gtars;
  return wasmModule;
}

self.onmessage = async (e) => {
  const { file } = e.data;

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
        const { done, value } = await reader.read();
        if (done) break;

        // Pass chunk directly to Rust - no parsing in JS
        gtars.fastaHasherUpdate(hasher, value);

        bytesProcessed += value.length;
        self.postMessage({
          type: 'progress',
          bytesProcessed,
          totalSize,
          percent: Math.round(100 * bytesProcessed / totalSize)
        });
      }

      // Finalize and get result
      self.postMessage({ type: 'status', message: 'Computing final digests...' });
      const result = gtars.fastaHasherFinish(hasher);
      self.postMessage({ type: 'result', result });

    } catch (err) {
      gtars.fastaHasherFree(hasher);  // Cleanup on error
      throw err;
    }

  } catch (error) {
    self.postMessage({ type: 'error', message: error.message || 'Processing failed' });
  }
};
