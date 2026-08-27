/**
 * Shared shapes for the seqcol/refget API payloads.
 *
 * These are deliberately open (`[key: string]: unknown`): the server returns
 * level-1/level-2 collections whose attribute set is data-dependent, and the
 * explorer renders whatever comes back. The named fields are the ones the UI
 * reads by name; the index signature keeps the rest reachable without pretending
 * to a schema we do not control.
 */

export interface ServiceInfoVersion {
  refget_version?: string;
  gtars_version?: string;
  python_version?: string;
  seqcol_spec_version?: string;
}

export interface ServiceInfo {
  id?: string;
  name?: string;
  description?: string;
  version?: ServiceInfoVersion;
  [key: string]: unknown;
}

/** Context handed down from the root route to every page via <Outlet>. */
export interface AppOutletContext {
  apiAvailable: boolean;
  serviceInfo: ServiceInfo | null;
}

/** A level-1 collection: attribute name -> digest. */
export interface SeqColLevel1 {
  lengths?: string;
  names?: string;
  sequences?: string;
  sorted_sequences?: string;
  name_length_pairs?: string;
  sorted_name_length_pairs?: string;
  [attribute: string]: string | undefined;
}

/** A level-2 collection: attribute name -> the array of values. */
export interface SeqColLevel2 {
  lengths?: number[];
  names?: string[];
  sequences?: string[];
  sorted_sequences?: string[];
  [attribute: string]: unknown;
}

export interface PagedResult<T> {
  results: T[];
  pagination?: {
    page?: number;
    page_size?: number;
    total?: number;
  };
  [key: string]: unknown;
}

/**
 * A /comparison response. The nested objects are declared required because the
 * spec guarantees them; callers still guard on them before reading, since a
 * malformed or truncated response is a real failure mode.
 */
export interface ComparisonResult {
  digests: { a: string; b: string };
  attributes: {
    a_only: string[];
    b_only: string[];
    a_and_b: string[];
  };
  array_elements: {
    a_count: Record<string, number>;
    b_count: Record<string, number>;
    a_and_b_count: Record<string, number>;
    a_and_b_same_order: Record<string, boolean | null>;
  };
  [key: string]: unknown;
}

/**
 * A router error. `useRouteError()` is typed `unknown`; every error this app
 * raises is either a plain Error, an `AppError` from the fetch layer, or a
 * router ErrorResponse, and this union covers reading all three.
 */
export interface AppError extends Error {
  status?: number | null;
  statusText?: string;
  isNotFound?: boolean;
  digest1?: string | null;
  digest2?: string | null;
}

/* ------------------------------------------------------------ RefgetStore */

/** One row of a parsed TSV: column name -> cell text. */
export type TsvRow = Record<string, string>;

export interface TsvParseResult {
  metadata: Record<string, string>;
  rows: TsvRow[];
}

export interface AliasRow {
  alias: string;
  digest: string;
}

/** A row of collections.rgci, with n_sequences already parsed to a number. */
export interface CollectionSummary {
  digest: string;
  n_sequences: number;
  names_digest?: string;
  sequences_digest?: string;
  lengths_digest?: string;
  name_length_pairs_digest?: string;
  sorted_name_length_pairs_digest?: string;
  sorted_sequences_digest?: string;
  [column: string]: string | number | undefined;
}

/** A row of sequences.rgsi (or a collection's sequence list). */
export interface SequenceRow {
  name?: string;
  length: number;
  sha512t24u?: string;
  md5?: string;
  alphabet?: string;
  [column: string]: string | number | undefined;
}

/** What `fetchBoundedList` resolves to: rows plus how much of the file was read. */
export interface BoundedList<T> {
  rows: T[];
  partial: boolean;
  totalSize: number;
}

export interface StoreMetadata {
  name?: string;
  description?: string;
  version?: string;
  created?: string;
  mode?: string;
  sequence_alias_namespaces?: string[];
  collection_alias_namespaces?: string[];
  seqdata_path_template?: string;
  collections_path_template?: string;
  collection_index?: string;
  [key: string]: unknown;
}

export interface CollectionDetail {
  metadata: Record<string, string>;
  sequences: SequenceRow[];
}

/** One collection alias, as indexed by `buildCollectionAliasMap`. */
export interface AliasEntry {
  namespace: string;
  alias: string;
}

export type CollectionAliasMap = Record<string, AliasEntry[]>;

/* ------------------------------------------------------------ SIMILARITY */

/**
 * One row of a /similarities response: the collection being compared against,
 * plus a per-attribute similarity score. The attribute set is server-driven, so
 * scores are read through the index signature.
 */
export interface SimilarityRow {
  comparedDigest: string;
  comparedAlias?: string;
  /** The digest this row was compared against (the matrix's other axis). */
  selectedDigest?: string;
  human_readable_names?: string[];
  /** Set by the UI, not the server: the row came from a user-built collection. */
  custom?: boolean;
  /** Set by the UI: the row is currently selected in the matrix. */
  selected?: boolean;
  [attribute: string]: unknown;
}

/** A collection the user assembled by hand in the SCOM builder. */
export interface CustomCollection {
  selectedDigest: string;
  [key: string]: unknown;
}

/** The shape SCOM passes around for the server's collection listing. */
export interface CollectionListing {
  results: string[];
  [key: string]: unknown;
}

/* ----------------------------------------------------------- WEB WORKERS */

/**
 * The slice of a dedicated worker's global scope our workers use.
 *
 * TypeScript cannot load the DOM and WebWorker libraries into one program, and
 * the app needs DOM, so the worker modules name what they need rather than
 * pretending `self` is a `Window`.
 */
export interface WorkerScope {
  onmessage: ((e: MessageEvent) => void) | null;
  postMessage(message: unknown, transfer?: Transferable[]): void;
  addEventListener(type: 'message', listener: (e: MessageEvent) => void): void;
}

/* -------------------------------------------------------- FASTA DIGEST */

/** What the in-browser FASTA hasher returns for one file. */
export interface SeqColDigestResult {
  digest: string;
  names_digest?: string;
  sequences_digest?: string;
  lengths_digest?: string;
  sorted_sequences_digest?: string;
  n_sequences: number;
  sequences: SequenceRow[];
  [key: string]: unknown;
}
