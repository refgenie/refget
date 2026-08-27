import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore';
import { StoreNav } from '../components/StoreNav';
import { PaginationNav } from '../components/PaginationNav';
import { PartialLoadBanner } from '../components/PartialLoadBanner';
import { usePagedList } from '../hooks/usePagedList';
import { Icon } from '../components/common/Icon';
import { errorMessage } from '../utils/errors';
import type { AliasRow, BoundedList } from '../types';
import type { BoundedListOptions } from '../services/storeService';

const aliasFilter = (a: AliasRow, term: string) =>
  a.alias.toLowerCase().includes(term) || a.digest.toLowerCase().includes(term);

interface AliasNamespacePanelProps {
  /** 'sequences' or 'collections'. */
  type: string;
  /** The `?url=...` query string carried between store pages. */
  storeUrlParam: string;
  availableNamespaces?: string[];
}

const AliasNamespacePanel = ({
  type,
  storeUrlParam,
  availableNamespaces,
}: AliasNamespacePanelProps) => {
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

  const linkPrefix =
    type === 'sequences'
      ? null // sequences don't have a detail page in the explorer
      : `/explore-store/collection/`;

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
            <Icon name="info" className="mr-1" />
            No {type} alias namespaces found in this store.
          </p>
        )}

        {error && (
          <div className="alert alert--warning text-sm py-2">{error}</div>
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
  const storeUrlParam = `?url=${encodeURIComponent(storeUrl || urlParam || '')}`;

  useEffect(() => {
    if (urlParam && !metadata && !loading) {
      loadStore(urlParam).catch(() => {});
    }
  }, [urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!metadata && !loading) {
    return (
      <div className="alert alert--warning">
        No store loaded.{' '}
        <Link to="/explore-store">Go back to enter a store URL.</Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="mb-12">
      <StoreNav active="aliases" storeUrlParam={storeUrlParam} />

      <p className="text-muted">
        Aliases map human-readable names to digests. Select a namespace to
        browse its alias mappings.
      </p>

      <AliasNamespacePanel
        type="sequences"
        storeUrlParam={storeUrlParam}
        availableNamespaces={metadata?.sequence_alias_namespaces}
      />
      <AliasNamespacePanel
        type="collections"
        storeUrlParam={storeUrlParam}
        availableNamespaces={metadata?.collection_alias_namespaces}
      />
    </div>
  );
};

export { StoreAliases };
