/**
 * Service for fetching and parsing RefgetStore static files.
 * A RefgetStore is a directory of static TSV/JSON files — no backend needed.
 */

import type {
  AliasRow,
  BoundedList,
  CollectionDetail,
  CollectionSummary,
  SequenceRow,
  StoreMetadata,
  TsvParseResult,
  TsvRow,
} from '../types';
import { errorMessage } from '../utils/errors';

/** Options accepted by `fetchBoundedList` and the loaders built on it. */
export interface BoundedListOptions {
  /** Override the auto/partial byte budget. */
  maxBytes?: number;
  /** Behaviour on 404/403. */
  onMissing?: 'throw' | 'null';
}

// Ensure URL ends without trailing slash
const normalizeUrl = (url: string): string => url.replace(/\/+$/, '');

/**
 * Parse TSV text into array of objects.
 * Handles # comment header lines and ## metadata headers.
 * Returns { metadata: {key: value}, rows: [{col: val}] }
 */
const parseTsv = (text: string): TsvParseResult => {
  const lines = text.split('\n').filter((l) => l.length > 0);
  const metadata: Record<string, string> = {};
  let headerCols: string[] | null = null;
  const rows: TsvRow[] = [];

  for (const line of lines) {
    if (line.startsWith('##')) {
      // Metadata header: ##key=value
      const eq = line.indexOf('=');
      if (eq > 2) {
        metadata[line.substring(2, eq)] = line.substring(eq + 1);
      }
    } else if (line.startsWith('#')) {
      // Column header
      headerCols = line.substring(1).split('\t');
    } else if (headerCols) {
      const fields = line.split('\t');
      const row: TsvRow = {};
      headerCols.forEach((col, i) => {
        row[col] = fields[i] ?? '';
      });
      rows.push(row);
    }
  }

  return { metadata, rows };
};

/**
 * Parse a two-column TSV (alias files have no header).
 * Returns [{alias, digest}]
 */
const parseAliasTsv = (text: string): AliasRow[] => {
  return text
    .split('\n')
    .filter((l) => l.length > 0 && !l.startsWith('#'))
    .map((line) => {
      const [alias, digest] = line.split('\t');
      return { alias, digest };
    });
};

/**
 * Parse collections.rgci — a TSV with #header row.
 * Columns: digest, n_sequences, names_digest, sequences_digest, lengths_digest,
 *          name_length_pairs_digest, sorted_name_length_pairs_digest, sorted_sequences_digest
 */
const parseRgci = (text: string): CollectionSummary[] => {
  const { rows } = parseTsv(text);
  return rows.map((r) => ({
    ...r,
    digest: r.digest ?? '',
    n_sequences: r.n_sequences ? parseInt(r.n_sequences, 10) : 0,
  }));
};

/** Fetch with error handling. `opts` is passed through to fetch() (e.g. { cache: 'reload' }). */
const fetchFile = async (url: string, opts: RequestInit = {}): Promise<Response | null> => {
  const response = await fetch(url, opts);
  if (!response.ok) {
    if (response.status === 404 || response.status === 403) return null;
    throw new Error(`HTTP ${response.status} fetching ${url}`);
  }
  return response;
};

/** GET rgstore.json → parsed JSON */
export const fetchStoreMetadata = async (baseUrl: string): Promise<StoreMetadata> => {
  const url = `${normalizeUrl(baseUrl)}/rgstore.json`;
  const response = await fetchFile(url);
  if (!response) throw new Error('rgstore.json not found at this URL');
  return response.json();
};

/** Size threshold for auto-loading sequence index (10 MB) */
const AUTO_LOAD_THRESHOLD = 10 * 1024 * 1024;
/** Default partial load size (2 MB) */
const PARTIAL_LOAD_SIZE = 2 * 1024 * 1024;

const parseSequenceRows = (text: string): SequenceRow[] => {
  const { rows } = parseTsv(text);
  return rows.map((r) => ({
    ...r,
    length: r.length ? parseInt(r.length, 10) : 0,
  }));
};

/**
 * Fetch a newline-delimited list file within a byte budget.
 *
 * For files larger than AUTO_LOAD_THRESHOLD, only the first PARTIAL_LOAD_SIZE
 * bytes are loaded (via an HTTP Range request), the trailing partial line is
 * discarded, and `partial` is returned true — callers can re-request with
 * `{ maxBytes: totalSize }` to load the whole file. Falls back to a full fetch
 * when the server supports neither HEAD nor Range (e.g. CORS restrictions).
 *
 * `parse` is handed the (possibly truncated) text.
 */
