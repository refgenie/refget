import { useState, useEffect } from 'react';
import { useUnifiedStore } from '../stores/unifiedStore';
import { useExplorerStore } from '../stores/explorerStore';
import { ExplorerNav } from '../components/ExplorerNav';
import { SequenceTable } from '../components/SequenceTable';
import { Icon } from '../components/common/Icon';
import { errorMessage } from '../utils/errors';

const PARTIAL_LOAD_SIZE = 2 * 1024 * 1024;

const formatBytes = (bytes: number) => {
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
  const [seqError, setSeqError] = useState<string | null>(null);

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
      // Lazy-load the sequence index once metadata arrives; this is a
      // load-on-mount data fetch, so the setState is intentional.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSeqLoading(true);
      loadSequenceIndex()
        .catch((err) => setSeqError(errorMessage(err)))
        .finally(() => setSeqLoading(false));
    }
  }, [metadata]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!probed || loading || seqLoading) {
    return (
      <div>
        <ExplorerNav active="sequences" />
        <div className="text-center py-12">
          <div className="spinner" />
          <p className="mt-4 text-muted">Loading sequences...</p>
        </div>
      </div>
    );
  }

  if (!hasStore) {
    return (
      <div>
        <ExplorerNav active="sequences" />
        <div className="alert alert--info">
          Sequence browsing requires a RefgetStore. No store was detected.
        </div>
      </div>
    );
  }

  if (seqError) {
    return (
      <div>
        <ExplorerNav active="sequences" />
        <div className="alert alert--danger">{seqError}</div>
      </div>
    );
  }

  if (!sequenceIndex) {
    return (
      <div>
        <ExplorerNav active="sequences" />
        <div className="alert alert--info">No sequence index found.</div>
      </div>
    );
  }

  const filtered = sequenceIndex.filter((s) => {
    if (!filter) return true;
    const term = filter.toLowerCase();
    return (
      String(s.name ?? '').toLowerCase().includes(term) ||
      String(s.sha512t24u ?? '').toLowerCase().includes(term) ||
      String(s.md5 ?? '').toLowerCase().includes(term) ||
      String(s.description ?? '').toLowerCase().includes(term)
    );
  });

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

  return (
    <div className="mb-12">
      <ExplorerNav active="sequences" />

      {sequenceIndexPartial && (
        <div className="alert alert--warning flex justify-between items-center py-2">
          <span>
            <Icon name="warning" className="mr-2" />
            Showing first {sequenceIndex.length.toLocaleString()} of
            ~{Math.round(sequenceIndex.length * sequenceIndexTotalSize / (PARTIAL_LOAD_SIZE) / 1000).toLocaleString()}k sequences
            (loaded {formatBytes(PARTIAL_LOAD_SIZE)} of {formatBytes(sequenceIndexTotalSize)}).
          </span>
          <button
            className="btn btn--sm btn--warning ml-4"
            onClick={() => handleLoadMore(sequenceIndexTotalSize)}
          >
            Load all ({formatBytes(sequenceIndexTotalSize)})
          </button>
        </div>
      )}

      <div className="flex justify-between items-center mb-4">
        <span className="text-muted">
          {filtered.length.toLocaleString()} sequences
          {filter && ` (filtered from ${sequenceIndex.length.toLocaleString()})`}
        </span>
        <input
          type="search"
          className="form-input form-input--sm filter-input"
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
