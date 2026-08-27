import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore';
import { APINav } from '../components/APINav';
import { fetchSeqColList } from '../services/fetchData';
import type { PagedResult } from '../types';
import { errorMessage } from '../utils/errors';

const APICollections = () => {
  const [searchParams] = useSearchParams();
  const { apiUrl, probeApi, loading: probing } = useApiExplorerStore();
  // fetchSeqColList resolves to [collections, pangenomes, attributes].
  const [data, setData] = useState<Array<PagedResult<string> | null> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const urlParam = searchParams.get('url');
  const effectiveUrl = apiUrl || urlParam;

  useEffect(() => {
    const init = async () => {
      try {
        if (urlParam && !apiUrl) {
          await probeApi(urlParam);
        }
        const result = await fetchSeqColList(effectiveUrl);
        setData(result);
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading || probing) {
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

  if (error) {
    return (
      <div>
        <APINav active="collections" />
        <div className="alert alert--danger">{error}</div>
      </div>
    );
  }

  if (!data || !Array.isArray(data) || data.length < 1) {
    return (
      <div>
        <APINav active="collections" />
        <div className="alert alert--warning">No data available.</div>
      </div>
    );
  }

  const collections = data[0];
  const urlSuffix = effectiveUrl ? `?url=${encodeURIComponent(effectiveUrl)}` : '';

  return (
    <div className="mb-12">
      <APINav active="collections" />

      <div className="flex justify-end mb-4">
        <div className="card">
          <div className="card__body py-2 px-4 text-xs">
            <b>{collections?.pagination?.total ?? 0}</b> collections
          </div>
        </div>
      </div>

      {collections?.results?.length ? (
        <ul>
          {collections.results.map((digest: string) => (
            <li key={digest}>
              <Link
                to={`/explore-api/collection/${digest}${urlSuffix}`}
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
    </div>
  );
};

export { APICollections };
