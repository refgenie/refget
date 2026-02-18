import { useState, useRef, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import FastaDropzone from './FastaDropzone';
import SeqColResult from './SeqColResult';
import './digest.css';

const HISTORY_KEY = 'digest-history';
const MAX_HISTORY = 20;

// Get history list from localStorage
function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
  } catch {
    return [];
  }
}

// Save result and update history
function saveToHistory(result, fileName) {
  const key = result.digest;

  // Save full result
  localStorage.setItem(`digest-${key}`, JSON.stringify({ result, fileName }));

  // Update history index
  let history = getHistory();
  // Remove if already exists (we'll re-add at top)
  history = history.filter(h => h.digest !== key);
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
    removed.forEach(h => localStorage.removeItem(`digest-${h.digest}`));
  }
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

// Load result from localStorage
function loadFromHistory(digest) {
  try {
    const stored = localStorage.getItem(`digest-${digest}`);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function createWorker() {
  return new Worker(
    new URL('./fastaDigestWorker.js', import.meta.url),
    { type: 'module' }
  );
}

export default function DigestPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [fileName, setFileName] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const workerRef = useRef(null);

  // Load history on mount
  useEffect(() => {
    setHistory(getHistory());
  }, []);

  // Restore state from URL on mount or when URL changes (back/forward)
  useEffect(() => {
    const key = searchParams.get('id');
    if (key) {
      const stored = loadFromHistory(key);
      if (stored) {
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

    worker.onmessage = (e) => {
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
        const name = worker._fileName;
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

    workerRef.current = worker;
    return worker;
  }, []);

  // Initialize worker on mount
  useEffect(() => {
    setupWorker();
    return () => workerRef.current?.terminate();
  }, [setupWorker]);

  const handleFileSelected = (file) => {
    // Cancel and replace any running worker to prevent double-processing
    const worker = setupWorker();
    setFileName(file.name);
    setResult(null);
    setError(null);
    setProgress(null);
    setStats(null);
    setStatus('Starting...');
    worker._fileName = file.name;
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

  const handleHistoryClick = (digest) => {
    navigate(`/fasta?id=${digest}`);
  };

  const clearHistory = () => {
    history.forEach(h => localStorage.removeItem(`digest-${h.digest}`));
    localStorage.removeItem(HISTORY_KEY);
    setHistory([]);
    toast.success('History cleared');
  };

  const isProcessing = status !== null;

  const formatSize = (bytes) => {
    if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
    if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
    if (bytes >= 1e3) return `${(bytes / 1e3).toFixed(1)} KB`;
    return `${bytes} bytes`;
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  // Generate RGSI file content from result
  const generateRgsi = (result) => {
    const lines = [
      `##seqcol_digest=${result.digest}`,
      `##names_digest=${result.names_digest}`,
      `##sequences_digest=${result.sequences_digest}`,
      `##lengths_digest=${result.lengths_digest}`,
      '#name\tlength\talphabet\tsha512t24u\tmd5\tdescription',
      ...result.sequences.map(seq =>
        `${seq.name}\t${seq.length}\t${seq.alphabet}\t${seq.sha512t24u}\t${seq.md5 || ''}\t${seq.description || ''}`
      )
    ];
    return lines.join('\n') + '\n';
  };

  // Convert result to level 1 seqcol format (digests only)
  const resultToSeqcolLevel1 = (result) => ({
    lengths: result.lengths_digest,
    names: result.names_digest,
    sequences: result.sequences_digest,
    // Note: sorted_sequences and name_length_pairs digests not computed by WASM
  });

  // Convert result to level 2 seqcol format (arrays)
  const resultToSeqcolLevel2 = (result) => {
    // Build sequences array - check if sha512t24u already has SQ. prefix
    const sequences = result.sequences.map(s => {
      const digest = s.sha512t24u;
      return digest.startsWith('SQ.') ? digest : `SQ.${digest}`;
    });

    const level2 = {
      lengths: result.sequences.map(s => Math.floor(s.length)), // ensure integers
      names: result.sequences.map(s => s.name),
      sequences: sequences,
      sorted_sequences: [...sequences].sort(),
      name_length_pairs: result.sequences.map(s => ({
        length: Math.floor(s.length),
        name: s.name
      }))
    };

    return level2;
  };

  // Convert result to uncollated format (record per sequence)
  const resultToSeqcolUncollated = (result) =>
    result.sequences.map(s => ({
      name: s.name,
      length: s.length,
      sequence: s.sha512t24u.startsWith('SQ.') ? s.sha512t24u : `SQ.${s.sha512t24u}`
    }));

  // Navigate to SCOM with this collection pre-loaded
  const handleCompareInScom = () => {
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

  const handleDownloadJson = (format) => {
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
    const blob = new Blob([generateRgsi(result)], { type: 'text/tab-separated-values' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${fileName.replace(/\.(fa|fasta|fna)(\.gz)?$/i, '')}.rgsi`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container py-4">
      <h2 className="mb-3">
        <i className="bi bi-fingerprint me-2"></i>
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
        <div className="mt-3">
          <div className="d-flex align-items-center mb-2">
            <div className="spinner-border spinner-border-sm me-2"></div>
            <span>{status}</span>
            <button
              className="btn btn-sm btn-outline-danger ms-3"
              onClick={handleCancel}
            >
              Cancel
            </button>
          </div>

          {progress && (
            <>
              <div className="progress" style={{ height: '20px' }}>
                <div
                  className="progress-bar progress-bar-striped progress-bar-animated"
                  role="progressbar"
                  style={{ width: `${progress.percent}%` }}
                  aria-valuenow={progress.percent}
                  aria-valuemin="0"
                  aria-valuemax="100"
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
        <div className={`alert ${error === 'Processing cancelled.' ? 'alert-warning' : 'alert-danger'} mt-3 d-flex justify-content-between align-items-center`}>
          <div>
            <i className={`bi ${error === 'Processing cancelled.' ? 'bi-x-circle' : 'bi-exclamation-triangle'} me-2`}></i>
            {error}
          </div>
          <button
            className="btn btn-sm btn-outline-secondary"
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
        <details className="mt-3">
          <summary className="text-muted" style={{ cursor: 'pointer' }}>
            <small>Processing details</small>
          </summary>
          <div className="mt-2 small text-muted">
            <div>Chunks processed: {stats.chunks.toLocaleString()}</div>
            <div>Average chunk size: {(stats.avgChunkSize / 1024).toFixed(1)} KB</div>
            <div>Elapsed time: {(stats.elapsedMs / 1000).toFixed(1)}s</div>
            <div>Throughput: {(stats.totalBytes / stats.elapsedMs / 1024).toFixed(1)} MB/s</div>
          </div>
        </details>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="mt-5">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5 className="text-muted mb-0">
              <i className="bi bi-clock-history me-2"></i>
              Recent Digests
            </h5>
            <button
              className="btn btn-sm btn-outline-secondary"
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
                  className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${
                    isSelected ? 'bg-light border-primary' : ''
                  }`}
                  onClick={() => handleHistoryClick(item.digest)}
                >
                  <div>
                    <div className="fw-medium">{item.fileName}</div>
                    <small className={isSelected ? 'text-primary' : 'text-muted'}>
                      <code>{item.digest}</code>
                      <span className="ms-2">({item.n_sequences} sequences)</span>
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
