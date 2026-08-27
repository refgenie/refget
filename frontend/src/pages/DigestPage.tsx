import type { CSSProperties } from 'react';
import { useState, useRef, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import FastaDropzone from '../components/digest/FastaDropzone';
import SeqColResult from '../components/digest/SeqColResult';
import { Icon } from '../components/common/Icon';
import type { SeqColDigestResult, SequenceRow } from '../types';

const HISTORY_KEY = 'digest-history';
const MAX_HISTORY = 20;

/** One entry in the local digest history list. */
interface HistoryEntry {
  digest: string;
  fileName: string | null;
  n_sequences: number;
  timestamp: number;
}

/** Progress reported by the streaming worker. */
interface DigestProgress {
  bytesProcessed: number;
  totalSize: number;
  percent: number;
}

/** Timing/throughput counters the worker sends with its result. */
interface DigestStats {
  chunks: number;
  totalBytes: number;
  elapsedMs: number;
  avgChunkSize: number;
}

/**
 * The worker that hashes one file. `fileName` rides along on the instance so
 * the result handler knows which upload it belongs to.
 */
type DigestWorker = Worker & { fileName?: string };

// Get history list from localStorage
function getHistory(): HistoryEntry[] {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
  } catch {
    return [];
  }
}

// Save result and update history
function saveToHistory(result: SeqColDigestResult, fileName: string | null) {
  const key = result.digest;

  // Save full result
  localStorage.setItem(`digest-${key}`, JSON.stringify({ result, fileName }));

  // Update history index
  let history = getHistory();
  // Remove if already exists (we'll re-add at top)
  history = history.filter((h) => h.digest !== key);
  // Add to front
  history.unshift({
    digest: key,
    fileName,
    n_sequences: result.n_sequences,
    timestamp: Date.now()
  });
  // Trim to max
  if (history.length > MAX_HISTORY) {
    const removed = history.splice(MAX_HISTORY);
    // Clean up old entries
    removed.forEach((h) => localStorage.removeItem(`digest-${h.digest}`));
  }
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

// Load result from localStorage
function loadFromHistory(digest: string) {
  try {
    const stored = localStorage.getItem(`digest-${digest}`);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function createWorker(): DigestWorker {
  return new Worker(
    new URL('../components/digest/fastaDigestWorker.ts', import.meta.url),
    { type: 'module' }
  );
}

export function DigestPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [result, setResult] = useState<SeqColDigestResult | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<DigestProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [stats, setStats] = useState<DigestStats | null>(null);
  const workerRef = useRef<DigestWorker | null>(null);

  // Load history on mount: initializing state from an external source
  // (localStorage) is the intended use of an effect here.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setHistory(getHistory());
  }, []);

  // Restore state from URL on mount or when URL changes (back/forward)
  useEffect(() => {
    const key = searchParams.get('id');
    if (key) {
      const stored = loadFromHistory(key);
      if (stored) {
        // Restoring state from the URL/history is intentional synchronization
        // with an external source on navigation.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setResult(stored.result);
        setFileName(stored.fileName);
      }
    } else {
      setResult(null);
      setFileName(null);
    }
  }, [searchParams]);

  const setupWorker = useCallback(() => {
    // Terminate existing worker if any
    if (workerRef.current) {
      workerRef.current.terminate();
    }

    const worker = createWorker();

    worker.onmessage = (e: MessageEvent) => {
      const { type, result, message, bytesProcessed, totalSize, percent, stats: workerStats } = e.data;

      if (type === 'status') {
        setStatus(message);
      } else if (type === 'progress') {
        setProgress({ bytesProcessed, totalSize, percent });
      } else if (type === 'result') {
        setResult(result);
        setStatus(null);
        setProgress(null);
        if (workerStats) {
          setStats(workerStats);
          if (import.meta.env.DEV) {
            console.log('[FASTA Digest]', {
              chunks: workerStats.chunks,
              avgChunkSize: `${(workerStats.avgChunkSize / 1024).toFixed(1)} KB`,
              elapsed: `${(workerStats.elapsedMs / 1000).toFixed(1)}s`,
              throughput: `${(workerStats.totalBytes / workerStats.elapsedMs / 1024).toFixed(1)} MB/s`
            });
          }
        }
        // Save to localStorage
        const name = worker.fileName ?? null;
        saveToHistory(result, name);
        setHistory(getHistory());
        // Update URL
        window.history.pushState({}, '', `${window.location.pathname}?id=${result.digest}`);
        toast.success(`Computed digest for ${result.n_sequences} sequences`);
      } else if (type === 'error') {
        setError(message);
        setStatus(null);
        setProgress(null);
        toast.error(message);
      } else if (type === 'cancelled') {
        setStatus(null);
        setProgress(null);
        setError('Processing cancelled.');
      }
    };

    worker.onerror = (event: ErrorEvent) => {
      event.preventDefault();
      setError(event.message || 'Worker crashed unexpectedly');
      setStatus(null);
      setProgress(null);
    };

    workerRef.current = worker;
    return worker;
  }, []);

  // Initialize worker on mount
  useEffect(() => {
    setupWorker();
    return () => workerRef.current?.terminate();
  }, [setupWorker]);

  const handleFileSelected = (file: File) => {
    // Cancel and replace any running worker to prevent double-processing
    const worker = setupWorker();
    setFileName(file.name);
    setResult(null);
    setError(null);
    setProgress(null);
    setStats(null);
    setStatus('Starting...');
    worker.fileName = file.name;
    worker.postMessage({ file });
  };

  const handleCancel = () => {
    if (workerRef.current) {
      workerRef.current.terminate();
      workerRef.current = null;
    }
    setStatus(null);
    setProgress(null);
    setError('Processing cancelled.');
  };

  const handleClear = () => {
    setError(null);
    setStatus(null);
    setProgress(null);
    setStats(null);
  };

  const handleHistoryClick = (digest: string) => {
    navigate(`/fasta?id=${digest}`);
  };

  const clearHistory = () => {
    history.forEach((h) => localStorage.removeItem(`digest-${h.digest}`));
    localStorage.removeItem(HISTORY_KEY);
    setHistory([]);
    toast.success('History cleared');
  };

  const isProcessing = status !== null;

  const formatSize = (bytes: number) => {
    if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
    if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
    if (bytes >= 1e3) return `${(bytes / 1e3).toFixed(1)} KB`;
    return `${bytes} bytes`;
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  // Generate RGSI file content from result
  const generateRgsi = (result: SeqColDigestResult) => {
    const lines = [
      `##seqcol_digest=${result.digest}`,
      `##names_digest=${result.names_digest}`,
      `##sequences_digest=${result.sequences_digest}`,
      `##lengths_digest=${result.lengths_digest}`,
      '#name\tlength\talphabet\tsha512t24u\tmd5\tdescription',
      ...result.sequences.map((seq: SequenceRow) =>
        `${seq.name}\t${seq.length}\t${seq.alphabet}\t${seq.sha512t24u}\t${seq.md5 || ''}\t${seq.description || ''}`
      )
    ];
    return lines.join('\n') + '\n';
  };

  // Convert result to level 1 seqcol format (digests only)
  const resultToSeqcolLevel1 = (result: SeqColDigestResult) => ({
    lengths: result.lengths_digest,
    names: result.names_digest,
    sequences: result.sequences_digest,
    // Note: sorted_sequences and name_length_pairs digests not computed by WASM
  });

  // Convert result to level 2 seqcol format (arrays)
  const resultToSeqcolLevel2 = (result: SeqColDigestResult) => {
    // Build sequences array - check if sha512t24u already has SQ. prefix
    const sequences = result.sequences.map((s: SequenceRow) => {
      const digest = s.sha512t24u ?? '';
      return digest.startsWith('SQ.') ? digest : `SQ.${digest}`;
    });

    const level2 = {
      lengths: result.sequences.map((s: SequenceRow) => Math.floor(s.length)), // ensure integers
      names: result.sequences.map((s: SequenceRow) => s.name),
      sequences: sequences,
      sorted_sequences: [...sequences].sort(),
      name_length_pairs: result.sequences.map((s: SequenceRow) => ({
        length: Math.floor(s.length),
        name: s.name
      }))
    };

    return level2;
  };

  // Convert result to uncollated format (record per sequence)
  const resultToSeqcolUncollated = (result: SeqColDigestResult) =>
    result.sequences.map((s: SequenceRow) => ({
      name: s.name,
      length: s.length,
      sequence: s.sha512t24u?.startsWith('SQ.') ? s.sha512t24u : `SQ.${s.sha512t24u}`
    }));

  // Navigate to SCOM with this collection pre-loaded
  const handleCompareInScom = () => {
    if (!result) return;
    const level2 = resultToSeqcolLevel2(result);
    localStorage.setItem('scom-prefill', JSON.stringify({
      json: level2,
      name: fileName
    }));
    navigate('/scom?prefill=true');
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    toast.success('Copied JSON');
  };

  const handleDownloadJson = (format: 'level1' | 'level2' | 'uncollated') => {
    if (!result) return;
    let data;
    let suffix;
    switch (format) {
      case 'level1':
        data = resultToSeqcolLevel1(result);
        suffix = 'level1';
        break;
      case 'level2':
        data = resultToSeqcolLevel2(result);
        suffix = 'level2';
        break;
      case 'uncollated':
        data = resultToSeqcolUncollated(result);
        suffix = 'uncollated';
        break;
      default:
        data = resultToSeqcolLevel2(result);
        suffix = 'level2';
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${fileName}.seqcol.${suffix}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadRgsi = () => {
    if (!result || !fileName) return;
    const blob = new Blob([generateRgsi(result)], { type: 'text/tab-separated-values' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${fileName.replace(/\.(fa|fasta|fna)(\.gz)?$/i, '')}.rgsi`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="py-6">
      <h2 className="mb-4">
        <Icon name="fingerprint" className="mr-2" />
        Compute Refget Sequence Collection Digest from FASTA file
      </h2>

      <p className="text-muted">
        Compute the refget sequence collection digest for a FASTA file.
        <strong> All processing happens in your browser</strong>—no data is uploaded.
        Supports files of any size through streaming. Uses the rust-based <a
          href="https://crates.io/crates/gtars"
          target="_blank"
          rel="noopener noreferrer"
        >
          gtars crate
        </a> exported via the <a
          href="https://www.npmjs.com/package/@databio/gtars"
          target="_blank"
          rel="noopener noreferrer"
        >
          gtars-js wasm package
        </a>.
      </p>

      <FastaDropzone
        onFileSelected={handleFileSelected}
        disabled={isProcessing}
      />

      {/* Status and Progress */}
      {isProcessing && (
        <div className="mt-4">
          <div className="flex items-center mb-2">
            <div className="spinner spinner--sm mr-2"></div>
            <span>{status}</span>
            <button
              className="btn btn--sm btn--outline-danger ml-4"
              onClick={handleCancel}
            >
              Cancel
            </button>
          </div>

          {progress && (
            <>
              <div className="progress progress--lg">
                <div
                  className="progress__bar progress__bar--striped"
                  role="progressbar"
                  style={{ '--progress-value': `${progress.percent}%` } as CSSProperties}
                  aria-valuenow={progress.percent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  {progress.percent}%
                </div>
              </div>
              <small className="text-muted">
                {formatSize(progress.bytesProcessed)} / {formatSize(progress.totalSize)}
              </small>
            </>
          )}
        </div>
      )}

      {/* Error or Cancelled */}
      {error && (
        <div className={`alert ${error === 'Processing cancelled.' ? 'alert--warning' : 'alert--danger'} mt-4 flex justify-between items-center`}>
          <div>
            <Icon name={error === 'Processing cancelled.' ? 'x-circle' : 'warning'} className='mr-2' />
            {error}
          </div>
          <button
            className="btn btn--sm btn--outline-secondary"
            onClick={handleClear}
          >
            Clear
          </button>
        </div>
      )}

      {/* Results */}
      <SeqColResult
        result={result}
        fileName={fileName}
        onCompare={handleCompareInScom}
        onCopyJson={handleCopyJson}
        onDownloadJson={handleDownloadJson}
        onDownloadRgsi={handleDownloadRgsi}
      />

      {/* Processing Stats (collapsed) */}
      {stats && result && (
        <details className="mt-4">
          <summary className="text-muted cursor-pointer">
            <small>Processing details</small>
          </summary>
          <div className="mt-2 text-sm text-muted">
            <div>Chunks processed: {stats.chunks.toLocaleString()}</div>
            <div>Average chunk size: {(stats.avgChunkSize / 1024).toFixed(1)} KB</div>
            <div>Elapsed time: {(stats.elapsedMs / 1000).toFixed(1)}s</div>
            <div>Throughput: {(stats.totalBytes / stats.elapsedMs / 1024).toFixed(1)} MB/s</div>
          </div>
        </details>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="mt-12">
          <div className="flex justify-between items-center mb-2">
            <h5 className="text-muted mb-0">
              <Icon name="clock" className="mr-2" />
              Recent Digests
            </h5>
            <button
              className="btn btn--sm btn--outline-secondary"
              onClick={clearHistory}
            >
              Clear history
            </button>
          </div>
          <div className="list-group">
            {history.map((item) => {
              const isSelected = result?.digest === item.digest;
              return (
                <button
                  key={item.digest}
                  className={`list-group__item list-group__item--action flex justify-between items-center ${
 isSelected ? 'bg-light border-primary' : ''
 }`}
                  onClick={() => handleHistoryClick(item.digest)}
                >
                  <div>
                    <div className="font-medium">{item.fileName}</div>
                    <small className={isSelected ? 'text-primary-fg' : 'text-muted'}>
                      <code>{item.digest}</code>
                      <span className="ml-2">({item.n_sequences} sequences)</span>
                    </small>
                  </div>
                  <small className="text-muted">{formatDate(item.timestamp)}</small>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
