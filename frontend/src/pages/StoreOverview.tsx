import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore';
import { StoreNav } from '../components/StoreNav';
import { RowCodeButton } from '../components/CliSnippet';
import { PaginationNav } from '../components/PaginationNav';
import { usePagedList } from '../hooks/usePagedList';
import { buildCollectionAliasMap, preferredAlias } from '../services/aliases';
import { Icon } from '../components/common/Icon';
import type { CollectionAliasMap } from '../types';

const StoreOverview = () => {
  const [searchParams] = useSearchParams();
  const {
    storeUrl,
    metadata,
    sequenceIndex,
    collections,
    loading,
    error,
    loadStore,
    loadSequenceIndex,
    loadAliases,
  } = useExplorerStore();
  const [seqLoading, setSeqLoading] = useState(false);
  const [aliasMap, setAliasMap] = useState<CollectionAliasMap>({});

  const urlParam = searchParams.get('url');

  // Load the store whenever the URL param differs from the currently loaded
  // store. Guarding on storeUrl (not metadata) ensures navigating between
  // stores — e.g. jungle -> pangenome — actually reloads instead of showing
  // the previously loaded store. loadStore sets storeUrl synchronously, so
  // this settles after one load without re-triggering.
  useEffect(() => {
    const init = async () => {
      if (urlParam && urlParam !== storeUrl && !loading) {
        await loadStore(urlParam).catch(() => {});
      }
    };
    init();
  }, [urlParam, storeUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-load sequence index (fetchSequenceIndex handles size check internally)
  useEffect(() => {
    if (metadata && !sequenceIndex && !seqLoading) {
      // Lazy-load the sequence index once metadata arrives; this is a
      // load-on-mount data fetch, so the setState is intentional.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSeqLoading(true);
      loadSequenceIndex()
        .catch(() => {})
        .finally(() => setSeqLoading(false));
    }
  }, [metadata]); // eslint-disable-line react-hooks/exhaustive-deps

  // Collections have no name of their own, so the label column is populated
  // from the store's collection-alias namespaces. Guarded against races when
  // switching stores: a slow load must not overwrite a newer one.
  useEffect(() => {
    const namespaces = metadata?.collection_alias_namespaces || [];
    if (namespaces.length === 0) return;
    let cancelled = false;
    buildCollectionAliasMap(namespaces, loadAliases)
      .then((map) => { if (!cancelled) setAliasMap(map); })
      .catch(() => { /* aliases are optional; the table renders without them */ });
    return () => { cancelled = true; };
  }, [metadata]); // eslint-disable-line react-hooks/exhaustive-deps

  // Paginate the collections table so large collection indexes don't render
  // thousands of rows in a single pass.
  const {
    paged: pagedCollections,
    page: collectionsPage,
    setPage: setCollectionsPage,
    totalPages: collectionsTotalPages,
  } = usePagedList(collections, { pageSize: 50 });

  // loadStore records the failure on the store before rethrowing (the effect's
  // catch only stops an unhandled rejection), so report the real cause rather
  // than implying no URL was given.
  if (!metadata && !loading && error) {
    return (
      <div className="alert alert--danger">
        <strong>Could not load this store.</strong>
        <div className="text-sm mt-1">{error}</div>
        {urlParam && (
          <div className="text-sm mt-1">
            URL: <code>{urlParam}</code>
          </div>
        )}
        <div className="text-sm mt-2">
          A store must serve <code>rgstore.json</code> and allow cross-origin reads.{' '}
          <Link to="/explore-store">Try a different store URL.</Link>
        </div>
      </div>
    );
  }

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
        <p className="mt-4 text-muted">Loading store...</p>
      </div>
    );
  }

  const totalBases = sequenceIndex
    ? sequenceIndex.reduce((sum, s) => sum + s.length, 0)
    : 0;

  const alphabetCounts: Record<string, number> = {};
  if (sequenceIndex) {
    sequenceIndex.forEach((s) => {
      const alphabet = s.alphabet ?? 'unknown';
      alphabetCounts[alphabet] = (alphabetCounts[alphabet] || 0) + 1;
    });
  }

  const storeUrlParam = `?url=${encodeURIComponent(storeUrl || urlParam || '')}`;

  return (
    <div className="mb-12">
      <StoreNav active="overview" storeUrlParam={storeUrlParam} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Store info card */}
        <div>
          <div className="card h-full">
            <div className="card__header">
              <h6 className="mb-0">
                <Icon name="info" className="mr-2" />
                Store Info
              </h6>
            </div>
            <div className="card__body">
              <table className="table table--sm mb-0">
                <tbody>
                  <tr>
                    <td className="text-muted">URL</td>
                    <td className="font-mono text-sm text-break">
                      {storeUrl || urlParam}
                    </td>
                  </tr>
                  <tr>
                    <td className="text-muted">Version</td>
                    <td>{metadata?.version}</td>
                  </tr>
                  <tr>
                    <td className="text-muted">Storage Mode</td>
                    <td>
                      <span
                        className={`badge ${metadata?.mode === 'Raw' ? 'badge--success' : 'badge--primary'}`}
                      >
                        {metadata?.mode}
                      </span>
                    </td>
                  </tr>
                  {typeof metadata?.created_at === 'string' && (
                    <tr>
                      <td className="text-muted">Created</td>
                      <td>{new Date(metadata.created_at).toLocaleString()}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Sequences summary card */}
        <div>
          <div className="card h-full">
            <div className="card__header flex justify-between items-center">
              <h6 className="mb-0">
                <Icon name="list-ol" className="mr-2" />
                Sequences
              </h6>
              <Link
                to={`/explore-store/sequences${storeUrlParam}`}
                className="btn btn--sm btn--outline-primary"
              >
                Browse all
              </Link>
            </div>
            <div className="card__body">
              {sequenceIndex ? (
                <table className="table table--sm mb-0">
                  <tbody>
                    <tr>
                      <td className="text-muted">Total sequences</td>
                      <td>{sequenceIndex.length.toLocaleString()}</td>
                    </tr>
                    <tr>
                      <td className="text-muted">Total bases</td>
                      <td>{totalBases.toLocaleString()}</td>
                    </tr>
                    <tr>
                      <td className="text-muted">Alphabets</td>
                      <td>
                        {Object.entries(alphabetCounts).map(([alph, count]) => (
                          <span
                            key={alph}
                            className="badge badge--secondary mr-1"
                          >
                            {alph}: {count}
                          </span>
                        ))}
                      </td>
                    </tr>
                  </tbody>
                </table>
              ) : seqLoading ? (
                <div className="text-center py-2">
                  <span className="spinner spinner--sm mr-2" />
                  Loading sequence index...
                </div>
              ) : (
                <p className="text-muted mb-0 text-sm">
                  Sequence index not available.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Collections */}
      <div className="card mb-4">
        <div className="card__header flex justify-between items-center">
          <h6 className="mb-0">
            <Icon name="collection" className="mr-2" />
            Collections{collections?.length ? ` (${collections.length.toLocaleString()})` : ''}
          </h6>
        </div>
        <div className="card__body">
          {collections && collections.length > 0 ? (
            <div className="table-wrap">
              <table className="table table--sm table--hover mb-0">
                <thead>
                  <tr>
                    <th>Alias</th>
                    <th>Digest</th>
                    <th className="text-right">Sequences</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {pagedCollections.map((col) => {
                    const { primary, all } = preferredAlias(aliasMap[col.digest]);
                    return (
                    <tr key={col.digest}>
                      <td>
                        {primary
                          ? <span title={all.length > 1 ? all.join('\n') : undefined}>{primary}</span>
                          : <span className="text-muted">-</span>}
                      </td>
                      <td>
                        <Link
                          to={`/explore-store/collection/${col.digest}${storeUrlParam}`}
                          className="font-mono text-sm"
                        >
                          {col.digest}
                        </Link>
                      </td>
                      <td className="text-right">{col.n_sequences}</td>
                      <td className="text-right">
                        <RowCodeButton
                          title="Collection commands"
                          snippets={[
                            {
                              label: 'Pull to local cache',
                              cli: `refget store pull \\
  ${col.digest} \\
  --remote ${storeUrl || urlParam}`,
                              python: `import refget

store = refget.RefgetStore("${storeUrl || urlParam}")
store.pull("${col.digest}")`,
                            },
                            {
                              label: 'Export as FASTA',
                              cli: `refget store export \\
  ${col.digest} \\
  --remote ${storeUrl || urlParam}`,
                              python: `import refget

store = refget.RefgetStore("${storeUrl || urlParam}")
store.export("${col.digest}")`,
                            },
                          ]}
                        />
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
              <PaginationNav
                page={collectionsPage}
                totalPages={collectionsTotalPages}
                onChange={setCollectionsPage}
              />
            </div>
          ) : (
            <p className="text-muted mb-0">
              No collection index (collections.rgci) found. Individual
              collections can still be viewed if you know the digest.
            </p>
          )}
        </div>
      </div>

      {/* Aliases section */}
      <div className="card mb-4">
        <div className="card__header flex justify-between items-center">
          <h6 className="mb-0">
            <Icon name="tag" className="mr-2" />
            Aliases
          </h6>
          <Link
            to={`/explore-store/aliases${storeUrlParam}`}
            className="btn btn--sm btn--outline-primary"
          >
            Browse aliases
          </Link>
        </div>
        <div className="card__body">
          {((metadata?.sequence_alias_namespaces?.length ?? 0) > 0 || (metadata?.collection_alias_namespaces?.length ?? 0) > 0) ? (
            <table className="table table--sm mb-0">
              <tbody>
                {(metadata?.sequence_alias_namespaces?.length ?? 0) > 0 && (
                  <tr>
                    <td className="text-muted">Sequence namespaces</td>
                    <td>
                      {(metadata?.sequence_alias_namespaces ?? []).map((ns) => (
                        <Link
                          key={ns}
                          to={`/explore-store/aliases${storeUrlParam}`}
                          className="badge badge--secondary mr-1 no-underline"
                        >
                          {ns}
                        </Link>
                      ))}
                    </td>
                  </tr>
                )}
                {(metadata?.collection_alias_namespaces?.length ?? 0) > 0 && (
                  <tr>
                    <td className="text-muted">Collection namespaces</td>
                    <td>
                      {(metadata?.collection_alias_namespaces ?? []).map((ns) => (
                        <Link
                          key={ns}
                          to={`/explore-store/aliases${storeUrlParam}`}
                          className="badge badge--secondary mr-1 no-underline"
                        >
                          {ns}
                        </Link>
                      ))}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          ) : (
            <p className="text-muted mb-0">
              No alias namespace information available.
            </p>
          )}
        </div>
      </div>

    </div>
  );
};

export { StoreOverview };
