import { cn } from '../utils/cn';

interface PaginationNavProps {
  /** Current zero-based page index. */
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}

/**
 * Compact Previous / Page X of Y / Next control shared by store list tables.
 * Renders nothing when there is a single page (or none).
 */
export function PaginationNav({ page, totalPages, onChange }: PaginationNavProps) {
  if (totalPages <= 1) return null;
  return (
    <nav>
      <ul className="pagination justify-center">
        <li>
          <button
            className={cn('pagination__page', page === 0 && 'pagination__page--disabled')}
            disabled={page === 0}
            onClick={() => onChange(page - 1)}
          >
            Previous
          </button>
        </li>
        <li>
          <span className="pagination__page pagination__page--disabled">
            Page {page + 1} of {totalPages}
          </span>
        </li>
        <li>
          <button
            className={cn(
              'pagination__page',
              page >= totalPages - 1 && 'pagination__page--disabled',
            )}
            disabled={page >= totalPages - 1}
            onClick={() => onChange(page + 1)}
          >
            Next
          </button>
        </li>
      </ul>
    </nav>
  );
}
