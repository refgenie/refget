import { formatBytes } from '../utilities.jsx';

/**
 * Warning banner shown when only a byte-bounded prefix of a large index was
 * loaded. Offers a "Load all" action that re-fetches the full file. Shared by
 * any bounded list view (sequences, aliases).
 *
 * @param {number} totalSize    full file size in bytes
 * @param {number} loadedCount  number of rows currently loaded
 * @param {string} [noun]       plural noun for the rows (default "entries")
 * @param {() => void} onLoadAll  triggers a full re-fetch
 * @param {boolean} [loading]   disables the button while a load is in flight
 */
export function PartialLoadBanner({ totalSize, loadedCount, noun = 'entries', onLoadAll, loading }) {
  return (
    <div className="alert alert-warning d-flex justify-content-between align-items-center py-2">
      <span>
        <i className="bi bi-exclamation-triangle me-2" />
        Index is {formatBytes(totalSize)} — showing first{' '}
        {loadedCount.toLocaleString()} {noun}. Sorting and filtering apply only
        to loaded data.
      </span>
      <button
        className="btn btn-sm btn-warning ms-3"
        onClick={onLoadAll}
        disabled={loading}
      >
        Load all ({formatBytes(totalSize)})
      </button>
    </div>
  );
}
