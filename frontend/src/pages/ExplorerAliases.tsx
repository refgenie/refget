import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useUnifiedStore } from '../stores/unifiedStore';
import { useExplorerStore } from '../stores/explorerStore';
import { ExplorerNav } from '../components/ExplorerNav';
import { PaginationNav } from '../components/PaginationNav';
import { PartialLoadBanner } from '../components/PartialLoadBanner';
import { usePagedList } from '../hooks/usePagedList';
import { Icon } from '../components/common/Icon';
import { errorMessage } from '../utils/errors';
import type { AliasRow, BoundedList } from '../types';
import type { BoundedListOptions } from '../services/storeService';

const aliasFilter = (a: AliasRow, term: string) =>
  a.alias.toLowerCase().includes(term) || a.digest.toLowerCase().includes(term);

interface AliasPanelProps {
  /** 'sequences' or 'collections'. */
  type: string;
  availableNamespaces?: string[];
}

const AliasPanel = ({ type, availableNamespaces }: AliasPanelProps) => {
  const { loadAliases } = useExplorerStore();
  const [namespace, setNamespace] = useState('');
  const [aliasData, setAliasData] = useState<BoundedList<AliasRow> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { filter, setFilter, page, setPage, paged, filtered, totalPages } =
    usePagedList(aliasData?.rows, { filterFn: aliasFilter });

  const loadNamespace = (ns: string, options?: BoundedListOptions) => {
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
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  };

  const handleNamespaceClick = (ns: string) => {
    setNamespace(ns);
    setFilter('');
    loadNamespace(ns);
  };

  const linkPrefix = type === 'collections' ? '/collection/' : null;

  return (
    <div className="card mb-4">
      <div className="card__header">
        <h6 className="mb-0 capitalize">
          <Icon name={type === 'sequences' ? 'list-ol' : 'collection'} className='mr-2' />
          {type} aliases
        </h6>
      </div>
      <div className="card__body">
        {availableNamespaces && availableNamespaces.length > 0 ? (
          <div className="mb-4">
            <span className="text-muted text-sm mr-2">Namespaces:</span>
            {availableNamespaces.map((ns: string) => (
              <button
                key={ns}
                className={`btn btn--sm mr-1 mb-1 ${namespace === ns ? 'btn--primary' : 'btn--outline-primary'}`}
                onClick={() => handleNamespaceClick(ns)}
                disabled={loading}
              >
                {ns}
              </button>
            ))}
            {loading && <span className="spinner spinner--sm ml-2" />}
          </div>
        ) : (
          <p className="text-muted text-sm mb-0">
            No {type} alias namespaces found.
          </p>
        )}

        {error && <div className="alert alert--warning text-sm py-2">{error}</div>}

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
            <div className="flex justify-between items-center mb-2">
              <span className="text-muted text-sm">
                {filtered.length.toLocaleString()} aliases in &quot;{namespace}&quot;
                {aliasData.partial && ' (partial)'}
              </span>
              <input
                type="search"
                className="form-input form-input--sm filter-input filter-input--narrow"
                placeholder="Filter..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </div>
            <div className="table-wrap table-wrap--scroll">
              <table className="table table--sm table--hover mb-0">
                <thead className="sticky bg-surface">
                  <tr>
                    <th>Alias</th>
                    <th>Digest</th>
                  </tr>
                </thead>
                <tbody>
                  {paged.map((a) => (
                    <tr key={`${a.alias}-${a.digest}`}>
                      <td>{a.alias}</td>
                      <td className="font-mono text-sm">
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
        <div className="text-center py-12">
          <div className="spinner" />
        </div>
      </div>
    );
  }

  if (!hasStore) {
    return (
      <div>
        <ExplorerNav active="aliases" />
        <div className="alert alert--info">
          Alias browsing requires a RefgetStore. No store was detected.
        </div>
      </div>
    );
  }

  return (
    <div className="mb-12">
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
