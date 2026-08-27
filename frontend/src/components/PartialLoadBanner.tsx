import { formatBytes } from '../utilities';
import { Icon } from './common/Icon';

/**
 * Warning banner shown when only a byte-bounded prefix of a large index was
 * loaded. Offers a "Load all" action that re-fetches the full file. Shared by
 * any bounded list view (sequences, aliases).
 */
interface PartialLoadBannerProps {
  /** Full file size in bytes. */
  totalSize: number;
  /** Number of rows currently loaded. */
  loadedCount: number;
  /** Plural noun for the rows. */
  noun?: string;
  /** Triggers a full re-fetch. */
  onLoadAll: () => void;
  /** Disables the button while a load is in flight. */
  loading?: boolean;
}

export function PartialLoadBanner({
  totalSize,
  loadedCount,
  noun = 'entries',
  onLoadAll,
  loading,
}: PartialLoadBannerProps) {
  return (
    <div className="alert alert--warning flex justify-between items-center py-2">
      <span>
        <Icon name="warning" className="mr-2" />
        Index is {formatBytes(totalSize)} — showing first{' '}
        {loadedCount.toLocaleString()} {noun}. Sorting and filtering apply only
        to loaded data.
      </span>
      <button
        className="btn btn--sm btn--warning ml-4"
        onClick={onLoadAll}
        disabled={loading}
      >
        Load all ({formatBytes(totalSize)})
      </button>
    </div>
  );
}
