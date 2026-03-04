/**
 * Service for fetching and parsing RefgetStore static files.
 * A RefgetStore is a directory of static TSV/JSON files — no backend needed.
 */

// Ensure URL ends without trailing slash
const normalizeUrl = (url) => url.replace(/\/+$/, '');

/**
 * Parse TSV text into array of objects.
 * Handles # comment header lines and ## metadata headers.
 * Returns { metadata: {key: value}, rows: [{col: val}] }
 */
const parseTsv = (text) => {
  const lines = text.split('\n').filter((l) => l.length > 0);
  const metadata = {};
  let headerCols = null;
  const rows = [];

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
      const row = {};
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
const parseAliasTsv = (text) => {
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
const parseRgci = (text) => {
  const { rows } = parseTsv(text);
  return rows.map((r) => ({
    ...r,
    n_sequences: r.n_sequences ? parseInt(r.n_sequences, 10) : 0,
  }));
};

/** Fetch with error handling */
const fetchFile = async (url) => {
  const response = await fetch(url);
  if (!response.ok) {
    if (response.status === 404 || response.status === 403) return null;
    throw new Error(`HTTP ${response.status} fetching ${url}`);
  }
  return response;
};

/** GET rgstore.json → parsed JSON */
export const fetchStoreMetadata = async (baseUrl) => {
  const url = `${normalizeUrl(baseUrl)}/rgstore.json`;
  const response = await fetchFile(url);
  if (!response) throw new Error('rgstore.json not found at this URL');
  return response.json();
};

/** Size threshold for auto-loading sequence index (10 MB) */
const AUTO_LOAD_THRESHOLD = 10 * 1024 * 1024;
/** Default partial load size (2 MB) */
const PARTIAL_LOAD_SIZE = 2 * 1024 * 1024;

const parseSequenceRows = (text) => {
  const { rows } = parseTsv(text);
  return rows.map((r) => ({
    ...r,
    length: r.length ? parseInt(r.length, 10) : 0,
  }));
};

/**
 * Check the size of sequences.rgsi via HEAD request.
 * Returns { url, size } or null if not found.
 */
export const checkSequenceIndexSize = async (baseUrl) => {
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
 * Fetch sequences.rgsi — auto-loads if small, otherwise requires explicit call.
 * Returns { rows, partial, totalSize }
 *   partial: true if only a prefix was loaded
 *   totalSize: file size in bytes
 */
export const fetchSequenceIndex = async (baseUrl, { maxBytes } = {}) => {
  const url = `${normalizeUrl(baseUrl)}/sequences.rgsi`;

  // Check file size first
  let totalSize = 0;
  try {
    const head = await fetch(url, { method: 'HEAD' });
    if (!head.ok) {
      if (head.status === 404 || head.status === 403) throw new Error('sequences.rgsi not found');
      throw new Error(`HTTP ${head.status} fetching ${url}`);
    }
    totalSize = parseInt(head.headers.get('content-length') || '0', 10);
  } catch (err) {
    if (err.message.includes('not found')) throw err;
    // HEAD failed (CORS?), fall back to full fetch
    const response = await fetchFile(url);
    if (!response) throw new Error('sequences.rgsi not found');
    const text = await response.text();
    return { rows: parseSequenceRows(text), partial: false, totalSize: text.length };
  }

  const limit = maxBytes || (totalSize <= AUTO_LOAD_THRESHOLD ? totalSize : PARTIAL_LOAD_SIZE);
  const loadFull = limit >= totalSize;

  if (loadFull) {
    const response = await fetchFile(url);
    if (!response) throw new Error('sequences.rgsi not found');
    const text = await response.text();
    return { rows: parseSequenceRows(text), partial: false, totalSize };
  }

  // Partial load via Range header
  const response = await fetch(url, {
    headers: { Range: `bytes=0-${limit - 1}` },
  });
  if (!response.ok && response.status !== 206) {
    // Server doesn't support Range — fall back to full fetch
    const fullResponse = await fetchFile(url);
    if (!fullResponse) throw new Error('sequences.rgsi not found');
    const text = await fullResponse.text();
    return { rows: parseSequenceRows(text), partial: false, totalSize };
  }
  const text = await response.text();
  // Discard last partial line
  const lastNewline = text.lastIndexOf('\n');
  const cleanText = lastNewline > 0 ? text.substring(0, lastNewline) : text;
  return { rows: parseSequenceRows(cleanText), partial: true, totalSize };
};

/** GET collections.rgci → array of collection summaries */
export const fetchCollectionIndex = async (baseUrl) => {
  const url = `${normalizeUrl(baseUrl)}/collections.rgci`;
  const response = await fetchFile(url);
  if (!response) return null; // No collection index available
  const text = await response.text();
  return parseRgci(text);
};

/** GET collections/{digest}.rgsi → {metadata, sequences} */
export const fetchCollection = async (baseUrl, digest) => {
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

/** GET aliases/{type}/{namespace}.tsv → [{alias, digest}] */
export const fetchAliases = async (baseUrl, type, namespace) => {
  const url = `${normalizeUrl(baseUrl)}/aliases/${type}/${namespace}.tsv`;
  const response = await fetchFile(url);
  if (!response) return null;
  const text = await response.text();
  return parseAliasTsv(text);
};

/** GET collections/{digest}.fhr.json → parsed JSON or null */
export const fetchFhrMetadata = async (baseUrl, digest) => {
  const url = `${normalizeUrl(baseUrl)}/collections/${digest}.fhr.json`;
  const response = await fetchFile(url);
  if (!response) return null;
  return response.json();
};
