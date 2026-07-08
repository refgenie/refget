import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useUnifiedStore } from '../stores/unifiedStore.js';
import { useExplorerStore } from '../stores/explorerStore.js';
import { ExplorerNav } from '../components/ExplorerNav.jsx';
import { PaginationNav } from '../components/PaginationNav.jsx';
import { PartialLoadBanner } from '../components/PartialLoadBanner.jsx';
import { usePagedList } from '../hooks/usePagedList.js';

const aliasFilter = (a, term) =>
  a.alias.toLowerCase().includes(term) || a.digest.toLowerCase().includes(term);

const AliasPanel = ({ type, availableNamespaces }) => {
  const { loadAliases } = useExplorerStore();
  const [namespace, setNamespace] = useState('');
  const [aliasData, setAliasData] = useState(null); // { rows, partial, totalSize }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { filter, setFilter, page, setPage, paged, filtered, totalPages } =
    usePagedList(aliasData?.rows, { filterFn: aliasFilter });

  const loadNamespace = (ns, options) => {
    setError(null);
    setLoading(true);
    loadAliases(type, ns, options)
      .then((data) => {
        if (!data) {
          setError(`Namespace "${ns}" not found.`);
          setAliasData(null);
        } else {
          setAliasData(data);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const handleNamespaceClick = (ns) => {
    setNamespace(ns);
    setFilter('');
    loadNamespace(ns);
  };

  const linkPrefix = type === 'collections' ? '/collection/' : null;

  return (
    <div className="card mb-3">
      <div className="card-header">
        <h6 className="mb-0 text-capitalize">
          <i className={`bi ${type === 'sequences' ? 'bi-list-ol' : 'bi-collection'} me-2`} />
          {type} aliases
        </h6>
      </div>
      <div className="card-body">
        {availableNamespaces && availableNamespaces.length > 0 ? (
          <div className="mb-3">
            <span className="text-muted small me-2">Namespaces:</span>
            {availableNamespaces.map((ns) => (
              <button
                key={ns}
                className={`btn btn-sm me-1 mb-1 ${namespace === ns ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => handleNamespaceClick(ns)}
                disabled={loading}
              >
                {ns}
              </button>
            ))}
            {loading && <span className="spinner-border spinner-border-sm ms-2" />}
          </div>
        ) : (
          <p className="text-muted small mb-0">
            No {type} alias namespaces found.
          </p>
        )}

        {error && <div className="alert alert-warning small py-2">{error}</div>}

        {aliasData && (
          <>
            {aliasData.partial && (
              <PartialLoadBanner
                totalSize={aliasData.totalSize}
                loadedCount={aliasData.rows.length}
                noun="aliases"
                onLoadAll={() => loadNamespace(namespace, { maxBytes: aliasData.totalSize })}
                loading={loading}
              />
            )}
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span className="text-muted small">
                {filtered.length.toLocaleString()} aliases in &quot;{namespace}&quot;
                {aliasData.partial && ' (partial)'}
              </span>
              <input
                type="search"
                className="form-control form-control-sm"
                style={{ maxWidth: '250px' }}
                placeholder="Filter..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </div>
            <div className="table-responsive" style={{ maxHeight: '400px' }}>
              <table className="table table-sm table-hover mb-0">
                <thead className="sticky-top bg-white">
                  <tr>
                    <th>Alias</th>
                    <th>Digest</th>
                  </tr>
                </thead>
                <tbody>
                  {paged.map((a) => (
                    <tr key={`${a.alias}-${a.digest}`}>
                      <td>{a.alias}</td>
                      <td className="font-monospace small">
                        {linkPrefix ? (
                          <Link to={`${linkPrefix}${a.digest}`}>{a.digest}</Link>
                        ) : (
                          a.digest
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <PaginationNav page={page} totalPages={totalPages} onChange={setPage} />
          </>
        )}
      </div>
    </div>
  );
};

const ExplorerAliases = () => {
  const { hasStore, storeUrl, probe, probed } = useUnifiedStore();
  const { metadata, loading, loadStore } = useExplorerStore();

  useEffect(() => {
    const init = async () => {
      if (!probed) await probe();
    };
    init();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (probed && hasStore && storeUrl && !metadata && !loading) {
      loadStore(storeUrl).catch(() => {});
    }
  }, [probed, hasStore, storeUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!probed || loading) {
    return (
      <div>
        <ExplorerNav active="aliases" />
        <div className="text-center py-5">
          <div className="spinner-border" />
        </div>
      </div>
    );
  }

  if (!hasStore) {
    return (
      <div>
        <ExplorerNav active="aliases" />
        <div className="alert alert-info">
          Alias browsing requires a RefgetStore. No store was detected.
        </div>
      </div>
    );
  }

  return (
    <div className="mb-5">
      <ExplorerNav active="aliases" />
      <p className="text-muted">
        Aliases map human-readable names to digests. Select a namespace to browse.
      </p>
      <AliasPanel type="sequences" availableNamespaces={metadata?.sequence_alias_namespaces} />
      <AliasPanel type="collections" availableNamespaces={metadata?.collection_alias_namespaces} />
    </div>
  );
};

export { ExplorerAliases };
