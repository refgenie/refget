import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore';
import { StoreNav } from '../components/StoreNav';
import { CliCommand } from '../components/CliSnippet';
import { PaginationNav } from '../components/PaginationNav';
import { PartialLoadBanner } from '../components/PartialLoadBanner';
import { usePagedList } from '../hooks/usePagedList';
import { Icon } from '../components/common/Icon';
import { errorMessage } from '../utils/errors';
import { BaseModal } from '../components/common/BaseModal';
import type { SequenceRow } from '../types';

const seqFilter = (s: SequenceRow, term: string) =>
  String(s.name ?? '').toLowerCase().includes(term) ||
  String(s.sha512t24u ?? '').toLowerCase().includes(term) ||
  String(s.md5 ?? '').toLowerCase().includes(term) ||
  String(s.description ?? '').toLowerCase().includes(term);

const StoreSequences = () => {
  const [searchParams] = useSearchParams();
  const {
    storeUrl, sequenceIndex, sequenceIndexPartial, sequenceIndexTotalSize,
    metadata, loading, loadStore, loadSequenceIndex,
  } = useExplorerStore();
  const [seqLoading, setSeqLoading] = useState(false);
  const [seqError, setSeqError] = useState<string | null>(null);
  const [selectedSeq, setSelectedSeq] = useState<SequenceRow | null>(null);
  const [seqCodeTab, setSeqCodeTab] = useState<'cli' | 'python'>('cli');

  const {
    filter, setFilter, page, setPage,
    sortCol, sortAsc, handleSort, filtered, paged, totalPages,
  } = usePagedList(sequenceIndex, { filterFn: seqFilter });

  const urlParam = searchParams.get('url');
  const storeUrlParam = `?url=${encodeURIComponent(storeUrl || urlParam || '')}`;

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
          setSeqError(errorMessage(err));
        } finally {
          setSeqLoading(false);
        }
      }
    };
    init();
  }, [urlParam, metadata]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleLoadMore = async (maxBytes?: number) => {
    setSeqLoading(true);
    setSeqError(null);
    try {
      await loadSequenceIndex(maxBytes ? { maxBytes } : {});
    } catch (err) {
      setSeqError(errorMessage(err));
    } finally {
      setSeqLoading(false);
    }
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (sortCol !== col) return null;
    return <Icon name={sortAsc ? 'caret-up' : 'caret-down'} className='ml-1' />;
  };

  if (!metadata && !loading) {
    return (
      <div className="alert alert--warning">
        No store loaded.{' '}
        <Link to="/explore-store">Go back to enter a store URL.</Link>
      </div>
    );
  }

  if (loading || seqLoading) {
    return (
      <div className="text-center py-12">
        <div className="spinner" />
        <p className="mt-4 text-muted">
          {seqLoading ? 'Loading sequence index...' : 'Loading store...'}
        </p>
      </div>
    );
  }

  if (seqError) {
    return (
      <div>
        <StoreNav active="sequences" storeUrlParam={storeUrlParam} />
        <div className="alert alert--danger">{seqError}</div>
      </div>
    );
  }

  if (!sequenceIndex) {
    return (
      <div>
        <StoreNav active="sequences" storeUrlParam={storeUrlParam} />
        <div className="alert alert--info">
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
    <div className="mb-12">
      <StoreNav active="sequences" storeUrlParam={storeUrlParam} />

      {/* Partial load banner */}
      {sequenceIndexPartial && (
        <PartialLoadBanner
          totalSize={sequenceIndexTotalSize}
          loadedCount={sequenceIndex.length}
          noun="sequences"
          onLoadAll={() => handleLoadMore(sequenceIndexTotalSize)}
          loading={seqLoading}
        />
      )}

      <div className="flex justify-between items-center mb-4">
        <span className="text-muted">
          {filtered.length.toLocaleString()} sequences
          {filter && ` (filtered from ${sequenceIndex.length.toLocaleString()})`}
          {sequenceIndexPartial && ' (partial)'}
        </span>
        <input
          type="search"
          className="form-input form-input--sm filter-input"
          placeholder="Filter by name, digest, description..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>

      <div className="table-wrap">
        <table className="table table--sm table--hover">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={col.key === 'length' ? 'cursor-pointer text-right' : 'cursor-pointer'}
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
                className="cursor-pointer"
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

      <PaginationNav page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
};

export { StoreSequences };
