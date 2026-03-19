import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useUnifiedStore } from '../stores/unifiedStore.js';
import { useExplorerStore } from '../stores/explorerStore.js';
import { ExplorerNav } from '../components/ExplorerNav.jsx';
import { CliCommand } from '../components/CliSnippet.jsx';
import { SequenceTable } from '../components/SequenceTable.jsx';
import { fetchCollectionLevels, fetchAttribute } from '../services/fetchData.jsx';
import { CopyableDigest } from '../components/CopyableDigest.jsx';
import {
  AttributeValue,
  LinkedAttributeDigest,
} from '../components/ValuesAndDigests.jsx';

const ExplorerCollection = () => {
  const { digest } = useParams();
  const { hasStore, hasAPI, storeUrl, apiUrl } = useUnifiedStore();
  const { loadCollection, loadFhrMetadata, loadStore, metadata } = useExplorerStore();

  const [storeData, setStoreData] = useState(null);
  const [apiData, setApiData] = useState(null);
  const [fhr, setFhr] = useState(undefined);
  const [relatedCollections, setRelatedCollections] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showRaw, setShowRaw] = useState(false);
  const [codeTab, setCodeTab] = useState('cli');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        // Load store data
        if (hasStore && storeUrl) {
          if (!metadata) {
            await loadStore(storeUrl).catch(() => {});
          }
          const col = await loadCollection(digest).catch(() => null);
          setStoreData(col);
          const fhrData = await loadFhrMetadata(digest).catch(() => null);
          setFhr(fhrData);
        }

        // Load API data
        if (hasAPI && apiUrl) {
          const levels = await fetchCollectionLevels(digest, apiUrl).catch(() => null);
          setApiData(levels);

          // Fetch related collections via sorted_name_length_pairs
          if (levels && levels[0]?.sorted_name_length_pairs) {
            const snlp = levels[0].sorted_name_length_pairs;
            try {
              const related = await fetchAttribute('sorted_name_length_pairs', snlp, apiUrl);
              setRelatedCollections(related[0]?.results?.filter((d) => d !== digest) || []);
            } catch {}
          }
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [digest]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div>
        <ExplorerNav active="collections" />
        <div className="text-center py-5">
          <div className="spinner-border" />
          <p className="mt-3 text-muted">Loading collection...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <ExplorerNav active="collections" />
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  }

  if (!storeData && !apiData) {
    return (
      <div>
        <ExplorerNav active="collections" />
        <div className="alert alert-warning">
          Collection <code>{digest}</code> not found.
        </div>
      </div>
    );
  }

  const sequences = storeData?.sequences || [];
  const totalBases = sequences.reduce((sum, s) => sum + s.length, 0);
  const alphabetCounts = {};
  sequences.forEach((s) => {
    alphabetCounts[s.alphabet] = (alphabetCounts[s.alphabet] || 0) + 1;
  });

  const level1 = apiData?.[0];
  const level2 = apiData?.[1];
  const uncollated = apiData?.[2];

  return (
    <div className="mb-5">
      <ExplorerNav active="" />

      <nav aria-label="breadcrumb" className="mb-3">
        <ol className="breadcrumb">
          <li className="breadcrumb-item"><Link to="/collections">Collections</Link></li>
          <li className="breadcrumb-item active font-monospace small" aria-current="page">{digest}</li>
        </ol>
      </nav>

      {/* Summary stats (from store) */}
      {storeData && (
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
                  {Object.entries(alphabetCounts).map(([alph, count]) => (
                    <span key={alph} className="badge bg-secondary me-1">
                      {alph}: {count}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Related collections (from API) */}
      {relatedCollections && relatedCollections.length > 0 && (
        <div className="card mb-4">
          <div className="card-header">
            <h6 className="mb-0">
              <i className="bi bi-diagram-3 me-2" />
              Related collections (same coordinate system)
            </h6>
          </div>
          <div className="card-body">
            <p className="text-muted small mb-2">
              Collections sharing the same <code>sorted_name_length_pairs</code> digest:
            </p>
            <ul className="mb-0">
              {relatedCollections.slice(0, 10).map((d) => (
                <li key={d}>
                  <Link to={`/collection/${d}`} className="font-monospace small">
                    {d}
                  </Link>
                </li>
              ))}
              {relatedCollections.length > 10 && (
                <li className="text-muted">
                  ...and {relatedCollections.length - 10} more
                </li>
              )}
            </ul>
          </div>
        </div>
      )}

      {/* Compare button */}
      {hasAPI && (
        <div className="mb-4">
          <Link to={`/compare`} className="btn btn-outline-primary btn-sm">
            <i className="bi bi-arrows-angle-contract me-1" />
            Compare this collection
          </Link>
        </div>
      )}

      {/* FHR metadata */}
      {fhr && (
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
      )}

      {/* Sequence table (from store) */}
      {sequences.length > 0 && (
        <div className="card mb-4">
          <div className="card-header">
            <h6 className="mb-0">Sequences ({sequences.length.toLocaleString()})</h6>
          </div>
          <div className="card-body p-0">
            <SequenceTable sequences={sequences} storeUrl={storeUrl} />
          </div>
        </div>
      )}

      {/* Attribute digests (from API) */}
      {level2 && (
        <div className="card mb-4">
          <div className="card-header">
            <h6 className="mb-0">Attribute Digests</h6>
          </div>
          <div className="card-body">
            {Object.keys(level2).map((attribute) => (
              <div key={attribute} className="mb-3">
                <h6 className="mb-1 fw-medium">{attribute}</h6>
                <div className="row align-items-center">
                  <div className="col-md-1 text-muted small">Digest:</div>
                  <div className="col">
                    <LinkedAttributeDigest
                      attribute={attribute}
                      digest={level1[attribute]}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Collapsible Technical Details */}
      {apiData && (
        <div className="card mb-4">
          <div className="card-header">
            <button
              className="btn btn-link text-decoration-none p-0 text-black"
              onClick={() => setShowRaw(!showRaw)}
            >
              <i className={`bi bi-chevron-${showRaw ? 'down' : 'right'} me-2`} />
              <h6 className="mb-0 d-inline">Technical Details</h6>
            </button>
          </div>
          {showRaw && (
            <div className="card-body">
              {[
                { label: 'Level 1', data: level1, query: '?level=1' },
                { label: 'Level 2', data: level2, query: '?level=2' },
                { label: 'Uncollated', data: uncollated, query: '?collated=false' },
              ].map(({ label, data, query }) => (
                <div key={label} className="mb-3">
                  <div className="d-flex justify-content-between align-items-center mb-1">
                    <strong className="small">{label}: /collection/{digest}{query}</strong>
                    {apiUrl && (
                      <a
                        className="btn btn-sm btn-outline-secondary"
                        href={`${apiUrl}/collection/${digest}${query}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <i className="bi bi-box-arrow-up-right me-1" />
                        API
                      </a>
                    )}
                  </div>
                  <pre className="bg-light p-3 rounded small mb-0">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </div>
              ))}

              {/* CLI/Python snippets */}
              {hasStore && storeUrl && (
                <div className="mt-4">
                  <h6 className="text-muted mb-2">Code</h6>
                  <ul className="nav nav-pills nav-pills-sm mb-3">
                    <li className="nav-item">
                      <button
                        className={`nav-link py-1 px-2 ${codeTab === 'cli' ? 'active' : ''}`}
                        onClick={() => setCodeTab('cli')}
                      >
                        CLI
                      </button>
                    </li>
                    <li className="nav-item">
                      <button
                        className={`nav-link py-1 px-2 ${codeTab === 'python' ? 'active' : ''}`}
                        onClick={() => setCodeTab('python')}
                      >
                        Python
                      </button>
                    </li>
                  </ul>
                  <small className="text-muted d-block mb-1">Pull collection</small>
                  <CliCommand
                    command={
                      codeTab === 'cli'
                        ? `refget store pull \\\n  ${digest} \\\n  --remote ${storeUrl}`
                        : `import refget\n\nstore = refget.RefgetStore("${storeUrl}")\nstore.pull("${digest}")`
                    }
                  />
                </div>
              )}
            </div>
          )}
        </div>
      )}

    </div>
  );
};

export { ExplorerCollection };
