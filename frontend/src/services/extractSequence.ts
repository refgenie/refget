/**
 * Browser-side region extraction from a served refgetstore.
 *
 * `RemoteRefgetStore` (shipped by @databio/gtars) reads bases over HTTP `Range:`
 * requests and decodes the bit-packed bytes with wasm, caching fetched windows
 * in OPFS. A region read therefore costs a few hundred bytes, not a chromosome.
 *
 * This module is the thin glue the explorer needs: initialise the wasm module
 * once, keep one store per base URL, and hand it the sequence index the page has
 * already downloaded so nothing is fetched twice.
 */

import { RemoteRefgetStore } from '@databio/gtars/remote';
import type { RefgetWasm, SeqMeta } from '@databio/gtars/remote';
import type { SequenceRow } from '../types';

type Gtars = typeof import('@databio/gtars');

/**
 * Alphabets whose `.seq` bytes are bit-packed and byte-addressable, i.e. the
 * ones RemoteRefgetStore can decode. Anything else is not offered in the UI.
 */
const EXTRACTABLE_ALPHABETS = new Set(['dna2bit', 'dna3bit', 'dnaio', 'dnaiupac']);

export const isExtractable = (alphabet?: string): boolean =>
  !!alphabet && EXTRACTABLE_ALPHABETS.has(alphabet.toLowerCase());

// Lazy wasm init, the same dynamic-import + default() pattern the VRS worker uses.
let gtars: Gtars | null = null;
const initWasm = async (): Promise<Gtars> => {
  if (gtars) return gtars;
  const mod = await import('@databio/gtars');
  await mod.default();
  gtars = mod;
  return gtars;
};

/** One store per base URL, plus the index array it was last given. */
const stores = new Map<string, { store: RemoteRefgetStore; index: SequenceRow[] }>();

/** The rows a RemoteRefgetStore can use: named, digested sequences. */
const toSeqMetas = (rows: SequenceRow[]): SeqMeta[] =>
  rows
    .filter((r) => r.name && r.sha512t24u)
    .map((r) => ({
      name: String(r.name),
      length: r.length,
      alphabet: String(r.alphabet ?? ''),
      sha512t24u: String(r.sha512t24u),
      md5: String(r.md5 ?? ''),
    }));

const getStore = async (
  baseUrl: string,
  sequenceIndex: SequenceRow[],
): Promise<RemoteRefgetStore> => {
  const cached = stores.get(baseUrl);
  if (cached) {
    // The page can load more of a partially-loaded index; re-register when it does.
    if (cached.index !== sequenceIndex) {
      cached.store.setSequences(toSeqMetas(sequenceIndex));
      cached.index = sequenceIndex;
    }
    return cached.store;
  }

  const wasm = await initWasm();
  // The published typings declare `encodedByteRange` as `number[]`; the wasm
  // module returns a Uint32Array. Both destructure to [bs, be], which is all
  // RemoteRefgetStore does with it, so the mismatch is in the .d.ts only.
  const store = new RemoteRefgetStore({ baseUrl, wasm: wasm as unknown as RefgetWasm });
  await store.prepare();
  store.setSequences(toSeqMetas(sequenceIndex));
  stores.set(baseUrl, { store, index: sequenceIndex });
  return store;
};

export interface ExtractRegionArgs {
  baseUrl: string;
  sequenceIndex: SequenceRow[];
  name: string;
  /** 0-based inclusive. */
  start: number;
  /** 0-based exclusive. */
  end: number;
}

/** Read bases [start, end) of `name`. Errors propagate to the caller. */
export const extractRegion = async ({
  baseUrl,
  sequenceIndex,
  name,
  start,
  end,
}: ExtractRegionArgs): Promise<string> => {
  const store = await getStore(baseUrl, sequenceIndex);
  return store.getSubstring(name, start, end);
};

/** Wrap bases to `width` columns, the FASTA convention. */
export const wrapBases = (bases: string, width = 60): string =>
  bases.replace(new RegExp(`(.{${width}})`, 'g'), '$1\n').trimEnd();
