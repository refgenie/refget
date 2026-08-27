import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useUnifiedStore } from '../stores/unifiedStore';
import { useExplorerStore } from '../stores/explorerStore';
import { ExplorerNav } from '../components/ExplorerNav';
import { CliCommand } from '../components/CliSnippet';
import { SequenceTable } from '../components/SequenceTable';
import { fetchCollectionLevels, fetchAttribute } from '../services/fetchData';
import {
  LinkedAttributeDigest,
} from '../components/ValuesAndDigests';
import { Icon } from '../components/common/Icon';
import { errorMessage } from '../utils/errors';
import type { CollectionDetail, SeqColLevel1, SeqColLevel2, SequenceRow } from '../types';

const ExplorerCollection = () => {
  const { digest } = useParams();
  const { hasStore, hasAPI, storeUrl, apiUrl, probe, probed } = useUnifiedStore();
  const { loadCollection, loadFhrMetadata, loadStore, metadata } = useExplorerStore();

  const [storeData, setStoreData] = useState<CollectionDetail | null>(null);
  const [apiData, setApiData] =
    useState<[SeqColLevel1, SeqColLevel2, SeqColLevel2] | null>(null);
  const [fhr, setFhr] = useState<Record<string, unknown> | null>(null);
  const [relatedCollections, setRelatedCollections] = useState<string[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState(false);
  const [codeTab, setCodeTab] = useState('cli');

  // Ensure probe runs first
  useEffect(() => {
    if (!probed) {
      probe();
    }
  }, [probed, probe]);

  useEffect(() => {
    if (!probed) return; // Wait for probe to complete

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        // Load store data
        if (hasStore && storeUrl) {
          if (!metadata) {
            await loadStore(storeUrl).catch(() => {});
          }
          const col = await loadCollection(digest ?? '').catch(() => null);
          setStoreData(col);
          const fhrData = await loadFhrMetadata(digest ?? '').catch(() => null);
          setFhr(fhrData);
        }

        // Load API data
        if (hasAPI && apiUrl) {
          const levels = await fetchCollectionLevels(digest ?? '', apiUrl).catch(() => null);
          setApiData(levels);

          // Fetch related collections via sorted_name_length_pairs
          if (levels && levels[0]?.sorted_name_length_pairs) {
            const snlp = levels[0].sorted_name_length_pairs;
            try {
              const related = await fetchAttribute('sorted_name_length_pairs', snlp, apiUrl);
              setRelatedCollections(
                related[0]?.results?.filter((d: string) => d !== digest) || [],
              );
            } catch { /* related collections are optional; ignore failures */ }
          }
        }
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [digest, probed, hasStore, hasAPI, storeUrl, apiUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div>
        <ExplorerNav active="collections" />
        <div className="text-center py-12">
          <div className="spinner" />
          <p className="mt-4 text-muted">Loading collection...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <ExplorerNav active="collections" />
        <div className="alert alert--danger">{error}</div>
      </div>
    );
  }

  if (!storeData && !apiData) {
    return (
      <div>
        <ExplorerNav active="collections" />
        <div className="alert alert--warning">
          Collection <code>{digest}</code> not found.
        </div>
      </div>
    );
  }

  const sequences = storeData?.sequences || [];
  const totalBases = sequences.reduce((sum: number, s: SequenceRow) => sum + s.length, 0);
  const alphabetCounts: Record<string, number> = {};
  sequences.forEach((s: SequenceRow) => {
    const alphabet = s.alphabet ?? 'unknown';
    alphabetCounts[alphabet] = (alphabetCounts[alphabet] || 0) + 1;
  });

  const level1 = apiData?.[0];
  const level2 = apiData?.[1];
  const uncollated = apiData?.[2];

  return (
    <div className="mb-12">
      <ExplorerNav active="" />

      <nav aria-label="breadcrumb" className="mb-4">
        <ol className="breadcrumb">
          <li className="breadcrumb__item"><Link to="/collections">Collections</Link></li>
          <li className="breadcrumb__item breadcrumb__item--current font-mono text-sm" aria-current="page">{digest}</li>
        </ol>
      </nav>

      {/* Summary stats (from store) */}
      {storeData && (
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
                  {Object.entries(alphabetCounts).map(([alph, count]) => (
                    <span key={alph} className="badge badge--secondary mr-1">
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
        <div className="card mb-6">
          <div className="card__header">
            <h6 className="mb-0">
              <Icon name="diagram" className="mr-2" />
              Related collections (same coordinate system)
            </h6>
          </div>
          <div className="card__body">
            <p className="text-muted text-sm mb-2">
              Collections sharing the same <code>sorted_name_length_pairs</code> digest:
            </p>
            <ul className="mb-0">
              {relatedCollections.slice(0, 10).map((d) => (
                <li key={d}>
                  <Link to={`/collection/${d}`} className="font-mono text-sm">
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
        <div className="mb-6">
          <Link to={`/compare`} className="btn btn--outline-primary btn--sm">
            <Icon name="collapse" className="mr-1" />
            Compare this collection
          </Link>
        </div>
      )}

      {/* FHR metadata */}
      {fhr && (
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
      )}

      {/* Sequence table (from store) */}
      {sequences.length > 0 && (
        <div className="card mb-6">
          <div className="card__header">
            <h6 className="mb-0">Sequences ({sequences.length.toLocaleString()})</h6>
          </div>
          <div className="card__body p-0">
            <SequenceTable sequences={sequences} storeUrl={storeUrl} />
          </div>
        </div>
      )}

      {/* Attribute digests (from API) */}
      {level2 && (
        <div className="card mb-6">
          <div className="card__header">
            <h6 className="mb-0">Attribute Digests</h6>
          </div>
          <div className="card__body">
            {Object.keys(level2).map((attribute) => (
              <div key={attribute} className="mb-4">
                <h6 className="mb-1 font-medium">{attribute}</h6>
                <div className="kv">
                  <div className="kv__term text-muted text-sm">Digest:</div>
                  <div className="kv__value">
                    <LinkedAttributeDigest
                      attribute={attribute}
                      digest={level1?.[attribute] ?? ''}
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
        <div className="card mb-6">
          <div className="card__header">
            <button
              className="btn btn--link no-underline p-0 text-strong"
              onClick={() => setShowRaw(!showRaw)}
            >
              <Icon name={showRaw ? 'chevron-down' : 'chevron-right'} className='mr-2' />
              <h6 className="mb-0 inline">Technical Details</h6>
            </button>
          </div>
          {showRaw && (
            <div className="card__body">
              {[
                { label: 'Level 1', data: level1, query: '?level=1' },
                { label: 'Level 2', data: level2, query: '?level=2' },
                { label: 'Uncollated', data: uncollated, query: '?collated=false' },
              ].map(({ label, data, query }) => (
                <div key={label} className="mb-4">
                  <div className="flex justify-between items-center mb-1">
                    <strong className="text-sm">{label}: /collection/{digest}{query}</strong>
                    {apiUrl && (
                      <a
                        className="btn btn--sm btn--outline-secondary"
                        href={`${apiUrl}/collection/${digest}${query}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Icon name="external" className="mr-1" />
                        API
                      </a>
                    )}
                  </div>
                  <pre className="bg-surface-muted p-4 rounded text-sm mb-0">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </div>
              ))}

              {/* CLI/Python snippets */}
              {hasStore && storeUrl && (
                <div className="mt-6">
                  <h6 className="text-muted mb-2">Code</h6>
                  <ul className="tabs tabs--pills mb-4">
                    <li>
                      <button
                        className={`tab ${codeTab === 'cli' ? 'tab--active' : ''}`}
                        onClick={() => setCodeTab('cli')}
                      >
                        CLI
                      </button>
                    </li>
                    <li>
                      <button
                        className={`tab ${codeTab === 'python' ? 'tab--active' : ''}`}
                        onClick={() => setCodeTab('python')}
                      >
                        Python
                      </button>
                    </li>
                  </ul>
                  <small className="text-muted block mb-1">Pull collection</small>
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
