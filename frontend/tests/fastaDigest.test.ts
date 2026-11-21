/// <reference lib="dom" />
/**
 * The shared FASTA digest module (src/lib/fastaDigest/) run against the real
 * @databio/gtars wasm: plain, gzip and bgzip input must all give the digest
 * the refget CLI gives, and the worker client must relay progress, results,
 * errors and cancel.
 *
 * Run with: npm test
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { randomBytes } from 'node:crypto';
import { crc32, deflateRawSync, gzipSync } from 'node:zlib';

import {
  bgzfBlockSize,
  bgzfMembers,
  BGZF_CUT_OFF,
  digestFastaChunks,
  inflateMembers,
  looksLikeFasta,
  sniffBytesNeeded,
  sniffCompression,
  type FastaHasherWasm,
} from '../src/lib/fastaDigest/fastaDigest.ts';
import {
  digestFile,
  isAbortError,
  type DigestWorkerReply,
  type DigestWorkerRequest,
  type WorkerLike,
} from '../src/lib/fastaDigest/fastaDigestClient.ts';

/** Three sequences, 60 bases per line. */
function makeFasta(): Uint8Array<ArrayBuffer> {
  const lines: string[] = [];
  for (const [name, len, unit] of [
    ['chr1', 3000, 'ACGT'],
    ['chr2', 1234, 'GGCAT'],
    ['chrM', 777, 'TTAN'],
  ] as const) {
    lines.push(`>${name}`);
    const seq = unit.repeat(Math.ceil(len / unit.length)).slice(0, len);
    for (let i = 0; i < len; i += 60) lines.push(seq.slice(i, i + 60));
  }
  return new TextEncoder().encode(lines.join('\n') + '\n');
}

const SOURCE = makeFasta();
// `refget fasta digest` (refget 0.13.0, gtars 0.11.2) on the same file.
const DIGEST = 'M8__3ZsweAFX1DOZ8_CkygrVvi7SDXMI';

/** One BGZF member holding `data`. */
function bgzfBlock(data: Uint8Array): Uint8Array {
  const deflated = deflateRawSync(data);
  const out = new Uint8Array(18 + deflated.length + 8);
  const view = new DataView(out.buffer);
  out.set([0x1f, 0x8b, 8, 4, 0, 0, 0, 0, 0, 0xff, 6, 0, 0x42, 0x43, 2, 0]);
  view.setUint16(16, out.length - 1, true);
  out.set(deflated, 18);
  view.setUint32(18 + deflated.length, crc32(data), true);
  view.setUint32(22 + deflated.length, data.length, true);
  return out;
}

/** BGZF with small blocks, so a short file spans several members, plus the EOF block. */
function bgzipped(bytes: Uint8Array, blockInput = 300): Uint8Array {
  const parts: Uint8Array[] = [];
  for (let i = 0; i < bytes.length; i += blockInput) {
    parts.push(bgzfBlock(bytes.slice(i, i + blockInput)));
  }
  parts.push(bgzfBlock(new Uint8Array(0)));
  return new Uint8Array(Buffer.concat(parts));
}

/** `bytes` as a stream of `size`-byte chunks. */
async function* chunked(bytes: Uint8Array, size: number): AsyncGenerator<Uint8Array> {
  for (let i = 0; i < bytes.length; i += size) yield bytes.slice(i, i + size);
}

async function loadWasm(): Promise<FastaHasherWasm> {
  const dir = dirname(createRequire(import.meta.url).resolve('@databio/gtars'));
  const mod = await import('@databio/gtars');
  await mod.default({ module_or_path: readFileSync(join(dir, 'gtars_js_bg.wasm')) });
  return mod;
}
const wasmReady = loadWasm();

test('sniffCompression tells plain text, gzip and BGZF apart', () => {
  assert.equal(sniffCompression(SOURCE), 'none');
  assert.equal(sniffCompression(new Uint8Array(gzipSync(SOURCE))), 'gzip');
  assert.equal(sniffCompression(bgzipped(SOURCE)), 'bgzf');
});

test('bgzfMembers splits a BGZF stream into whole members, whatever the chunking', async () => {
  const file = bgzipped(SOURCE);
  const sizes: number[] = [];
  for await (const member of bgzfMembers(chunked(file, 7))) {
    assert.equal(bgzfBlockSize(member, 0), member.length);
    sizes.push(member.length);
  }
  assert.ok(sizes.length > 3);
  assert.equal(sizes.reduce((a, b) => a + b, 0), file.length);
});

