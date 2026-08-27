import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore';
import { Icon } from '../components/common/Icon';
import { errorMessage } from '../utils/errors';

const RECENT_STORES_KEY = 'refget-explorer-recent-stores';
const MAX_RECENT = 5;

const getRecentStores = (): string[] => {
  try {
    return JSON.parse(localStorage.getItem(RECENT_STORES_KEY) ?? 'null') || [];
  } catch {
    return [];
  }
};

const saveRecentStore = (url: string) => {
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
  const [localError, setLocalError] = useState<string | null>(null);
  const recentStores = getRecentStores();

  const handleExplore = async (targetUrl?: string) => {
    const trimmed = (targetUrl || url).trim();
    if (!trimmed) return;
    setLocalError(null);
    try {
      await loadStore(trimmed);
      saveRecentStore(trimmed);
      navigate(`/explore-store/overview?url=${encodeURIComponent(trimmed)}`);
    } catch (err) {
      setLocalError(errorMessage(err));
    }
  };

  // Auto-load if URL param provided
  useEffect(() => {
    const paramUrl = searchParams.get('url');
    if (paramUrl && paramUrl !== storeUrl) {
      // Auto-trigger a store load from the URL param on mount; handleExplore
      // performs an async fetch and only sets state afterward, so this is a
      // deliberate load-on-mount, not a synchronous cascading render.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      handleExplore(paramUrl);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    handleExplore();
  };

  return (
    <div className="mb-12">
      <h3 className="font-light mb-4">
        <Icon name="archive" className="mr-2" />
        RefgetStore Explorer
      </h3>
      <p className="text-muted">
        Browse the contents of any RefgetStore — sequences, collections, aliases,
        and metadata. Enter the URL of a store hosted on any HTTP server.
      </p>

      <form onSubmit={handleSubmit} className="mb-6">
        <div className="input-group">
          <input
            type="url"
            className="form-input"
            placeholder="https://example.com/path/to/refget-store/"
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
                Loading...
              </>
            ) : (
              <>
                <Icon name="search" className="mr-2" />
                Explore store
              </>
            )}
          </button>
        </div>
      </form>

      {(localError || error) && (
        <div className="alert alert--danger">
          <strong>Failed to load store:</strong> {localError || error}
          <p className="mt-2 mb-0 text-muted text-sm">
            Make sure the URL points to a valid RefgetStore directory with an{' '}
            <code>rgstore.json</code> file. The server must allow cross-origin
            requests (CORS).
          </p>
        </div>
      )}

      {recentStores.length > 0 && (
        <div className="mt-6">
          <h6 className="text-muted">Recent stores</h6>
          <div className="list-group">
            {recentStores.map((recentUrl: string) => (
              <div
                key={recentUrl}
                className="list-group__item flex justify-between items-center"
              >
                <span className="font-mono text-sm text-truncate mr-2">{recentUrl}</span>
                <span className="flex gap-1 flex-shrink-0">
                  <button
                    className="btn btn--sm btn--outline-secondary"
                    title="Copy URL"
                    onClick={() => navigator.clipboard.writeText(recentUrl)}
                  >
                    <Icon name="clipboard" />
                  </button>
                  <button
                    className="btn btn--sm btn--outline-primary"
                    title="Load store"
                    onClick={() => {
                      setUrl(recentUrl);
                      handleExplore(recentUrl);
                    }}
                  >
                    <Icon name="log-in" />
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
