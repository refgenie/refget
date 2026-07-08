import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore.js';
import { StoreNav } from '../components/StoreNav.jsx';
import { PaginationNav } from '../components/PaginationNav.jsx';
import { PartialLoadBanner } from '../components/PartialLoadBanner.jsx';
import { usePagedList } from '../hooks/usePagedList.js';

const aliasFilter = (a, term) =>
  a.alias.toLowerCase().includes(term) || a.digest.toLowerCase().includes(term);

const AliasNamespacePanel = ({ type, storeUrlParam, availableNamespaces }) => {
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

  const linkPrefix =
    type === 'sequences'
      ? null // sequences don't have a detail page in the explorer
      : `/explore-store/collection/`;

  return (
    <div className="card mb-3">
      <div className="card-header">
        <h6 className="mb-0 text-capitalize">
          <i
            className={`bi ${type === 'sequences' ? 'bi-list-ol' : 'bi-collection'} me-2`}
          />
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
            <i className="bi bi-info-circle me-1" />
            No {type} alias namespaces found in this store.
          </p>
        )}

        {error && (
          <div className="alert alert-warning small py-2">{error}</div>
        )}

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
                          <Link
                            to={`${linkPrefix}${a.digest}${storeUrlParam}`}
                          >
                            {a.digest}
                          </Link>
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

const StoreAliases = () => {
  const [searchParams] = useSearchParams();
  const { storeUrl, metadata, loading, loadStore } = useExplorerStore();

  const urlParam = searchParams.get('url');
  const storeUrlParam = `?url=${encodeURIComponent(storeUrl || urlParam)}`;

  useEffect(() => {
    if (urlParam && !metadata && !loading) {
      loadStore(urlParam).catch(() => {});
    }
  }, [urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!metadata && !loading) {
    return (
      <div className="alert alert-warning">
        No store loaded.{' '}
        <Link to="/explore-store">Go back to enter a store URL.</Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border" />
      </div>
    );
  }

  return (
    <div className="mb-5">
      <StoreNav active="aliases" storeUrlParam={storeUrlParam} />

      <p className="text-muted">
        Aliases map human-readable names to digests. Select a namespace to
        browse its alias mappings.
      </p>

      <AliasNamespacePanel type="sequences" storeUrlParam={storeUrlParam} availableNamespaces={metadata.sequence_alias_namespaces} />
      <AliasNamespacePanel type="collections" storeUrlParam={storeUrlParam} availableNamespaces={metadata.collection_alias_namespaces} />
    </div>
  );
};

export { StoreAliases };