test('bgzfMembers refuses a truncated file', async () => {
  const file = bgzipped(SOURCE);
  await assert.rejects(async () => {
    for await (const member of bgzfMembers(chunked(file.slice(0, file.length - 40), 64))) {
      void member;
    }
  }, /ends partway/);
});

test('bgzfMembers refuses a file cut off at a block boundary (no EOF block)', async () => {
  const file = bgzipped(SOURCE);
  const eof = bgzfBlock(new Uint8Array(0)).length;
  await assert.rejects(async () => {
    for await (const member of bgzfMembers(chunked(file.slice(0, file.length - eof), 64))) {
      void member;
    }
  }, (err: Error) => err.message === BGZF_CUT_OFF);
});

/** A BGZF member whose extra field has a long subfield before `BC`. */
function bgzfBlockExtra(data: Uint8Array, padLen = 80): Uint8Array {
  const plain = bgzfBlock(data);
  const xlen = 4 + padLen + 6;
  const out = new Uint8Array(plain.length + 4 + padLen);
  const view = new DataView(out.buffer);
  out.set(plain.subarray(0, 10));
  view.setUint16(10, xlen, true);
  out.set([0x58, 0x58], 12); // 'XX' subfield
  view.setUint16(14, padLen, true);
  out.set([0x42, 0x43, 2, 0], 16 + padLen);
  view.setUint16(20 + padLen, out.length - 1, true);
  out.set(plain.subarray(18), 22 + padLen);
  return out;
}

test('a BGZF header with a long extra field is still sniffed as BGZF', async () => {
  const parts: Uint8Array[] = [];
  for (let i = 0; i < SOURCE.length; i += 300) parts.push(bgzfBlockExtra(SOURCE.slice(i, i + 300)));
  parts.push(bgzfBlockExtra(new Uint8Array(0)));
  const file = new Uint8Array(Buffer.concat(parts));
  assert.equal(bgzfBlockSize(file, 0), parts[0].length);
  // The first 64 bytes do not hold the whole extra field...
  assert.equal(sniffCompression(file.subarray(0, 64)), 'gzip');
  assert.equal(sniffBytesNeeded(file.subarray(0, 64)), 12 + 4 + 80 + 6);
  assert.equal(sniffCompression(file), 'bgzf');
  // ...so the digest must read further before deciding, whatever the chunking.
  const wasm = await wasmReady;
  for (const size of [1, 13, 64, 65536]) {
    const result = await digestFastaChunks(chunked(file, size), wasm);
    assert.equal(result.digest, DIGEST, `chunk size ${size}`);
  }
});

test('inflateMembers leaves no unhandled rejection when it stops early', async () => {
  const unhandled: unknown[] = [];
  const onUnhandled = (reason: unknown) => unhandled.push(reason);
  process.on('unhandledRejection', onUnhandled);
  try {
    // Members that fail to decompress, from a stream that breaks partway.
    const gunzip = () =>
      new Promise<Uint8Array>((_, reject) =>
        setTimeout(() => reject(new Error('bad member')), 5),
      );
    async function* members(): AsyncGenerator<Uint8Array> {
      yield new Uint8Array(1);
      yield new Uint8Array(1);
      throw new Error('read failed');
    }
    await assert.rejects(async () => {
      for await (const out of inflateMembers(members(), gunzip, 4)) void out;
    }, /read failed/);
    await new Promise((r) => setTimeout(r, 50));
    assert.deepEqual(unhandled, []);
  } finally {
    process.off('unhandledRejection', onUnhandled);
  }
});

test('digestFastaChunks closes the file stream when it stops early', async () => {
  const wasm = await wasmReady;
  let closed = false;
  async function* source(bytes: Uint8Array): AsyncGenerator<Uint8Array> {
    try {
      yield* chunked(bytes, 50);
    } finally {
      closed = true;
    }
  }
  // bgzip around gzip: the first decompressed bytes are gzip again. Random
  // bytes do not compress, so the file is far longer than what is read.
  const twice = bgzipped(new Uint8Array(gzipSync(randomBytes(100_000))));
  await assert.rejects(digestFastaChunks(source(twice), wasm), /compressed twice/);
  assert.equal(closed, true);
});

