import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useUnifiedStore } from '../stores/unifiedStore.js';
import { useExplorerStore } from '../stores/explorerStore.js';
import { ExplorerNav } from '../components/ExplorerNav.jsx';
import { fetchSeqColList } from '../services/fetchData.jsx';

const Explorer = () => {
  const { hasStore, hasAPI, storeUrl, apiUrl, storeCollections, probe, probed, loading: probing } =
    useUnifiedStore();
  const { loadStore, metadata, loadAliases } = useExplorerStore();
  const [apiCollections, setApiCollections] = useState(null);
  const [aliasMap, setAliasMap] = useState({});
  const [filter, setFilter] = useState('');
  const [sortCol, setSortCol] = useState(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [loading, setLoading] = useState(true);

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
        } catch {}
        // Try to load collection aliases
        try {
          const storeData = useExplorerStore.getState();
          const namespaces = storeData.metadata?.collection_alias_namespaces || [];
          const map = {};
          for (const ns of namespaces) {
            const aliases = await loadAliases('collections', ns).catch(() => null);
            if (aliases) {
              aliases.forEach((a) => {
                if (!map[a.digest]) map[a.digest] = [];
                map[a.digest].push(a.alias);
              });
            }
          }
          setAliasMap(map);
        } catch {}
      }

      // Load API collection list if available
      if (hasAPI) {
        try {
          const result = await fetchSeqColList(apiUrl);
          setApiCollections(result[0]);
        } catch {}
      }

      setLoading(false);
    };
    load();
  }, [probed, hasStore, hasAPI]); // eslint-disable-line react-hooks/exhaustive-deps

  // Merge store collections with API collection list
  // NOTE: useMemo hooks must be called before any early returns to avoid
  // "Rendered more hooks than during the previous render" errors
  const collections = useMemo(() => {
    const byDigest = new Map();

    // Store collections have richer data (n_sequences, attribute digests)
    if (storeCollections) {
      storeCollections.forEach((col) => {
        byDigest.set(col.digest, {
          digest: col.digest,
          n_sequences: col.n_sequences,
          names: aliasMap[col.digest] || [],
          source: 'store',
        });
      });
    }

    // API collections add any that store doesn't have
    if (apiCollections?.results) {
      apiCollections.results.forEach((digest) => {
        if (!byDigest.has(digest)) {
          byDigest.set(digest, {
            digest,
            n_sequences: null,
            names: aliasMap[digest] || [],
            source: 'api',
          });
        }
      });
    }

    return Array.from(byDigest.values());
  }, [storeCollections, apiCollections, aliasMap]);

  const filtered = useMemo(() => {
    if (!filter) return collections;
    const term = filter.toLowerCase();
    return collections.filter(
      (c) =>
        c.digest.toLowerCase().includes(term) ||
        c.names.some((n) => n.toLowerCase().includes(term)),
    );
  }, [collections, filter]);

  const sorted = useMemo(() => {
    if (!sortCol) return filtered;
    return [...filtered].sort((a, b) => {
      let va, vb;
      if (sortCol === 'name') {
        va = (a.names[0] || '').toLowerCase();
        vb = (b.names[0] || '').toLowerCase();
      } else if (sortCol === 'n_sequences') {
        va = a.n_sequences ?? -1;
        vb = b.n_sequences ?? -1;
        return sortAsc ? va - vb : vb - va;
      } else {
        va = (a[sortCol] || '').toLowerCase();
        vb = (b[sortCol] || '').toLowerCase();
      }
      return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    });
  }, [filtered, sortCol, sortAsc]);

  const handleSort = (col) => {
    if (sortCol === col) setSortAsc(!sortAsc);
    else { setSortCol(col); setSortAsc(true); }
  };

  if (probing || loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border" />
        <p className="mt-3 text-muted">Loading collections...</p>
      </div>
    );
  }

  const totalFromApi = apiCollections?.pagination?.total;

  return (
    <div className="mb-5">
      <ExplorerNav active="collections" />

      <div className="d-flex justify-content-between align-items-center mb-3">
        <span className="text-muted">
          {filtered.length} collection{filtered.length !== 1 ? 's' : ''}
          {totalFromApi != null && ` (${totalFromApi} total on server)`}
          {filter && ` matching "${filter}"`}
        </span>
        <input
          type="search"
          className="form-control form-control-sm"
          style={{ maxWidth: '300px' }}
          placeholder="Filter by name or digest..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>

      {!hasStore && !hasAPI && (
        <div className="alert alert-warning">
          Neither a RefgetStore nor an API was detected at this server.
          Try the <Link to="/explore-store">Store Explorer</Link> or{' '}
          <Link to="/explore-api">API Explorer</Link> to connect to a specific URL.
        </div>
      )}

      {sorted.length > 0 ? (
        <div className="table-responsive">
          <table className="table table-sm table-hover">
            <thead>
              <tr>
                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('name')}>
                  Name
                  {sortCol === 'name' && <i className={`bi bi-caret-${sortAsc ? 'up' : 'down'}-fill ms-1`} />}
                </th>
                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('digest')}>
                  Digest
                  {sortCol === 'digest' && <i className={`bi bi-caret-${sortAsc ? 'up' : 'down'}-fill ms-1`} />}
                </th>
                {hasStore && (
                  <th className="text-end" style={{ cursor: 'pointer' }} onClick={() => handleSort('n_sequences')}>
                    Sequences
                    {sortCol === 'n_sequences' && <i className={`bi bi-caret-${sortAsc ? 'up' : 'down'}-fill ms-1`} />}
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {sorted.map((col) => (
                <tr key={col.digest}>
                  <td>
                    {col.names.length > 0
                      ? [...new Set(col.names)].join(', ')
                      : <span className="text-muted">-</span>}
                  </td>
                  <td>
                    <Link
                      to={`/collection/${col.digest}`}
                      className="font-monospace small"
                    >
                      {col.digest}
                    </Link>
                  </td>
                  {hasStore && (
                    <td className="text-end">
                      {col.n_sequences != null ? col.n_sequences : '-'}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-muted">No collections found.</p>
      )}
    </div>
  );
};

export { Explorer };
