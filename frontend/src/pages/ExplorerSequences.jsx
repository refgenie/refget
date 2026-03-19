import { useState, useMemo, useEffect } from 'react';
import { useUnifiedStore } from '../stores/unifiedStore.js';
import { useExplorerStore } from '../stores/explorerStore.js';
import { ExplorerNav } from '../components/ExplorerNav.jsx';
import { SequenceTable } from '../components/SequenceTable.jsx';

const PARTIAL_LOAD_SIZE = 2 * 1024 * 1024;

const formatBytes = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const ExplorerSequences = () => {
  const { hasStore, storeUrl, probe, probed } = useUnifiedStore();
  const {
    metadata, sequenceIndex, sequenceIndexPartial, sequenceIndexTotalSize,
    loading, loadStore, loadSequenceIndex,
  } = useExplorerStore();
  const [filter, setFilter] = useState('');
  const [seqLoading, setSeqLoading] = useState(false);
  const [seqError, setSeqError] = useState(null);

  useEffect(() => {
    const init = async () => {
      if (!probed) await probe();
    };
    init();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (probed && hasStore && storeUrl && !metadata && !loading) {
      loadStore(storeUrl).catch(() => {});
    }
  }, [probed, hasStore, storeUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (metadata && !sequenceIndex && !seqLoading) {
      setSeqLoading(true);
      loadSequenceIndex()
        .catch((err) => setSeqError(err.message))
        .finally(() => setSeqLoading(false));
    }
  }, [metadata]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!probed || loading || seqLoading) {
    return (
      <div>
        <ExplorerNav active="sequences" />
        <div className="text-center py-5">
          <div className="spinner-border" />
          <p className="mt-3 text-muted">Loading sequences...</p>
        </div>
      </div>
    );
  }

  if (!hasStore) {
    return (
      <div>
        <ExplorerNav active="sequences" />
        <div className="alert alert-info">
          Sequence browsing requires a RefgetStore. No store was detected.
        </div>
      </div>
    );
  }

  if (seqError) {
    return (
      <div>
        <ExplorerNav active="sequences" />
        <div className="alert alert-danger">{seqError}</div>
      </div>
    );
  }

  if (!sequenceIndex) {
    return (
      <div>
        <ExplorerNav active="sequences" />
        <div className="alert alert-info">No sequence index found.</div>
      </div>
    );
  }

  const filtered = sequenceIndex.filter((s) => {
    if (!filter) return true;
    const term = filter.toLowerCase();
    return (
      s.name?.toLowerCase().includes(term) ||
      s.sha512t24u?.toLowerCase().includes(term) ||
      s.md5?.toLowerCase().includes(term) ||
      s.description?.toLowerCase().includes(term)
    );
  });

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

  return (
    <div className="mb-5">
      <ExplorerNav active="sequences" />

      {sequenceIndexPartial && (
        <div className="alert alert-warning d-flex justify-content-between align-items-center py-2">
          <span>
            <i className="bi bi-exclamation-triangle me-2" />
            Showing first {sequenceIndex.length.toLocaleString()} of
            ~{Math.round(sequenceIndex.length * sequenceIndexTotalSize / (PARTIAL_LOAD_SIZE) / 1000).toLocaleString()}k sequences
            (loaded {formatBytes(PARTIAL_LOAD_SIZE)} of {formatBytes(sequenceIndexTotalSize)}).
          </span>
          <button
            className="btn btn-sm btn-warning ms-3"
            onClick={() => handleLoadMore(sequenceIndexTotalSize)}
          >
            Load all ({formatBytes(sequenceIndexTotalSize)})
          </button>
        </div>
      )}

      <div className="d-flex justify-content-between align-items-center mb-3">
        <span className="text-muted">
          {filtered.length.toLocaleString()} sequences
          {filter && ` (filtered from ${sequenceIndex.length.toLocaleString()})`}
        </span>
        <input
          type="search"
          className="form-control form-control-sm"
          style={{ maxWidth: '300px' }}
          placeholder="Filter by name, digest..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>

      <SequenceTable sequences={filtered} storeUrl={storeUrl} sortable />
    </div>
  );
};

export { ExplorerSequences };
