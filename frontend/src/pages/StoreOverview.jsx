import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore.js';
import { StoreNav } from '../components/StoreNav.jsx';
import { RowCodeButton } from '../components/CliSnippet.jsx';

const StoreOverview = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { storeUrl, metadata, sequenceIndex, collections, loading, loadStore, loadSequenceIndex } =
    useExplorerStore();
  const [seqLoading, setSeqLoading] = useState(false);

  const urlParam = searchParams.get('url');

  // If we have a URL param but no loaded store, load it
  useEffect(() => {
    const init = async () => {
      if (urlParam && !metadata && !loading) {
        await loadStore(urlParam).catch(() => {});
      }
    };
    init();
  }, [urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-load sequence index (fetchSequenceIndex handles size check internally)
  useEffect(() => {
    if (metadata && !sequenceIndex && !seqLoading) {
      setSeqLoading(true);
      loadSequenceIndex()
        .catch(() => {})
        .finally(() => setSeqLoading(false));
    }
  }, [metadata]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!metadata && !loading) {
    return (
      <div className="alert alert-warning">
        No store loaded.{' '}
        <Link to="/explore">Go back to enter a store URL.</Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border" />
        <p className="mt-3 text-muted">Loading store...</p>
      </div>
    );
  }

  const totalBases = sequenceIndex
    ? sequenceIndex.reduce((sum, s) => sum + s.length, 0)
    : 0;

  const alphabetCounts = {};
  if (sequenceIndex) {
    sequenceIndex.forEach((s) => {
      alphabetCounts[s.alphabet] = (alphabetCounts[s.alphabet] || 0) + 1;
    });
  }

  const storeUrlParam = `?url=${encodeURIComponent(storeUrl || urlParam)}`;

  return (
    <div className="mb-5">
      <StoreNav active="overview" storeUrlParam={storeUrlParam} />

      <div className="row g-3 mb-4">
        {/* Store info card */}
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header">
              <h6 className="mb-0">
                <i className="bi bi-info-circle me-2" />
                Store Info
              </h6>
            </div>
            <div className="card-body">
              <table className="table table-sm mb-0">
                <tbody>
                  <tr>
                    <td className="text-muted">URL</td>
                    <td className="font-monospace small text-break">
                      {storeUrl || urlParam}
                    </td>
                  </tr>
                  <tr>
                    <td className="text-muted">Version</td>
                    <td>{metadata.version}</td>
                  </tr>
                  <tr>
                    <td className="text-muted">Storage Mode</td>
                    <td>
                      <span
                        className={`badge ${metadata.mode === 'Raw' ? 'bg-success' : 'bg-primary'}`}
                      >
                        {metadata.mode}
                      </span>
                    </td>
                  </tr>
                  {metadata.created_at && (
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
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h6 className="mb-0">
                <i className="bi bi-list-ol me-2" />
                Sequences
              </h6>
              <Link
                to={`/explore/store/sequences${storeUrlParam}`}
                className="btn btn-sm btn-outline-primary"
              >
                Browse all
              </Link>
            </div>
            <div className="card-body">
              {sequenceIndex ? (
                <table className="table table-sm mb-0">
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
                            className="badge bg-secondary me-1"
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
                  <span className="spinner-border spinner-border-sm me-2" />
                  Loading sequence index...
                </div>
              ) : (
                <p className="text-muted mb-0 small">
                  Sequence index not available.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Collections */}
      <div className="card mb-3">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h6 className="mb-0">
            <i className="bi bi-collection me-2" />
            Collections
          </h6>
        </div>
        <div className="card-body">
          {collections && collections.length > 0 ? (
            <div className="table-responsive">
              <table className="table table-sm table-hover mb-0">
                <thead>
                  <tr>
                    <th>Digest</th>
                    <th className="text-end">Sequences</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {collections.map((col) => (
                    <tr key={col.digest}>
                      <td>
                        <Link
                          to={`/explore/store/collection/${col.digest}${storeUrlParam}`}
                          className="font-monospace small"
                        >
                          {col.digest}
                        </Link>
                      </td>
                      <td className="text-end">{col.n_sequences}</td>
                      <td className="text-end">
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
                  ))}
                </tbody>
              </table>
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
      <div className="card mb-3">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h6 className="mb-0">
            <i className="bi bi-tag me-2" />
            Aliases
          </h6>
          <Link
            to={`/explore/store/aliases${storeUrlParam}`}
            className="btn btn-sm btn-outline-primary"
          >
            Browse aliases
          </Link>
        </div>
        <div className="card-body">
          {(metadata.sequence_alias_namespaces?.length > 0 || metadata.collection_alias_namespaces?.length > 0) ? (
            <table className="table table-sm mb-0">
              <tbody>
                {metadata.sequence_alias_namespaces?.length > 0 && (
                  <tr>
                    <td className="text-muted">Sequence namespaces</td>
                    <td>
                      {metadata.sequence_alias_namespaces.map((ns) => (
                        <Link
                          key={ns}
                          to={`/explore/store/aliases${storeUrlParam}`}
                          className="badge bg-secondary me-1 text-decoration-none"
                        >
                          {ns}
                        </Link>
                      ))}
                    </td>
                  </tr>
                )}
                {metadata.collection_alias_namespaces?.length > 0 && (
                  <tr>
                    <td className="text-muted">Collection namespaces</td>
                    <td>
                      {metadata.collection_alias_namespaces.map((ns) => (
                        <Link
                          key={ns}
                          to={`/explore/store/aliases${storeUrlParam}`}
                          className="badge bg-secondary me-1 text-decoration-none"
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
