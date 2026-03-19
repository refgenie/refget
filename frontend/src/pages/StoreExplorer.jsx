import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore.js';

const RECENT_STORES_KEY = 'refget-explorer-recent-stores';
const MAX_RECENT = 5;

const getRecentStores = () => {
  try {
    return JSON.parse(localStorage.getItem(RECENT_STORES_KEY)) || [];
  } catch {
    return [];
  }
};

const saveRecentStore = (url) => {
  const recent = getRecentStores().filter((u) => u !== url);
  recent.unshift(url);
  localStorage.setItem(
    RECENT_STORES_KEY,
    JSON.stringify(recent.slice(0, MAX_RECENT)),
  );
};

const StoreExplorer = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { loadStore, loading, error, storeUrl } = useExplorerStore();
  const [url, setUrl] = useState(searchParams.get('url') || '');
  const [localError, setLocalError] = useState(null);
  const recentStores = getRecentStores();

  // Auto-load if URL param provided
  useEffect(() => {
    const paramUrl = searchParams.get('url');
    if (paramUrl && paramUrl !== storeUrl) {
      handleExplore(paramUrl);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleExplore = async (targetUrl) => {
    const trimmed = (targetUrl || url).trim();
    if (!trimmed) return;
    setLocalError(null);
    try {
      await loadStore(trimmed);
      saveRecentStore(trimmed);
      navigate(`/explore-store/overview?url=${encodeURIComponent(trimmed)}`);
    } catch (err) {
      setLocalError(err.message);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleExplore();
  };

  return (
    <div className="mb-5">
      <h3 className="fw-light mb-3">
        <i className="bi bi-archive me-2" />
        RefgetStore Explorer
      </h3>
      <p className="text-muted">
        Browse the contents of any RefgetStore — sequences, collections, aliases,
        and metadata. Enter the URL of a store hosted on any HTTP server.
      </p>

      <form onSubmit={handleSubmit} className="mb-4">
        <div className="input-group input-group-lg">
          <input
            type="url"
            className="form-control"
            placeholder="https://example.com/path/to/refget-store/"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <button
            className="btn btn-primary"
            type="submit"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" />
                Loading...
              </>
            ) : (
              <>
                <i className="bi bi-search me-2" />
                Explore
              </>
            )}
          </button>
        </div>
      </form>

      {(localError || error) && (
        <div className="alert alert-danger">
          <strong>Failed to load store:</strong> {localError || error}
          <p className="mt-2 mb-0 text-muted small">
            Make sure the URL points to a valid RefgetStore directory with an{' '}
            <code>rgstore.json</code> file. The server must allow cross-origin
            requests (CORS).
          </p>
        </div>
      )}

      {recentStores.length > 0 && (
        <div className="mt-4">
          <h6 className="text-muted">Recent stores</h6>
          <div className="list-group">
            {recentStores.map((recentUrl) => (
              <div
                key={recentUrl}
                className="list-group-item d-flex justify-content-between align-items-center"
              >
                <span className="font-monospace small text-truncate me-2">{recentUrl}</span>
                <span className="d-flex gap-1 flex-shrink-0">
                  <button
                    className="btn btn-sm btn-outline-secondary"
                    title="Copy URL"
                    onClick={() => navigator.clipboard.writeText(recentUrl)}
                  >
                    <i className="bi bi-clipboard" />
                  </button>
                  <button
                    className="btn btn-sm btn-outline-primary"
                    title="Load store"
                    onClick={() => {
                      setUrl(recentUrl);
                      handleExplore(recentUrl);
                    }}
                  >
                    <i className="bi bi-box-arrow-in-right" />
                  </button>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export { StoreExplorer };
