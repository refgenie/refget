import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useUnifiedStore } from '../stores/unifiedStore.js';
import { useExplorerStore } from '../stores/explorerStore.js';
import { ExplorerNav } from '../components/ExplorerNav.jsx';
import { useState } from 'react';

const AliasPanel = ({ type, availableNamespaces }) => {
  const { loadAliases } = useExplorerStore();
  const [namespace, setNamespace] = useState('');
  const [aliases, setAliases] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('');

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

        {filtered && (
          <>
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span className="text-muted small">{filtered.length} aliases in "{namespace}"</span>
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
