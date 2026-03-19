import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore.js';

const RECENT_APIS_KEY = 'refget-explorer-recent-apis';
const MAX_RECENT = 5;

const getRecentApis = () => {
  try {
    return JSON.parse(localStorage.getItem(RECENT_APIS_KEY)) || [];
  } catch {
    return [];
  }
};

const APIExplorer = () => {
  const navigate = useNavigate();
  const { probeApi, loading, error } = useApiExplorerStore();
  const [url, setUrl] = useState('');
  const [localError, setLocalError] = useState(null);
  const recentApis = getRecentApis();

  const handleExplore = async (targetUrl) => {
    const trimmed = (targetUrl || url).trim();
    if (!trimmed) return;
    setLocalError(null);
    try {
      await probeApi(trimmed);
      navigate(`/explore-api/collections?url=${encodeURIComponent(trimmed)}`);
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
        <i className="bi bi-cloud me-2" />
        API Explorer
      </h3>
      <p className="text-muted">
        Browse any SeqCol API server. Enter the base URL and explore its collections,
        run comparisons, and test compliance.
      </p>

      <form onSubmit={handleSubmit} className="mb-4">
        <div className="input-group input-group-lg">
          <input
            type="url"
            className="form-control"
            placeholder="https://seqcolapi.databio.org"
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
                Connecting...
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
          <strong>Failed to connect:</strong> {localError || error}
          <p className="mt-2 mb-0 text-muted small">
            Make sure the URL points to a SeqCol API server with a{' '}
            <code>/service-info</code> endpoint. The server must allow CORS.
          </p>
        </div>
      )}

      {recentApis.length > 0 && (
        <div className="mt-4">
          <h6 className="text-muted">Recent APIs</h6>
          <div className="list-group">
            {recentApis.map((recentUrl) => (
              <button
                key={recentUrl}
                className="list-group-item list-group-item-action font-monospace small"
                onClick={() => {
                  setUrl(recentUrl);
                  handleExplore(recentUrl);
                }}
              >
                <i className="bi bi-clock-history me-2" />
                {recentUrl}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export { APIExplorer };
