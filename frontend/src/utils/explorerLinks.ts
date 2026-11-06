/**
 * Links that keep the API Explorer on the API it is browsing.
 *
 * Explorer pages name the explored API in a `?url=` query parameter. Pass the
 * explored API as `apiUrl`; pass null outside the explorer to get this site's
 * own pages, which use API_BASE.
 */

/** The `?url=` suffix for an explored API, or '' outside the explorer. */
export const apiQuery = (apiUrl?: string | null): string =>
  apiUrl ? `?url=${encodeURIComponent(apiUrl)}` : '';

/** The attribute page, on the explored API if there is one. */
export const attributePath = (attribute: string, digest: string, apiUrl?: string | null): string =>
  `/attribute/${attribute}/${digest}${apiQuery(apiUrl)}`;

/** The explorer's view of a collection, or this site's own collection page. */
export const collectionPath = (digest: string, apiUrl?: string | null): string =>
  apiUrl ? `/explore-api/collection/${digest}${apiQuery(apiUrl)}` : `/collection/${digest}`;

/** What spec v1.0.0's standard schema marks transient. */
const DEFAULT_TRANSIENT = ['sorted_name_length_pairs'];

type SeqcolInfo = { schema?: { ga4gh?: { transient?: unknown } } | null };

/**
 * Attributes the API's schema marks transient. The spec says /attribute does
 * not serve these, so there is no attribute page to link to.
 */
export const transientAttributes = (
  // A ServiceInfo; typed loosely so this file (and its test) need not import ../types.
  serviceInfo?: Record<string, unknown> | null,
): string[] => {
  const schema = (serviceInfo?.seqcol as SeqcolInfo | undefined)?.schema;
  if (!schema) return DEFAULT_TRANSIENT;
  const transient = schema.ga4gh?.transient;
  return Array.isArray(transient)
    ? transient.filter((a): a is string => typeof a === 'string')
    : [];
};
