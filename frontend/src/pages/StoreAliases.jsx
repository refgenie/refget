import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore.js';
import { StoreNav } from '../components/StoreNav.jsx';

const AliasNamespacePanel = ({ type, storeUrlParam, availableNamespaces }) => {
  const { loadAliases } = useExplorerStore();
  const [namespace, setNamespace] = useState('');
  const [aliases, setAliases] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('');

  const handleLoad = async (e) => {
    e?.preventDefault();
    if (!namespace.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await loadAliases(type, namespace.trim());
      if (!data) {
        setError(`Namespace "${namespace}" not found.`);
        setAliases(null);
      } else {
        setAliases(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNamespaceClick = (ns) => {
    setNamespace(ns);
    setFilter('');
    setError(null);
    setLoading(true);
    loadAliases(type, ns)
      .then((data) => {
        if (!data) {
          setError(`Namespace "${ns}" not found.`);
          setAliases(null);
        } else {
          setAliases(data);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const filtered = aliases
    ? aliases.filter(
        (a) =>
          !filter ||
          a.alias.toLowerCase().includes(filter.toLowerCase()) ||
          a.digest.toLowerCase().includes(filter.toLowerCase()),
      )
    : null;

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

        {filtered && (
          <>
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span className="text-muted small">
                {filtered.length} aliases in "{namespace}"
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
                  {filtered.map((a, i) => (
                    <tr key={`${a.alias}-${i}`}>
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
