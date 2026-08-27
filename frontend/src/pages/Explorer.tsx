import { useState, useEffect, useMemo, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useUnifiedStore } from '../stores/unifiedStore';
import { useExplorerStore } from '../stores/explorerStore';
import { ExplorerNav } from '../components/ExplorerNav';
import { PaginationNav } from '../components/PaginationNav';
import { fetchSeqColList } from '../services/fetchData';
import { fetchCollectionIndex } from '../services/storeService';
import { buildCollectionAliasMap, preferredAlias } from '../services/aliases';
import { Icon } from '../components/common/Icon';
import type { AliasEntry, CollectionAliasMap, CollectionSummary, PagedResult } from '../types';

/** One row of the merged collection table: store data, API data, or both. */
interface ExplorerRow {
  digest: string;
  n_sequences: number | null;
  aliases: AliasEntry[];
  source: 'store' | 'api';
}

const PAGE_SIZE = 50;

const Explorer = () => {
  const { hasStore, hasAPI, storeUrl, apiUrl, storeCollections, probe, probed, loading: probing } =
    useUnifiedStore();
  const { loadStore, loadAliases } = useExplorerStore();
  const [apiCollections, setApiCollections] = useState<PagedResult<string> | null>(null);
  const [aliasMap, setAliasMap] = useState<CollectionAliasMap>({});
  const [filter, setFilter] = useState('');
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  // Holds a cache-bypassing re-fetch of the store index when it disagrees with the API.
  const [storeOverride, setStoreOverride] = useState<CollectionSummary[] | null>(null);
  const revalidatedRef = useRef(false);

  useEffect(() => {
    const init = async () => {
      await probe();
    };
    init();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!probed) return;

    const load = async () => {
      // Load store data if available
      if (hasStore && storeUrl) {
        try {
          await loadStore(storeUrl);
        } catch { /* store load is best-effort; ignore failures */ }
        // Try to load collection aliases
        try {
          const storeData = useExplorerStore.getState();
          const namespaces = storeData.metadata?.collection_alias_namespaces || [];
          setAliasMap(await buildCollectionAliasMap(namespaces, loadAliases));
        } catch { /* aliases are optional; ignore failures */ }
      }

      // Load API collection list if available
      if (hasAPI) {
        try {
          const result = await fetchSeqColList(apiUrl);
          setApiCollections(result[0]);
        } catch { /* API list is optional; ignore failures */ }
      }

      setLoading(false);
    };
    load();
  }, [probed, hasStore, hasAPI]); // eslint-disable-line react-hooks/exhaustive-deps

  // Prefer a freshly revalidated store index over the (possibly cached) probe result.
  const effectiveStoreCollections = storeOverride ?? storeCollections;

  // Self-validating revalidation: the store index (collections.rgci) and the store-backed
  // API are two views of the SAME store, so their collection counts must agree. If they
  // don't, the likely cause is a stale browser-cached index file — so revalidate BOTH
  // once, bypassing the HTTP cache, and reconcile to whatever they then report. Guarded
  // to run at most once (a genuine version/superset difference must not loop).
  useEffect(() => {
    if (loading || probing || revalidatedRef.current) return;
    const apiTotal = apiCollections?.pagination?.total;
    const storeLen = effectiveStoreCollections?.length;
    if (apiTotal == null || storeLen == null || storeLen === apiTotal) return;

    revalidatedRef.current = true;
    (async () => {
      const [freshStore, freshApi] = await Promise.all([
        storeUrl ? fetchCollectionIndex(storeUrl, { cache: 'reload' }).catch(() => null) : null,
        hasAPI ? fetchSeqColList(apiUrl, { cache: 'reload' }).catch(() => null) : null,
      ]);
      if (freshStore) setStoreOverride(freshStore);
      if (freshApi?.[0]) setApiCollections(freshApi[0]);
    })();
  }, [loading, probing, apiCollections, effectiveStoreCollections, storeUrl, apiUrl, hasAPI]);

  // Merge store collections with API collection list
  // NOTE: useMemo hooks must be called before any early returns to avoid
  // "Rendered more hooks than during the previous render" errors
  const collections = useMemo(() => {
    const byDigest = new Map<string, ExplorerRow>();

    // Store collections have richer data (n_sequences, attribute digests)
    if (effectiveStoreCollections) {
      effectiveStoreCollections.forEach((col) => {
        byDigest.set(col.digest, {
          digest: col.digest,
          n_sequences: col.n_sequences,
          aliases: aliasMap[col.digest] || [],
          source: 'store',
        });
      });
    }

    // API collections add any that store doesn't have
    if (apiCollections?.results) {
      apiCollections.results.forEach((digest: string) => {
        if (!byDigest.has(digest)) {
          byDigest.set(digest, {
            digest,
            n_sequences: null,
            aliases: aliasMap[digest] || [],
            source: 'api',
          });
        }
      });
    }

    return Array.from(byDigest.values());
  }, [effectiveStoreCollections, apiCollections, aliasMap]);

  const filtered = useMemo(() => {
    if (!filter) return collections;
    const term = filter.toLowerCase();
    return collections.filter(
      (c) =>
        c.digest.toLowerCase().includes(term) ||
        c.aliases.some((a) => a.alias.toLowerCase().includes(term)),
    );
  }, [collections, filter]);

  const sorted = useMemo(() => {
    if (!sortCol) return filtered;
    return [...filtered].sort((a, b) => {
      let va: string;
      let vb: string;
      if (sortCol === 'alias') {
        va = (preferredAlias(a.aliases).primary || '').toLowerCase();
        vb = (preferredAlias(b.aliases).primary || '').toLowerCase();
      } else if (sortCol === 'n_sequences') {
        const na = a.n_sequences ?? -1;
        const nb = b.n_sequences ?? -1;
        return sortAsc ? na - nb : nb - na;
      } else {
        va = String((a as unknown as Record<string, unknown>)[sortCol] ?? '').toLowerCase();
        vb = String((b as unknown as Record<string, unknown>)[sortCol] ?? '').toLowerCase();
      }
      return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    });
  }, [filtered, sortCol, sortAsc]);

  const handleSort = (col: string) => {
    if (sortCol === col) setSortAsc(!sortAsc);
    else { setSortCol(col); setSortAsc(true); }
    setPage(0);
  };

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const clampedPage = Math.min(page, Math.max(0, totalPages - 1));
  const paged = sorted.slice(clampedPage * PAGE_SIZE, (clampedPage + 1) * PAGE_SIZE);

  if (probing || loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner" />
        <p className="mt-4 text-muted">Loading collections...</p>
      </div>
    );
  }

  const totalFromApi = apiCollections?.pagination?.total;

  return (
    <div className="mb-12">
      <ExplorerNav active="collections" />

      <div className="flex justify-between items-center mb-4">
        <span className="text-muted">
          {filtered.length} collection{filtered.length !== 1 ? 's' : ''}
          {totalFromApi != null && ` (${totalFromApi} total on server)`}
          {filter && ` matching "${filter}"`}
        </span>
        <input
          type="search"
          className="form-input form-input--sm filter-input"
          placeholder="Filter by alias or digest..."
          value={filter}
          onChange={(e) => { setFilter(e.target.value); setPage(0); }}
        />
      </div>

      {!hasStore && !hasAPI && (
        <div className="alert alert--warning">
          Neither a RefgetStore nor an API was detected at this server.
          Try the <Link to="/explore-store">Store Explorer</Link> or{' '}
          <Link to="/explore-api">API Explorer</Link> to connect to a specific URL.
        </div>
      )}

      {sorted.length > 0 ? (
        <div className="table-wrap">
          <table className="table table--sm table--hover">
            <thead>
              <tr>
                <th className="cursor-pointer" onClick={() => handleSort('alias')}>
                  Alias
                  {sortCol === 'alias' && <Icon name={sortAsc ? 'caret-up' : 'caret-down'} className='ml-1' />}
                </th>
                <th className="cursor-pointer" onClick={() => handleSort('digest')}>
                  Digest
                  {sortCol === 'digest' && <Icon name={sortAsc ? 'caret-up' : 'caret-down'} className='ml-1' />}
                </th>
                {hasStore && (
                  <th className="text-right cursor-pointer" onClick={() => handleSort('n_sequences')}>
                    Sequences
                    {sortCol === 'n_sequences' && <Icon name={sortAsc ? 'caret-up' : 'caret-down'} className='ml-1' />}
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {paged.map((col) => {
                const { primary, all } = preferredAlias(col.aliases);
                return (
                <tr key={col.digest}>
                  <td>
                    {primary
                      ? <span title={all.length > 1 ? all.join('\n') : undefined}>{primary}</span>
                      : <span className="text-muted">-</span>}
                  </td>
                  <td>
                    <Link
                      to={`/collection/${col.digest}`}
                      className="font-mono text-sm"
                    >
                      {col.digest}
                    </Link>
                  </td>
                  {hasStore && (
                    <td className="text-right">
                      {col.n_sequences != null ? col.n_sequences : '-'}
                    </td>
                  )}
                </tr>
                );
              })}
            </tbody>
          </table>
          <PaginationNav page={clampedPage} totalPages={totalPages} onChange={setPage} />
        </div>
      ) : (
        <p className="text-muted">No collections found.</p>
      )}
    </div>
  );
};

export { Explorer };
