import { useState, useMemo, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore.js';
import { StoreNav } from '../components/StoreNav.jsx';
import { CliCommand } from '../components/CliSnippet.jsx';

const PAGE_SIZE = 50;

const formatBytes = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const StoreSequences = () => {
  const [searchParams] = useSearchParams();
  const {
    storeUrl, sequenceIndex, sequenceIndexPartial, sequenceIndexTotalSize,
    metadata, loading, loadStore, loadSequenceIndex,
  } = useExplorerStore();
  const [filter, setFilter] = useState('');
  const [sortCol, setSortCol] = useState(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [page, setPage] = useState(0);
  const [seqLoading, setSeqLoading] = useState(false);
  const [seqError, setSeqError] = useState(null);
  const [selectedSeq, setSelectedSeq] = useState(null);
  const [seqCodeTab, setSeqCodeTab] = useState('cli');

  const urlParam = searchParams.get('url');
  const storeUrlParam = `?url=${encodeURIComponent(storeUrl || urlParam)}`;

  // Auto-load on mount — fetchSequenceIndex handles the size check internally
  useEffect(() => {
    const init = async () => {
      if (urlParam && !metadata && !loading) {
        await loadStore(urlParam).catch(() => {});
      }
      if (!sequenceIndex && !seqLoading) {
        setSeqLoading(true);
        try {
          await loadSequenceIndex();
        } catch (err) {
          setSeqError(err.message);
        } finally {
          setSeqLoading(false);
        }
      }
    };
    init();
  }, [urlParam, metadata]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleLoadMore = async (maxBytes) => {
    setSeqLoading(true);
    setSeqError(null);
    try {
      await loadSequenceIndex(maxBytes ? { maxBytes } : {});
    } catch (err) {
      setSeqError(err.message);
    } finally {
      setSeqLoading(false);
    }
  };

  const filtered = useMemo(() => {
    if (!sequenceIndex) return [];
    const term = filter.toLowerCase();
    return sequenceIndex.filter(
      (s) =>
        !term ||
        s.name?.toLowerCase().includes(term) ||
        s.sha512t24u?.toLowerCase().includes(term) ||
        s.md5?.toLowerCase().includes(term) ||
        s.description?.toLowerCase().includes(term),
    );
  }, [sequenceIndex, filter]);

  const sorted = useMemo(() => {
    if (!sortCol) return filtered;
    return [...filtered].sort((a, b) => {
      const va = a[sortCol];
      const vb = b[sortCol];
      if (typeof va === 'number' && typeof vb === 'number') {
        return sortAsc ? va - vb : vb - va;
      }
      return sortAsc
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va));
    });
  }, [filtered, sortCol, sortAsc]);

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const paged = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const handleSort = (col) => {
    if (sortCol === col) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(col);
      setSortAsc(true);
    }
    setPage(0);
  };

  const SortIcon = ({ col }) => {
    if (sortCol !== col) return null;
    return <i className={`bi bi-caret-${sortAsc ? 'up' : 'down'}-fill ms-1`} />;
  };

  if (!metadata && !loading) {
    return (
      <div className="alert alert-warning">
        No store loaded.{' '}
        <Link to="/explore-store">Go back to enter a store URL.</Link>
      </div>
    );
  }

  if (loading || seqLoading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border" />
        <p className="mt-3 text-muted">
          {seqLoading ? 'Loading sequence index...' : 'Loading store...'}
        </p>
      </div>
    );
  }

  if (seqError) {
    return (
      <div>
        <StoreNav active="sequences" storeUrlParam={storeUrlParam} />
        <div className="alert alert-danger">{seqError}</div>
      </div>
    );
  }

  if (!sequenceIndex) {
    return (
      <div>
        <StoreNav active="sequences" storeUrlParam={storeUrlParam} />
        <div className="alert alert-info">
          No sequence index (sequences.rgsi) found in this store.
        </div>
      </div>
    );
  }

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'length', label: 'Length' },
    { key: 'sha512t24u', label: 'SHA-512/24u' },
  ];

  return (
    <div className="mb-5">
      <StoreNav active="sequences" storeUrlParam={storeUrlParam} />

      {/* Partial load banner */}
      {sequenceIndexPartial && (
        <div className="alert alert-warning d-flex justify-content-between align-items-center py-2">
          <span>
            <i className="bi bi-exclamation-triangle me-2" />
            Sequence index is {formatBytes(sequenceIndexTotalSize)} — showing first{' '}
            {sequenceIndex.length.toLocaleString()} sequences.
            Sorting and filtering apply only to loaded data.
          </span>
          <button
            className="btn btn-sm btn-warning ms-3"
            onClick={() => handleLoadMore(sequenceIndexTotalSize)}
            disabled={seqLoading}
          >
            Load all ({formatBytes(sequenceIndexTotalSize)})
          </button>
        </div>
      )}

      <div className="d-flex justify-content-between align-items-center mb-3">
        <span className="text-muted">
          {filtered.length.toLocaleString()} sequences
          {filter && ` (filtered from ${sequenceIndex.length.toLocaleString()})`}
          {sequenceIndexPartial && ' (partial)'}
        </span>
        <input
          type="search"
          className="form-control form-control-sm"
          style={{ maxWidth: '300px' }}
          placeholder="Filter by name, digest, description..."
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value);
            setPage(0);
          }}
        />
      </div>

      <div className="table-responsive">
        <table className="table table-sm table-hover">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  style={{ cursor: 'pointer' }}
                  className={col.key === 'length' ? 'text-end' : ''}
                >
                  {col.label}
                  <SortIcon col={col.key} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.map((seq, i) => (
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

      {totalPages > 1 && (
        <nav>
          <ul className="pagination pagination-sm justify-content-center">
            <li className={`page-item ${page === 0 ? 'disabled' : ''}`}>
              <button className="page-link" onClick={() => setPage(page - 1)}>
                Previous
              </button>
            </li>
            <li className="page-item disabled">
              <span className="page-link">
                Page {page + 1} of {totalPages}
              </span>
            </li>
            <li
              className={`page-item ${page >= totalPages - 1 ? 'disabled' : ''}`}
            >
              <button className="page-link" onClick={() => setPage(page + 1)}>
                Next
              </button>
            </li>
          </ul>
        </nav>
      )}
    </div>
  );
};

export { StoreSequences };
