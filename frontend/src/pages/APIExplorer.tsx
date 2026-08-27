import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore';
import { Icon } from '../components/common/Icon';
import { errorMessage } from '../utils/errors';

const RECENT_APIS_KEY = 'refget-explorer-recent-apis';

const getRecentApis = (): string[] => {
  try {
    return JSON.parse(localStorage.getItem(RECENT_APIS_KEY) ?? 'null') || [];
  } catch {
    return [];
  }
};

const DEFAULT_API = 'https://seqcolapi.databio.org';

const APIExplorer = () => {
  const navigate = useNavigate();
  const { probeApi, loading, error } = useApiExplorerStore();
  const [url, setUrl] = useState(DEFAULT_API);
  const [localError, setLocalError] = useState<string | null>(null);
  const recentApis = getRecentApis();

  const handleExplore = async (targetUrl?: string) => {
    const trimmed = (targetUrl || url).trim();
    if (!trimmed) return;
    setLocalError(null);
    try {
      await probeApi(trimmed);
      navigate(`/explore-api/collections?url=${encodeURIComponent(trimmed)}`);
    } catch (err) {
      setLocalError(errorMessage(err));
    }
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    handleExplore();
  };

  return (
    <div className="mb-12">
      <h3 className="font-light mb-4">
        <Icon name="cloud" className="mr-2" />
        API Explorer
      </h3>
      <p className="text-muted">
        Browse any SeqCol API server. Enter the base URL and explore its collections,
        run comparisons, and test compliance.
      </p>

      <form onSubmit={handleSubmit} className="mb-6">
        <div className="input-group">
          <input
            type="url"
            className="form-input form-input--lg"
            placeholder="Enter API URL..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <button
            className="btn btn--primary"
            type="submit"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner spinner--sm mr-2" />
                Connecting...
              </>
            ) : (
              <>
                <Icon name="search" className="mr-2" />
                Explore
              </>
            )}
          </button>
        </div>
      </form>

      {(localError || error) && (
        <div className="alert alert--danger">
          <strong>Failed to connect:</strong> {localError || error}
          <p className="mt-2 mb-0 text-muted text-sm">
            Make sure the URL points to a SeqCol API server with a{' '}
            <code>/service-info</code> endpoint. The server must allow CORS.
          </p>
        </div>
      )}

      {recentApis.length > 0 && (
        <div className="mt-6">
          <h6 className="text-muted">Recent APIs</h6>
          <div className="list-group">
            {recentApis.map((recentUrl: string) => (
              <button
                key={recentUrl}
                className="list-group__item list-group__item--action font-mono text-sm"
                onClick={() => {
                  setUrl(recentUrl);
                  handleExplore(recentUrl);
                }}
              >
                <Icon name="clock" className="mr-2" />
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