export const fetchBoundedList = async <T>(
  url: string,
  parse: (text: string) => T[],
  { maxBytes, onMissing = 'throw' }: BoundedListOptions = {},
): Promise<BoundedList<T> | null> => {
  const missing = (): null => {
    if (onMissing === 'null') return null;
    throw new Error(`${url} not found`);
  };

  // Resolve the total size up front so we can decide whether to bound the load.
  let totalSize: number;
  try {
    const head = await fetch(url, { method: 'HEAD' });
    if (!head.ok) {
      if (head.status === 404 || head.status === 403) return missing();
      throw new Error(`HTTP ${head.status} fetching ${url}`);
    }
    totalSize = parseInt(head.headers.get('content-length') || '0', 10);
  } catch (err) {
    if (err instanceof Error && errorMessage(err).includes('not found')) throw err;
    // HEAD failed (e.g. CORS) — fall back to a full fetch.
    const response = await fetchFile(url);
    if (!response) return missing();
    const text = await response.text();
    return { rows: parse(text), partial: false, totalSize: text.length };
  }

  const limit = maxBytes || (totalSize <= AUTO_LOAD_THRESHOLD ? totalSize : PARTIAL_LOAD_SIZE);
  const loadFull = limit >= totalSize;

  if (loadFull) {
    const response = await fetchFile(url);
    if (!response) return missing();
    const text = await response.text();
    return { rows: parse(text), partial: false, totalSize };
  }

  // Partial load via Range header.
  const response = await fetch(url, { headers: { Range: `bytes=0-${limit - 1}` } });
  if (!response.ok && response.status !== 206) {
    // Server doesn't support Range — fall back to a full fetch.
    const fullResponse = await fetchFile(url);
    if (!fullResponse) return missing();
    const text = await fullResponse.text();
    return { rows: parse(text), partial: false, totalSize };
  }
  const text = await response.text();
  // Discard the trailing partial line so the parser never sees a truncated row.
  const lastNewline = text.lastIndexOf('\n');
  const cleanText = lastNewline > 0 ? text.substring(0, lastNewline) : text;
  return { rows: parse(cleanText), partial: true, totalSize };
};

/**
 * Check the size of sequences.rgsi via HEAD request.
 * Returns { url, size } or null if not found.
 */
export const checkSequenceIndexSize = async (
  baseUrl: string,
): Promise<{ url: string; size: number } | null> => {
  const url = `${normalizeUrl(baseUrl)}/sequences.rgsi`;
  try {
    const response = await fetch(url, { method: 'HEAD' });
    if (!response.ok) return null;
    const size = parseInt(response.headers.get('content-length') || '0', 10);
    return { url, size };
  } catch {
    return null;
  }
};

/**
 * Fetch sequences.rgsi — auto-loads if small, otherwise loads a bounded prefix.
 * Returns { rows, partial, totalSize }.
 */
export const fetchSequenceIndex = (baseUrl: string, opts: BoundedListOptions = {}) =>
  fetchBoundedList(`${normalizeUrl(baseUrl)}/sequences.rgsi`, parseSequenceRows, opts);

/** GET collections.rgci → array of collection summaries. `opts` passes through to fetch(). */
export const fetchCollectionIndex = async (
  baseUrl: string,
  opts: RequestInit = {},
): Promise<CollectionSummary[] | null> => {
  const url = `${normalizeUrl(baseUrl)}/collections.rgci`;
  const response = await fetchFile(url, opts);
  if (!response) return null; // No collection index available
  const text = await response.text();
  return parseRgci(text);
};

/** GET collections/{digest}.rgsi → {metadata, sequences} */
export const fetchCollection = async (
  baseUrl: string,
  digest: string,
): Promise<CollectionDetail> => {
  const base = normalizeUrl(baseUrl);
  // Try .rgsi first (format spec default), then .rgci
  let response = await fetchFile(`${base}/collections/${digest}.rgsi`);
  if (!response) {
    response = await fetchFile(`${base}/collections/${digest}.rgci`);
  }
  if (!response)
    throw new Error(`Collection ${digest} not found`);
  const text = await response.text();
  const { metadata, rows } = parseTsv(text);
  return {
    metadata,
    sequences: rows.map((r) => ({
      ...r,
      length: r.length ? parseInt(r.length, 10) : 0,
    })),
  };
};

/**
 * GET aliases/{type}/{namespace}.tsv — bounded prefix for large namespaces.
 * Returns { rows: [{alias, digest}], partial, totalSize }, or null if missing.
 */
export const fetchAliases = (
  baseUrl: string,
  type: string,
  namespace: string,
  opts: BoundedListOptions = {},
) =>
  fetchBoundedList(
    `${normalizeUrl(baseUrl)}/aliases/${type}/${namespace}.tsv`,
    parseAliasTsv,
    { ...opts, onMissing: 'null' },
  );

/** GET collections/{digest}.fhr.json → parsed JSON or null */
export const fetchFhrMetadata = async (
  baseUrl: string,
  digest: string,
): Promise<Record<string, unknown> | null> => {
  const url = `${normalizeUrl(baseUrl)}/collections/${digest}.fhr.json`;
  const response = await fetchFile(url);
  if (!response) return null;
  return response.json();
};
