// Collection alias helpers.
//
// A collection has no name: SequenceCollectionMetadata carries only digests and
// n_sequences. Human-readable labels come entirely from the alias subsystem,
// where a "namespace" is just the stem of an aliases/collections/*.tsv file.
// gtars treats it as an opaque string — nothing is reserved or special-cased —
// so which namespaces exist is per-store convention.

/**
 * Display preference for collections carrying aliases in several namespaces.
 * Purely a UI choice; mirrors the probe order used by components/vrs/vrsWorker.js.
 */
export const COLLECTION_NAMESPACE_PRIORITY = [
  'genome_assembly',
  'name',
  'accession',
  'refseq',
  'insdc',
];

/**
 * Load every collection-alias namespace and index the results by digest.
 *
 * `loadAliases` is the explorer store's loader, which resolves to
 * { rows: [{alias, digest}], partial, totalSize } — or null when the namespace
 * file is missing. Namespaces that fail are skipped: aliases are decoration,
 * and a store without them must still render.
 *
 * @returns {Promise<Object>} digest -> [{ namespace, alias }]
 */
export const buildCollectionAliasMap = async (namespaces, loadAliases) => {
  const map = {};
  for (const namespace of namespaces) {
    const data = await loadAliases('collections', namespace).catch(() => null);
    if (!data?.rows) continue;
    data.rows.forEach(({ alias, digest }) => {
      if (!map[digest]) map[digest] = [];
      map[digest].push({ namespace, alias });
    });
  }
  return map;
};

/**
 * Choose one alias to show, preferring COLLECTION_NAMESPACE_PRIORITY and falling
 * back to whatever the store happens to carry.
 *
 * @returns {{primary: string|null, all: string[]}} `all` is a deduped
 *   "namespace: alias" list, suitable for a tooltip.
 */
export const preferredAlias = (entries) => {
  if (!entries || entries.length === 0) return { primary: null, all: [] };
  const all = [...new Set(entries.map((e) => `${e.namespace}: ${e.alias}`))];
  for (const namespace of COLLECTION_NAMESPACE_PRIORITY) {
    const hit = entries.find((e) => e.namespace === namespace);
    if (hit) return { primary: hit.alias, all };
  }
  return { primary: entries[0].alias, all };
};
