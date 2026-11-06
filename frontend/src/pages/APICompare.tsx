import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore';
import { APINav } from '../components/APINav';
import { fetchComparison } from '../services/fetchData';
import { ExplorerApiContext } from '../hooks/useExplorerApi';
import type { ComparisonResult } from '../types';
import { errorMessage } from '../utils/errors';
import { ComparisonView } from './ComparisonView';
import { SCIM } from './SCIM';

interface ComparisonState {
  /** Which request this answers, so a stale answer is never shown. */
  key: string;
  comparison: ComparisonResult | null;
  error: string | null;
}

const APICompare = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { apiUrl, probeApi } = useApiExplorerStore();
  const urlParam = searchParams.get('url');
  // The API named in the URL wins over one probed earlier in the session.
  const effectiveUrl = urlParam || apiUrl;

  // The two collections to compare, kept in the URL so a comparison can be shared.
  const digestA = searchParams.get('a') ?? '';
  const digestB = searchParams.get('b') ?? '';
  const [inputA, setInputA] = useState(digestA);
  const [inputB, setInputB] = useState(digestB);
  const [result, setResult] = useState<ComparisonState | null>(null);
  const requestKey = digestA && digestB ? `${effectiveUrl ?? ''}|${digestA}|${digestB}` : null;

  useEffect(() => {
    if (urlParam && urlParam.replace(/\/+$/, '') !== apiUrl) {
      probeApi(urlParam).catch(() => {});
    }
  }, [urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!requestKey) return;
    let cancelled = false;
    fetchComparison(digestA, digestB, effectiveUrl)
      .then((comparison) => {
        if (!cancelled) setResult({ key: requestKey, comparison, error: null });
      })
      .catch((err) => {
        if (!cancelled) setResult({ key: requestKey, comparison: null, error: errorMessage(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [requestKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSearchParams((prev) => {
      const params = new URLSearchParams(prev);
      params.set('a', inputA.trim());
      params.set('b', inputB.trim());
      return params;
    });
  };

  const current = requestKey && result?.key === requestKey ? result : null;

  return (
    <div>
      <APINav active="compare" />
      <ExplorerApiContext value={effectiveUrl}>
        <form className="card mb-6" onSubmit={handleSubmit}>
          <div className="card__header text-xs font-bold">
            Compare two collections on this API
          </div>
          <div className="card__body flex flex-col gap-2">
            <input
              className="form-input form-input--mono text-sm"
              placeholder="Digest of collection A"
              aria-label="Digest of collection A"
              value={inputA}
              onChange={(e) => setInputA(e.target.value)}
            />
            <input
              className="form-input form-input--mono text-sm"
              placeholder="Digest of collection B"
              aria-label="Digest of collection B"
              value={inputB}
              onChange={(e) => setInputB(e.target.value)}
            />
            <div>
              <button
                className="btn btn--primary btn--sm"
                type="submit"
                disabled={!inputA.trim() || !inputB.trim()}
              >
                Compare
              </button>
            </div>
          </div>
        </form>

        {requestKey && !current && (
          <div className="text-center py-12">
            <div className="spinner" />
          </div>
        )}
        {current?.error && <div className="alert alert--danger">{current.error}</div>}
        {current?.comparison && <ComparisonView paramComparison={current.comparison} />}

        {/* Without two digests, offer the paste-a-comparison tool instead. */}
        {!requestKey && <SCIM />}
      </ExplorerApiContext>
    </div>
  );
};

export { APICompare };
