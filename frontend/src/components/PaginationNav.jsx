/**
 * Compact Previous / Page X of Y / Next control shared by store list tables.
 * Renders nothing when there is a single page (or none).
 *
 * @param {number} page        current zero-based page index
 * @param {number} totalPages  total number of pages
 * @param {(page: number) => void} onChange  called with the requested page index
 */
export function PaginationNav({ page, totalPages, onChange }) {
  if (totalPages <= 1) return null;
  return (
    <nav>
      <ul className="pagination pagination-sm justify-content-center">
        <li className={`page-item ${page === 0 ? 'disabled' : ''}`}>
          <button className="page-link" onClick={() => onChange(page - 1)}>
            Previous
          </button>
        </li>
        <li className="page-item disabled">
          <span className="page-link">
            Page {page + 1} of {totalPages}
          </span>
        </li>
        <li className={`page-item ${page >= totalPages - 1 ? 'disabled' : ''}`}>
          <button className="page-link" onClick={() => onChange(page + 1)}>
            Next
          </button>
        </li>
      </ul>
    </nav>
  );
}
