import { useState, useEffect } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore';
import { StoreNav } from '../components/StoreNav';
import { CliCommand } from '../components/CliSnippet';
import { Icon } from '../components/common/Icon';
import { errorMessage } from '../utils/errors';
import { BaseModal } from '../components/common/BaseModal';
import type { CollectionDetail, SequenceRow } from '../types';

const StoreCollection = () => {
  const { digest } = useParams();
  const [searchParams] = useSearchParams();
  const { storeUrl, metadata, loadStore, loadCollection, loadFhrMetadata, loading } =
    useExplorerStore();
  const [collection, setCollection] = useState<CollectionDetail | null>(null);
  const [fhr, setFhr] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingCol, setLoadingCol] = useState(true);
  const [selectedSeq, setSelectedSeq] = useState<SequenceRow | null>(null);
  const [seqCodeTab, setSeqCodeTab] = useState<'cli' | 'python'>('cli');

  const urlParam = searchParams.get('url');
  const storeUrlParam = `?url=${encodeURIComponent(storeUrl || urlParam || '')}`;

  useEffect(() => {
    const load = async () => {
      try {
        // Ensure store is loaded
        if (!metadata && urlParam) {
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
          <div className="table-wrap">
            <table className="table table--sm table--hover mb-0">
              <thead>
                <tr>
                  <th>Name</th>
                  <th className="text-right">Length</th>
                  <th>SHA-512/24u</th>
                </tr>
              </thead>
              <tbody>
                {sequences.map((seq: SequenceRow, i: number) => (
                  <tr
                    key={`${seq.sha512t24u}-${i}`}
                    className="table__row--clickable"
                    onClick={() => setSelectedSeq(seq)}
                  >
                    <td>{seq.name}</td>
                    <td className="text-right font-mono">
                      {seq.length.toLocaleString()}
                    </td>
                    <td className="font-mono text-sm">{seq.sha512t24u}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Sequence detail modal */}
      {selectedSeq && (
        <BaseModal
          isOpen
          onClose={() => setSelectedSeq(null)}
          title={selectedSeq.name ?? 'Sequence'}
          size="lg"
        >
          <table className="table table--sm mb-6">
            <tbody>
              <tr>
                <td className="text-muted">Length</td>
                <td className="font-mono">{selectedSeq.length.toLocaleString()}</td>
              </tr>
              <tr>
                <td className="text-muted">Alphabet</td>
                <td><span className="badge badge--secondary">{selectedSeq.alphabet}</span></td>
              </tr>
              <tr>
                <td className="text-muted">SHA-512/24u</td>
                <td className="font-mono text-sm">{selectedSeq.sha512t24u}</td>
              </tr>
              <tr>
                <td className="text-muted">MD5</td>
                <td className="font-mono text-sm">{selectedSeq.md5}</td>
              </tr>
              {selectedSeq.description && (
                <tr>
                  <td className="text-muted">Description</td>
                  <td className="text-sm">{selectedSeq.description}</td>
                </tr>
              )}
            </tbody>
          </table>

          <h6 className="text-muted mb-2">Code</h6>
          <ul className="tabs tabs--pills mb-4">
            <li>
              <button
                className={`tab ${seqCodeTab === 'cli' ? 'tab--active' : ''}`}
                onClick={() => setSeqCodeTab('cli')}
              >
                <Icon name="terminal" className="mr-1" />
                CLI
              </button>
            </li>
            <li>
              <button
                className={`tab ${seqCodeTab === 'python' ? 'tab--active' : ''}`}
                onClick={() => setSeqCodeTab('python')}
              >
                <Icon name="python" className="mr-1" />
                Python
              </button>
            </li>
          </ul>
          <small className="text-muted block mb-1">Get sequence</small>
          <CliCommand command={seqCodeTab === 'cli'
            ? `refget store get --sequence \\
    ${selectedSeq.sha512t24u} \\
    --remote ${storeUrl || urlParam}`
            : `import refget

  store = refget.RefgetStore("${storeUrl || urlParam}")
  store.get("${selectedSeq.sha512t24u}", sequence=True)`
          } />
        </BaseModal>
      )}
    </div>
  );
};

export { StoreCollection };
