import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore.js';
import { APINav } from '../components/APINav.jsx';
import { fetchSeqColList } from '../services/fetchData.jsx';

const APICollections = () => {
  const [searchParams] = useSearchParams();
  const { apiUrl, probeApi, loading: probing } = useApiExplorerStore();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
        setError(err.message);
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
        <div className="text-center py-5">
          <div className="spinner-border" />
          <p className="mt-3 text-muted">Loading collections...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <APINav active="collections" />
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  }

  if (!data || !Array.isArray(data) || data.length < 1) {
    return (
      <div>
        <APINav active="collections" />
        <div className="alert alert-warning">No data available.</div>
      </div>
    );
  }

  const collections = data[0];
  const urlSuffix = effectiveUrl ? `?url=${encodeURIComponent(effectiveUrl)}` : '';

  return (
    <div className="mb-5">
      <APINav active="collections" />

      <div className="d-flex justify-content-end mb-3">
        <div className="card">
          <div className="card-body py-2 px-3 tiny">
            <b>{collections?.pagination?.total ?? 0}</b> collections
          </div>
        </div>
      </div>

      {collections?.results?.length > 0 ? (
        <ul>
          {collections.results.map((digest) => (
            <li key={digest}>
              <Link
                to={`/explore-api/collection/${digest}${urlSuffix}`}
                className="font-monospace"
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
