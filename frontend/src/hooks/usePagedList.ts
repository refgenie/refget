import { useState, useMemo } from 'react';

/**
 * Shared filter + sort + pagination state for store list views.
 *
 * This encapsulates the pattern repeated across the sequence, alias, and
 * collection tables: memoize a filtered view, optionally sort it, and slice it
 * into fixed-size pages, resetting to page 0 whenever the filter or sort
 * changes. Render the returned `paged` rows and drive navigation with the
 * returned `page`/`setPage`/`totalPages` (see components/PaginationNav.tsx).
 */
export interface PagedListOptions<T> {
  /** Match a row against the lowercased filter term; omit to disable filtering. */
  filterFn?: (item: T, term: string) => boolean;
  /** Initial sort column key. */
  initialSort?: string | null;
  /** Rows per page. */
  pageSize?: number;
}

export function usePagedList<T extends object>(
  rows: T[] | null | undefined,
  { filterFn, initialSort = null, pageSize = 50 }: PagedListOptions<T> = {},
) {
  const [filter, setFilterRaw] = useState('');
  const [page, setPage] = useState(0);
  const [sortCol, setSortCol] = useState<string | null>(initialSort);
  const [sortAsc, setSortAsc] = useState(true);

  const filtered = useMemo(() => {
    const list = rows ?? [];
    if (!filterFn || !filter) return list;
    const term = filter.toLowerCase();
    return list.filter((item) => filterFn(item, term));
  }, [rows, filter, filterFn]);

  const sorted = useMemo(() => {
    if (!sortCol) return filtered;
    return [...filtered].sort((a, b) => {
      const va = (a as unknown as Record<string, unknown>)[sortCol];
      const vb = (b as unknown as Record<string, unknown>)[sortCol];
      if (typeof va === 'number' && typeof vb === 'number') {
        return sortAsc ? va - vb : vb - va;
      }
      return sortAsc
        ? String(va ?? '').localeCompare(String(vb ?? ''))
        : String(vb ?? '').localeCompare(String(va ?? ''));
    });
  }, [filtered, sortCol, sortAsc]);

  const totalPages = Math.ceil(sorted.length / pageSize);
  // Clamp so a shrinking result set (e.g. after filtering) never leaves us
  // stranded on an out-of-range page.
  const clampedPage = Math.min(page, Math.max(0, totalPages - 1));
  const paged = sorted.slice(clampedPage * pageSize, (clampedPage + 1) * pageSize);

  const setFilter = (value: string) => {
    setFilterRaw(value);
    setPage(0);
  };

  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortAsc((asc) => !asc);
    } else {
      setSortCol(col);
      setSortAsc(true);
    }
    setPage(0);
  };

  const resetPage = () => setPage(0);

  return {
    filter,
    setFilter,
    page: clampedPage,
    setPage,
    resetPage,
    sortCol,
    sortAsc,
    handleSort,
    filtered,
    sorted,
    paged,
    totalPages,
  };
}