test('plain, gzip and bgzip give the refget CLI digest, in any chunk size', async () => {
  const wasm = await wasmReady;
  const forms = {
    plain: SOURCE,
    gzip: new Uint8Array(gzipSync(SOURCE)),
    bgzip: bgzipped(SOURCE),
  };
  for (const [form, bytes] of Object.entries(forms)) {
    for (const size of [1, 13, 50, 65536]) {
      const result = await digestFastaChunks(chunked(bytes, size), wasm);
      assert.equal(result.digest, DIGEST, `${form}, chunk size ${size}`);
    }
  }
});

test('digestFastaChunks reports sequences in order and bytes read', async () => {
  const wasm = await wasmReady;
  const seen: number[] = [];
  const result = await digestFastaChunks(chunked(SOURCE, 500), wasm, {
    onProgress: (n) => seen.push(n),
  });
  assert.deepEqual(result.sequences.map((s) => s.name), ['chr1', 'chr2', 'chrM']);
  assert.equal(seen[seen.length - 1], SOURCE.length);
});

test('digestFastaChunks rejects empty, non-FASTA and double-gzipped input', async () => {
  const wasm = await wasmReady;
  await assert.rejects(digestFastaChunks(chunked(new Uint8Array(0), 10), wasm), /empty/);
  const text = new TextEncoder().encode('hello world\nnot a fasta\n');
  await assert.rejects(digestFastaChunks(chunked(text, 10), wasm));
  const twice = new Uint8Array(gzipSync(gzipSync(SOURCE)));
  await assert.rejects(digestFastaChunks(chunked(twice, 100), wasm), /compressed twice/);
});

test('looksLikeFasta accepts FASTA names, plain or gzipped', () => {
  for (const name of ['a.fa', 'b.fasta', 'c.fna', 'd.fa.gz', 'E.FASTA.GZ', 'f.fa.bgz']) {
    assert.equal(looksLikeFasta(name), true, name);
  }
  assert.equal(looksLikeFasta('notes.txt'), false);
  assert.equal(looksLikeFasta('reads.bam'), false);
});

/** A fake worker the test drives by hand. */
function fakeWorker() {
  const worker = {
    onmessage: null,
    onerror: null,
    sent: [] as DigestWorkerRequest[],
    terminated: false,
    postMessage(message: DigestWorkerRequest) {
      this.sent.push(message);
    },
    terminate() {
      this.terminated = true;
    },
    reply(data: DigestWorkerReply) {
      this.onmessage?.({ data } as MessageEvent<DigestWorkerReply>);
    },
  } as WorkerLike & {
    sent: DigestWorkerRequest[];
    terminated: boolean;
    reply(data: DigestWorkerReply): void;
  };
  return worker;
}

test('digestFile relays status, progress and the result', async () => {
  const worker = fakeWorker();
  const file = new File([SOURCE], 'mine.fa');
  const events: string[] = [];
  const job = digestFile(
    file,
    {
      onStatus: (m) => events.push(`status ${m}`),
      onProgress: (n, total) => events.push(`progress ${n}/${total}`),
    },
    () => worker,
  );
  assert.equal(worker.sent[0].file, file);
  worker.reply({ type: 'status', message: 'Processing file...' });
  worker.reply({ type: 'progress', bytesRead: 10, totalBytes: 20 });
  const stats = { chunks: 1, totalBytes: 20, elapsedMs: 5, avgChunkSize: 20 };
  const result = { digest: DIGEST, n_sequences: 0, names_digest: '', sequences_digest: '', lengths_digest: '', sequences: [] };
  worker.reply({ type: 'result', result, stats });
  assert.deepEqual(await job.done, { result, stats });
  assert.deepEqual(events, ['status Processing file...', 'progress 10/20']);
  assert.equal(worker.terminated, true);
});

test('digestFile rejects on a worker error, and cancel aborts', async () => {
  const failing = fakeWorker();
  const job = digestFile(new File([SOURCE], 'x.fa'), {}, () => failing);
  failing.reply({ type: 'error', message: 'No sequences found.' });
  await assert.rejects(job.done, /No sequences found/);

  const slow = fakeWorker();
  const cancelled = digestFile(new File([SOURCE], 'y.fa'), {}, () => slow);
  cancelled.cancel();
  await assert.rejects(cancelled.done, (err) => isAbortError(err));
  assert.equal(slow.terminated, true);
});
