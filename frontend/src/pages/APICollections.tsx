import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore';
import { APINav } from '../components/APINav';
import { PaginationNav } from '../components/PaginationNav';
import { fetchCollectionPage } from '../services/fetchData';
import type { PagedResult } from '../types';
import { errorMessage } from '../utils/errors';
import { apiQuery } from '../utils/explorerLinks';

const PAGE_SIZE = 50;

interface PageResult {
  /** Which request this answers, so a stale answer is never shown. */
  key: string;
  data: PagedResult<string> | null;
  error: string | null;
}

const APICollections = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { apiUrl, probeApi } = useApiExplorerStore();
  const [result, setResult] = useState<PageResult | null>(null);

  const urlParam = searchParams.get('url');
  // The API named in the URL wins over one probed earlier in the session.
  const effectiveUrl = urlParam || apiUrl;
  // Zero-based page index. The URL holds the one-based page number people see.
  const page = Math.max(0, (Number(searchParams.get('page')) || 1) - 1);
  const requestKey = `${urlParam ?? ''}|${page}`;

  useEffect(() => {
    const controller = new AbortController();
    const init = async () => {
      try {
        if (urlParam && urlParam.replace(/\/+$/, '') !== apiUrl) {
          await probeApi(urlParam);
        }
        const data = await fetchCollectionPage(effectiveUrl, page, PAGE_SIZE, {
          signal: controller.signal,
        });
        setResult({ key: requestKey, data, error: null });
      } catch (err) {
        if (controller.signal.aborted) return;
        setResult({ key: requestKey, data: null, error: errorMessage(err) });
      }
    };
    init();
    return () => controller.abort();
  }, [requestKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const goToPage = (next: number) => {
    setSearchParams((prev) => {
      const params = new URLSearchParams(prev);
      if (next > 0) params.set('page', String(next + 1));
      else params.delete('page');
      return params;
    });
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
  };

  const current = result?.key === requestKey ? result : null;

  if (!current) {
    return (
      <div>
        <APINav active="collections" />
        <div className="text-center py-12">
          <div className="spinner" />
          <p className="mt-4 text-muted">Loading collections...</p>
        </div>
      </div>
    );
  }

  if (current.error) {
    return (
      <div>
        <APINav active="collections" />
        <div className="alert alert--danger">{current.error}</div>
      </div>
    );
  }

  const collections = current.data;
  const total = collections?.pagination?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="mb-12">
      <APINav active="collections" />

      <div className="flex justify-end mb-4">
        <div className="card">
          <div className="card__body py-2 px-4 text-xs">
            <b>{total}</b> collections
          </div>
        </div>
      </div>

      {collections?.results?.length ? (
        <ul>
          {collections.results.map((digest: string) => (
            <li key={digest}>
              <Link
                to={`/explore-api/collection/${digest}${apiQuery(effectiveUrl)}`}
                className="font-mono"
              >
                {digest}
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted">No collections found.</p>
      )}

      <PaginationNav page={page} totalPages={totalPages} onChange={goToPage} />
    </div>
  );
};

export { APICollections };
