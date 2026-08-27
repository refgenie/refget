import { useState, useRef, useEffect } from 'react';
import type { CSSProperties } from 'react';
import { useSearchParams } from 'react-router-dom';
import { API_BASE } from '../utilities';

/** One compliance check result, as streamed from /compliance/stream. */
interface ComplianceResult {
  type: string;
  name: string;
  description?: string;
  passed: boolean;
  duration_ms: number;
  error?: string;
}

interface ComplianceSummary {
  passed: number;
  failed: number;
  total: number;
  [key: string]: unknown;
}

export const CompliancePage = () => {
  // ?url= prefills the target so "Run compliance" from a specific server's
  // card tests that server rather than dropping back to this one.
  const [searchParams] = useSearchParams();
  const [targetUrl, setTargetUrl] = useState(() => searchParams.get('url') || '');
  const [results, setResults] = useState<ComplianceResult[]>([]);
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [total, setTotal] = useState(0);
  const [serverUrl, setServerUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  // onerror closes over `summary` from the render that started the run, which
  // is always null; track completion in a ref so the guard actually works.
  const doneRef = useRef(false);

  // Close the stream if the user navigates away mid-run.
  useEffect(() => () => eventSourceRef.current?.close(), []);

  // Accept a bare host (e.g. "seqcolapi-demo.databio.org") by defaulting to
  // https:// when no scheme is given.
  const normalizeUrl = (raw: string) => {
    const t = raw.trim();
    if (!t) return '';
    return /^https?:\/\//i.test(t) ? t : `https://${t}`;
  };

  const runCompliance = () => {
    setLoading(true);
    setError(null);
    setResults([]);
    setSummary(null);
    setTotal(0);
    setServerUrl('');
    doneRef.current = false;

    const normalized = normalizeUrl(targetUrl);
    if (normalized !== targetUrl) setTargetUrl(normalized); // reflect back to the user

    const params = normalized
      ? `?target_url=${encodeURIComponent(normalized)}`
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
        doneRef.current = true;
        setSummary(data);
        setLoading(false);
        es.close();
      }
    };

    es.onerror = () => {
      if (!doneRef.current) {
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
      <p className="text-muted mb-6">
        Run GA4GH SeqCol specification compliance checks against any server.
        Structure tests validate response format, pagination, and endpoint availability.
      </p>

      <div className="card mb-6">
        <div className="card__body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div className="md:col-span-2">
              <label htmlFor="targetUrl" className="form-label font-medium">
                Target Server URL
              </label>
              <input
                type="text"
                className="form-input"
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
            <div>
              {loading ? (
                <button
                  className="btn btn--outline-danger w-full"
                  onClick={stopCompliance}
                >
                  <span className="spinner spinner--sm mr-2" role="status" />
                  Stop ({completed}/{total})
                </button>
              ) : (
                <button
                  className="btn btn--primary w-full"
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
        <div className="alert alert--danger" role="alert">
          <strong>Error:</strong> {error}
        </div>
      )}

      {(results.length > 0 || loading) && (
        <div>
          <div className="card mb-6">
            <div className="card__body">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-xl font-bold">{total}</div>
                  <div className="text-muted text-sm">Total</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-success-fg">{passed}</div>
                  <div className="text-muted text-sm">Passed</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-danger-fg">{failed}</div>
                  <div className="text-muted text-sm">Failed</div>
                </div>
                <div>
                  <div className="text-muted text-sm mt-1">
                    {serverUrl}
                  </div>
                  {summary && (
                    <div className="text-muted text-sm">
                      {new Date().toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-4">
                <div className="progress progress--split">
                  <div
                    className="progress__bar progress__bar--pass"
                    style={{
                      '--progress-value': `${total > 0 ? (passed / total) * 100 : 0}%`,
                    } as CSSProperties}
                  />
                  <div
                    className="progress__bar progress__bar--fail"
                    style={{
                      '--progress-value': `${total > 0 ? (failed / total) * 100 : 0}%`,
                    } as CSSProperties}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="list-group">
            {results.map((result, idx) => (
              <div
                key={idx}
                className={`list-group__item flex justify-between items-start ${
 result.passed ? '' : 'list-group__item--danger'
 }`}
              >
                <div className="mr-auto">
                  <div className="flex items-center">
                    <span
                      className={`badge badge--pill mr-2 ${
 result.passed ? 'badge--success' : 'badge--danger'
 }`}
                    >
                      {result.passed ? 'PASS' : 'FAIL'}
                    </span>
                    <span className="font-medium">{result.name}</span>
                  </div>
                  {result.description && (
                    <div className="text-muted text-sm mt-1">
                      {result.description}
                    </div>
                  )}
                  {result.error && (
                    <div className="text-danger-fg text-sm mt-1">
                      <code className="code code--inline">{result.error}</code>
                    </div>
                  )}
                </div>
                <span className="badge bg-surface-muted text-strong">
                  {result.duration_ms.toFixed(0)}ms
                </span>
              </div>
            ))}
            {loading && completed < total && (
              <div className="list-group__item text-muted flex items-center">
                <span className="spinner spinner--sm mr-2" role="status" />
                Running check {completed + 1} of {total}...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
