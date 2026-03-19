import { copyToClipboard } from '../../utilities';

export default function SeqColResult({ result, fileName, onCompare, onDownloadJson, onDownloadRgsi, onCopyJson }) {
  if (!result) return null;

  return (
    <div className="card mt-4">
      <div className="card-header d-flex justify-content-between align-items-center">
        <div>
          <strong>Sequence Collection</strong>
          <span className="text-muted ms-2">({fileName})</span>
        </div>
        <div className="btn-group btn-group-sm">
          <button
            className="btn btn-outline-primary"
            onClick={onCompare}
            title="Compare with database"
          >
            <i className="bi bi-arrow-left-right me-1"></i>
            Compare
          </button>
          <button
            className="btn btn-outline-secondary"
            onClick={onCopyJson}
            title="Copy JSON to clipboard"
          >
            <i className="bi bi-clipboard me-1"></i>
            Copy JSON
          </button>
          <div className="btn-group">
            <button
              type="button"
              className="btn btn-outline-secondary dropdown-toggle"
              data-bs-toggle="dropdown"
              aria-expanded="false"
              title="Download as JSON"
            >
              <i className="bi bi-download me-1"></i>
              JSON
            </button>
            <ul className="dropdown-menu">
              <li>
                <button className="dropdown-item" onClick={() => onDownloadJson('level2')}>
                  Level 2 (arrays)
                </button>
              </li>
              <li>
                <button className="dropdown-item" onClick={() => onDownloadJson('uncollated')}>
                  Uncollated (records)
                </button>
              </li>
              <li>
                <button className="dropdown-item" onClick={() => onDownloadJson('level1')}>
                  Level 1 (digests)
                </button>
              </li>
            </ul>
          </div>
          <button
            className="btn btn-outline-secondary"
            onClick={onDownloadRgsi}
            title="Download as RGSI"
          >
            <i className="bi bi-download me-1"></i>
            RGSI
          </button>
        </div>
      </div>
      <div className="card-body">
        {/* Main digest */}
        <div className="mb-3">
          <label className="form-label text-muted small">Collection Digest</label>
          <div className="d-flex align-items-center gap-2">
            <code className="fs-5 user-select-all">{result.digest}</code>
            <button
              className="btn btn-sm btn-outline-secondary"
              onClick={() => copyToClipboard(result.digest)}
              title="Copy digest"
            >
              <i className="bi bi-clipboard"></i>
            </button>
            <a
              href={`/collection/${result.digest}`}
              className="btn btn-sm btn-outline-primary"
              title="Look up in database"
              target="_blank"
              rel="noopener noreferrer"
            >
              <i className="bi bi-database me-1"></i>
              Lookup
            </a>
          </div>
        </div>

        {/* Level 1 digests */}
        <div className="mb-3">
          <label className="form-label text-muted small">Level 1 Digests</label>
          <table className="table table-sm mb-0">
            <tbody>
              <tr>
                <td className="text-muted">names</td>
                <td><code>{result.names_digest}</code></td>
              </tr>
              <tr>
                <td className="text-muted">sequences</td>
                <td><code>{result.sequences_digest}</code></td>
              </tr>
              <tr>
                <td className="text-muted">lengths</td>
                <td><code>{result.lengths_digest}</code></td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Sequences */}
        <div>
          <label className="form-label text-muted small">
            Sequences ({result.n_sequences})
          </label>
          <div style={{ maxHeight: '400px', overflow: 'auto' }}>
            <table className="table table-sm table-striped mb-0">
              <thead className="sticky-top bg-white">
                <tr>
                  <th>Name</th>
                  <th>Length</th>
                  <th>Alphabet</th>
                  <th>SHA512t24u</th>
                </tr>
              </thead>
              <tbody>
                {result.sequences.map((seq, i) => (
                  <tr key={i}>
                    <td>{seq.name}</td>
                    <td>{seq.length.toLocaleString()}</td>
                    <td><span className="badge bg-secondary">{seq.alphabet}</span></td>
                    <td><code className="small">{seq.sha512t24u}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
