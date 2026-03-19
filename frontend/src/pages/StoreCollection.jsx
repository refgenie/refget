import { useState, useEffect } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore.js';
import { StoreNav } from '../components/StoreNav.jsx';
import { CliCommand } from '../components/CliSnippet.jsx';

const StoreCollection = () => {
  const { digest } = useParams();
  const [searchParams] = useSearchParams();
  const { storeUrl, metadata, loadStore, loadCollection, loadFhrMetadata, loading } =
    useExplorerStore();
  const [collection, setCollection] = useState(null);
  const [fhr, setFhr] = useState(undefined);
  const [error, setError] = useState(null);
  const [loadingCol, setLoadingCol] = useState(true);
  const [selectedSeq, setSelectedSeq] = useState(null);
  const [seqCodeTab, setSeqCodeTab] = useState('cli');

  const urlParam = searchParams.get('url');
  const storeUrlParam = `?url=${encodeURIComponent(storeUrl || urlParam)}`;

  useEffect(() => {
    const load = async () => {
      try {
        // Ensure store is loaded
        if (!metadata && urlParam) {
          await loadStore(urlParam);
        }
        const col = await loadCollection(digest);
        setCollection(col);
        const fhrData = await loadFhrMetadata(digest);
        setFhr(fhrData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingCol(false);
      }
    };
    load();
  }, [digest, urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!metadata && !loading && !loadingCol) {
    return (
      <div className="alert alert-warning">
        No store loaded.{' '}
        <Link to="/explore-store">Go back to enter a store URL.</Link>
      </div>
    );
  }

  if (loading || loadingCol) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border" />
        <p className="mt-3 text-muted">Loading collection...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <StoreNav active="collections" storeUrlParam={storeUrlParam} />
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  }

  const { metadata: colMeta, sequences } = collection;
  const totalBases = sequences.reduce((sum, s) => sum + s.length, 0);
  const alphabetCounts = {};
  sequences.forEach((s) => {
    alphabetCounts[s.alphabet] = (alphabetCounts[s.alphabet] || 0) + 1;
  });

  return (
    <div className="mb-5">
      <StoreNav active="collections" storeUrlParam={storeUrlParam} collectionDigest={digest} />

      <h5 className="fw-light font-monospace mb-3">{digest}</h5>

      {/* Summary stats */}
      <div className="row g-3 mb-4">
        <div className="col-auto">
          <div className="card">
            <div className="card-body py-2 px-3">
              <small className="text-muted d-block">Sequences</small>
              <strong>{sequences.length.toLocaleString()}</strong>
            </div>
          </div>
        </div>
        <div className="col-auto">
          <div className="card">
            <div className="card-body py-2 px-3">
              <small className="text-muted d-block">Total bases</small>
              <strong>{totalBases.toLocaleString()}</strong>
            </div>
          </div>
        </div>
        {Object.keys(alphabetCounts).length > 0 && (
          <div className="col-auto">
            <div className="card">
              <div className="card-body py-2 px-3">
                <small className="text-muted d-block">Alphabets</small>
                <table className="table table-sm table-borderless mb-0" style={{ minWidth: 0 }}>
                  <tbody>
                    {Object.entries(alphabetCounts).map(([alph, count]) => (
                      <tr key={alph}>
                        <td className="py-0 ps-0 pe-2">{alph}</td>
                        <td className="py-0 ps-0 text-end"><strong>{count.toLocaleString()}</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Collection metadata from ## headers */}
      {Object.keys(colMeta).length > 0 && (
        <div className="card mb-3">
          <div className="card-header">
            <h6 className="mb-0">Collection Metadata</h6>
          </div>
          <div className="card-body">
            <table className="table table-sm mb-0">
              <tbody>
                {Object.entries(colMeta).map(([key, value]) => (
                  <tr key={key}>
                    <td className="text-muted">{key}</td>
                    <td className="font-monospace small">{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* FHR metadata */}
      {fhr ? (
        <div className="card mb-3">
          <div className="card-header">
            <h6 className="mb-0">
              <i className="bi bi-file-earmark-text me-2" />
              FHR Metadata
            </h6>
          </div>
          <div className="card-body">
            <pre className="bg-light p-3 rounded mb-0 small">
              {JSON.stringify(fhr, null, 2)}
            </pre>
          </div>
        </div>
      ) : fhr === null ? (
        <p className="text-muted small">
          <i className="bi bi-info-circle me-1" />
          No FHR metadata sidecar found for this collection.
        </p>
      ) : null}

      {/* Sequence table */}
      <div className="card">
        <div className="card-header">
          <h6 className="mb-0">Sequences in this collection</h6>
        </div>
        <div className="card-body p-0">
          <div className="table-responsive">
            <table className="table table-sm table-hover mb-0">
              <thead>
                <tr>
                  <th>Name</th>
                  <th className="text-end">Length</th>
                  <th>SHA-512/24u</th>
                </tr>
              </thead>
              <tbody>
                {sequences.map((seq, i) => (
                  <tr
                    key={`${seq.sha512t24u}-${i}`}
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedSeq(seq)}
                  >
                    <td>{seq.name}</td>
                    <td className="text-end font-monospace">
                      {seq.length.toLocaleString()}
                    </td>
                    <td className="font-monospace small">{seq.sha512t24u}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Sequence detail modal */}
      {selectedSeq && (
        <>
          <div className="modal-backdrop fade show" onClick={() => setSelectedSeq(null)} />
          <div className="modal fade show d-block" tabIndex="-1" onClick={() => setSelectedSeq(null)}>
            <div className="modal-dialog modal-lg" onClick={(e) => e.stopPropagation()}>
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">{selectedSeq.name}</h5>
                  <button type="button" className="btn-close" onClick={() => setSelectedSeq(null)} />
                </div>
                <div className="modal-body">
                  <table className="table table-sm mb-4">
                    <tbody>
                      <tr>
                        <td className="text-muted">Length</td>
                        <td className="font-monospace">{selectedSeq.length.toLocaleString()}</td>
                      </tr>
                      <tr>
                        <td className="text-muted">Alphabet</td>
                        <td><span className="badge bg-secondary">{selectedSeq.alphabet}</span></td>
                      </tr>
                      <tr>
                        <td className="text-muted">SHA-512/24u</td>
                        <td className="font-monospace small">{selectedSeq.sha512t24u}</td>
                      </tr>
                      <tr>
                        <td className="text-muted">MD5</td>
                        <td className="font-monospace small">{selectedSeq.md5}</td>
                      </tr>
                      {selectedSeq.description && (
                        <tr>
                          <td className="text-muted">Description</td>
                          <td className="small">{selectedSeq.description}</td>
                        </tr>
                      )}
                    </tbody>
                  </table>

                  <h6 className="text-muted mb-2">Code</h6>
                  <ul className="nav nav-pills nav-pills-sm mb-3">
                    <li className="nav-item">
                      <button
                        className={`nav-link py-1 px-2 ${seqCodeTab === 'cli' ? 'active' : ''}`}
                        onClick={() => setSeqCodeTab('cli')}
                      >
                        <i className="bi bi-terminal me-1" />
                        CLI
                      </button>
                    </li>
                    <li className="nav-item">
                      <button
                        className={`nav-link py-1 px-2 ${seqCodeTab === 'python' ? 'active' : ''}`}
                        onClick={() => setSeqCodeTab('python')}
                      >
                        <i className="bi bi-filetype-py me-1" />
                        Python
                      </button>
                    </li>
                  </ul>
                  <small className="text-muted d-block mb-1">Get sequence</small>
                  <CliCommand command={seqCodeTab === 'cli'
                    ? `refget store get --sequence \\
  ${selectedSeq.sha512t24u} \\
  --remote ${storeUrl || urlParam}`
                    : `import refget

store = refget.RefgetStore("${storeUrl || urlParam}")
store.get("${selectedSeq.sha512t24u}", sequence=True)`
                  } />
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export { StoreCollection };
