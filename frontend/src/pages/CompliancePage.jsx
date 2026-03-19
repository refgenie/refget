import React, { useState, useRef } from 'react';
import { API_BASE } from '../utilities.jsx';

export const CompliancePage = () => {
  const [targetUrl, setTargetUrl] = useState('');
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState(null);
  const [total, setTotal] = useState(0);
  const [serverUrl, setServerUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);

  const runCompliance = () => {
    setLoading(true);
    setError(null);
    setResults([]);
    setSummary(null);
    setTotal(0);
    setServerUrl('');

    const params = targetUrl.trim()
      ? `?target_url=${encodeURIComponent(targetUrl.trim())}`
      : '';
    const url = `${API_BASE}/compliance/stream${params}`;

    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'start') {
        setTotal(data.total);
        setServerUrl(data.server_url);
      } else if (data.type === 'result') {
        setResults((prev) => [...prev, data]);
      } else if (data.type === 'done') {
        setSummary(data);
        setLoading(false);
        es.close();
      }
    };

    es.onerror = () => {
      if (!summary) {
        setError('Connection lost or server unavailable');
      }
      setLoading(false);
      es.close();
    };
  };

  const stopCompliance = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setLoading(false);
  };

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;
  const completed = results.length;

  return (
    <div>
      <h2>Compliance Test Runner</h2>
      <p className="text-muted mb-4">
        Run GA4GH SeqCol specification compliance checks against any server.
        Structure tests validate response format, pagination, and endpoint availability.
      </p>

      <div className="card mb-4">
        <div className="card-body">
          <div className="row align-items-end">
            <div className="col-md-8">
              <label htmlFor="targetUrl" className="form-label fw-medium">
                Target Server URL
              </label>
              <input
                type="text"
                className="form-control"
                id="targetUrl"
                placeholder={`Leave empty to test this server (${API_BASE})`}
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !loading) runCompliance();
                }}
                disabled={loading}
              />
            </div>
            <div className="col-md-4 mt-2 mt-md-0">
              {loading ? (
                <button
                  className="btn btn-outline-danger w-100"
                  onClick={stopCompliance}
                >
                  <span className="spinner-border spinner-border-sm me-2" role="status" />
                  Stop ({completed}/{total})
                </button>
              ) : (
                <button
                  className="btn btn-primary w-100"
                  onClick={runCompliance}
                >
                  Run Compliance Tests
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          <strong>Error:</strong> {error}
        </div>
      )}

      {(results.length > 0 || loading) && (
        <div>
          <div className="card mb-4">
            <div className="card-body">
              <div className="row text-center">
                <div className="col-md-3">
                  <div className="fs-4 fw-bold">{total}</div>
                  <div className="text-muted small">Total</div>
                </div>
                <div className="col-md-3">
                  <div className="fs-4 fw-bold text-success">{passed}</div>
                  <div className="text-muted small">Passed</div>
                </div>
                <div className="col-md-3">
                  <div className="fs-4 fw-bold text-danger">{failed}</div>
                  <div className="text-muted small">Failed</div>
                </div>
                <div className="col-md-3">
                  <div className="text-muted small mt-1">
                    {serverUrl}
                  </div>
                  {summary && (
                    <div className="text-muted small">
                      {new Date().toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-3">
                <div className="progress" style={{ height: '8px' }}>
                  <div
                    className="progress-bar bg-success"
                    style={{
                      width: `${total > 0 ? (passed / total) * 100 : 0}%`,
                      transition: 'width 0.3s ease',
                    }}
                  />
                  <div
                    className="progress-bar bg-danger"
                    style={{
                      width: `${total > 0 ? (failed / total) * 100 : 0}%`,
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="list-group">
            {results.map((result, idx) => (
              <div
                key={idx}
                className={`list-group-item d-flex justify-content-between align-items-start ${
                  result.passed ? '' : 'list-group-item-danger'
                }`}
              >
                <div className="me-auto">
                  <div className="d-flex align-items-center">
                    <span
                      className={`badge rounded-pill me-2 ${
                        result.passed ? 'bg-success' : 'bg-danger'
                      }`}
                    >
                      {result.passed ? 'PASS' : 'FAIL'}
                    </span>
                    <span className="fw-medium">{result.name}</span>
                  </div>
                  {result.description && (
                    <div className="text-muted small mt-1">
                      {result.description}
                    </div>
                  )}
                  {result.error && (
                    <div className="text-danger small mt-1">
                      <code>{result.error}</code>
                    </div>
                  )}
                </div>
                <span className="badge bg-light text-dark">
                  {result.duration_ms.toFixed(0)}ms
                </span>
              </div>
            ))}
            {loading && completed < total && (
              <div className="list-group-item text-muted d-flex align-items-center">
                <span className="spinner-border spinner-border-sm me-2" role="status" />
                Running check {completed + 1} of {total}...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
