import { useState, useEffect, useMemo } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore';
import { StoreNav } from '../components/StoreNav';
import { SequenceTable } from '../components/SequenceTable';
import { Icon } from '../components/common/Icon';
import { errorMessage } from '../utils/errors';
import { buildCollectionAliasMap, preferredAlias } from '../services/aliases';
import type { CollectionAliasMap, CollectionDetail } from '../types';

/** How many same-coordinate collections to list before summarizing the rest. */
const MAX_RELATED = 20;

const StoreCollection = () => {
  const { digest } = useParams();
  const [searchParams] = useSearchParams();
  const {
    storeUrl,
    metadata,
    collections,
    loadStore,
    loadCollection,
    loadFhrMetadata,
    loadAliases,
    loading,
  } = useExplorerStore();
  const [collection, setCollection] = useState<CollectionDetail | null>(null);
  const [fhr, setFhr] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingCol, setLoadingCol] = useState(true);
  const [aliasMap, setAliasMap] = useState<CollectionAliasMap>({});

  const urlParam = searchParams.get('url');
  const storeUrlParam = `?url=${encodeURIComponent(storeUrl || urlParam || '')}`;

  useEffect(() => {
    const load = async () => {
      try {
        // Load the store named in the URL unless it is the one already loaded;
        // a different store may be loaded from earlier in the session.
        if (urlParam && (urlParam !== storeUrl || !metadata)) {
          await loadStore(urlParam);
        }
        const col = await loadCollection(digest ?? '');
        setCollection(col);
        const fhrData = await loadFhrMetadata(digest ?? '');
        setFhr(fhrData);
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoadingCol(false);
      }
    };
    load();
  }, [digest, urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  // Collections in this store with the same coordinate system: the same
  // sequence names and lengths in any order. The store index already carries
  // each collection's sorted_name_length_pairs digest, so no server is needed.
  const related = useMemo(() => {
    const snlp = collections?.find((c) => c.digest === digest)?.sorted_name_length_pairs_digest;
    if (!snlp || !collections) return [];
    return collections.filter(
      (c) => c.sorted_name_length_pairs_digest === snlp && c.digest !== digest,
    );
  }, [collections, digest]);

  // Label related collections with their aliases, loaded only when there are any.
  useEffect(() => {
    const namespaces = metadata?.collection_alias_namespaces || [];
    if (related.length === 0 || namespaces.length === 0) return;
    let cancelled = false;
    buildCollectionAliasMap(namespaces, loadAliases)
      .then((map) => { if (!cancelled) setAliasMap(map); })
      .catch(() => { /* aliases are optional; the list renders without them */ });
    return () => { cancelled = true; };
  }, [metadata, related.length]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!metadata && !loading && !loadingCol) {
    return (
      <div className="alert alert--warning">
        No store loaded.{' '}
        <Link to="/explore-store">Go back to enter a store URL.</Link>
      </div>
    );
  }

  if (loading || loadingCol) {
    return (
      <div className="text-center py-12">
        <div className="spinner" />
        <p className="mt-4 text-muted">Loading collection...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <StoreNav active="collections" storeUrlParam={storeUrlParam} />
        <div className="alert alert--danger">{error}</div>
      </div>
    );
  }

  if (!collection) {
    return (
      <div>
        <StoreNav active="collections" storeUrlParam={storeUrlParam} />
        <div className="alert alert--warning">Collection not found.</div>
      </div>
    );
  }

  const { metadata: colMeta, sequences } = collection;
  const totalBases = sequences.reduce((sum, s) => sum + s.length, 0);
  const alphabetCounts: Record<string, number> = {};
  sequences.forEach((s) => {
    const alphabet = s.alphabet ?? 'unknown';
    alphabetCounts[alphabet] = (alphabetCounts[alphabet] || 0) + 1;
  });

  return (
    <div className="mb-12">
      <StoreNav active="collections" storeUrlParam={storeUrlParam} collectionDigest={digest} />

      <h5 className="font-light font-mono mb-4">{digest}</h5>

      {/* Summary stats */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div>
          <div className="card">
            <div className="card__body py-2 px-4">
              <small className="text-muted block">Sequences</small>
              <strong>{sequences.length.toLocaleString()}</strong>
            </div>
          </div>
        </div>
        <div>
          <div className="card">
            <div className="card__body py-2 px-4">
              <small className="text-muted block">Total bases</small>
              <strong>{totalBases.toLocaleString()}</strong>
            </div>
          </div>
        </div>
        {Object.keys(alphabetCounts).length > 0 && (
          <div>
            <div className="card">
              <div className="card__body py-2 px-4">
                <small className="text-muted block">Alphabets</small>
                <table className="table table--sm table--borderless mb-0 min-w-0">
                  <tbody>
                    {Object.entries(alphabetCounts).map(([alph, count]) => (
                      <tr key={alph}>
                        <td className="py-0 pl-0 pr-2">{alph}</td>
                        <td className="py-0 pl-0 text-right"><strong>{count.toLocaleString()}</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Related collections, from the store index */}
      {related.length > 0 && (
        <div className="card mb-4">
          <div className="card__header">
            <h6 className="mb-0">
              <Icon name="diagram" className="mr-2" />
              Same coordinate system ({related.length.toLocaleString()})
            </h6>
          </div>
          <div className="card__body">
            <p className="text-muted text-sm mb-2">
              Other collections in this store with the same sequence names and lengths, in any
              order (the same <code>sorted_name_length_pairs</code> digest). Their sequences may
              still differ.
            </p>
            <ul className="mb-0">
              {related.slice(0, MAX_RELATED).map((c) => {
                const { primary } = preferredAlias(aliasMap[c.digest]);
                return (
                  <li key={c.digest}>
                    <Link
                      to={`/explore-store/collection/${c.digest}${storeUrlParam}`}
                      className="font-mono text-sm"
                    >
                      {c.digest}
                    </Link>
                    {primary && <span className="text-muted text-sm ml-2">{primary}</span>}
                  </li>
                );
              })}
              {related.length > MAX_RELATED && (
                <li className="text-muted">
                  and {(related.length - MAX_RELATED).toLocaleString()} more
                </li>
              )}
            </ul>
          </div>
        </div>
      )}

      {/* Collection metadata from ## headers */}
      {Object.keys(colMeta).length > 0 && (
        <div className="card mb-4">
          <div className="card__header">
            <h6 className="mb-0">Collection Metadata</h6>
          </div>
          <div className="card__body">
            <table className="table table--sm mb-0">
              <tbody>
                {Object.entries(colMeta).map(([key, value]) => (
                  <tr key={key}>
                    <td className="text-muted">{key}</td>
                    <td className="font-mono text-sm">{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* FHR metadata */}
      {fhr ? (
        <div className="card mb-4">
          <div className="card__header">
            <h6 className="mb-0">
              <Icon name="file-text" className="mr-2" />
              FHR Metadata
            </h6>
          </div>
          <div className="card__body">
            <pre className="bg-surface-muted p-4 rounded mb-0 text-sm">
              {JSON.stringify(fhr, null, 2)}
            </pre>
          </div>
        </div>
      ) : fhr === null ? (
        <p className="text-muted text-sm">
          <Icon name="info" className="mr-1" />
          No FHR metadata sidecar found for this collection.
        </p>
      ) : null}

      {/* Sequence table */}
      <div className="card">
        <div className="card__header">
          <h6 className="mb-0">Sequences in this collection</h6>
        </div>
        <div className="card__body p-0">
          <SequenceTable sequences={sequences} storeUrl={storeUrl || urlParam} sortable />
        </div>
      </div>
    </div>
  );
};

export { StoreCollection };
