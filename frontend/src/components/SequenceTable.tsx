import { useState, useMemo } from 'react';
import { CopyableDigest } from './CopyableDigest';
import { CliCommand } from './CliSnippet';
import { Icon } from './common/Icon';
import { BaseModal } from './common/BaseModal';
import { cn } from '../utils/cn';
import type { SequenceRow } from '../types';

const PAGE_SIZE = 50;

interface SequenceTableProps {
  sequences: SequenceRow[];
  /** Store URL, for the code snippets in the detail modal. */
  storeUrl?: string | null;
  /** Make the column headers clickable to sort. */
  sortable?: boolean;
}

/** Paginated sequence table with a detail modal. */
const SequenceTable = ({ sequences, storeUrl, sortable = false }: SequenceTableProps) => {
  const [page, setPage] = useState(0);
  const [selectedSeq, setSelectedSeq] = useState<SequenceRow | null>(null);
  const [codeTab, setCodeTab] = useState<'cli' | 'python'>('cli');
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  const handleSort = (col: string) => {
    if (!sortable) return;
    if (sortCol === col) setSortAsc(!sortAsc);
    else { setSortCol(col); setSortAsc(true); }
    setPage(0);
  };

  const sorted = useMemo(() => {
    if (!sortable || !sortCol) return sequences;
    return [...sequences].sort((a, b) => {
      const va = a[sortCol];
      const vb = b[sortCol];
      if (typeof va === 'number' && typeof vb === 'number')
        return sortAsc ? va - vb : vb - va;
      return sortAsc
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va));
    });
  }, [sequences, sortCol, sortAsc, sortable]);

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const paged = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  // Plain render helper (not a component) so it isn't re-created as a new
  // component type on every render.
  const renderSortIcon = (col: string) => {
    if (!sortable || sortCol !== col) return null;
    return <Icon name={sortAsc ? 'caret-up' : 'caret-down'} className='ml-1' />;
  };

  const thClass = sortable ? 'cursor-pointer' : undefined;

  return (
    <>
      <div className="table-wrap">
        <table className="table table--sm table--hover mb-0">
          <thead>
            <tr>
              <th className={thClass} onClick={() => handleSort('name')}>
                Name{renderSortIcon('name')}
              </th>
              <th className={cn('text-right', thClass)} onClick={() => handleSort('length')}>
                Length{renderSortIcon('length')}
              </th>
              <th className={thClass} onClick={() => handleSort('sha512t24u')}>
                SHA-512/24u{renderSortIcon('sha512t24u')}
              </th>
              <th className="table__cell--shrink"></th>
            </tr>
          </thead>
          <tbody>
            {paged.map((seq, i) => (
              <tr key={`${seq.sha512t24u}-${i}`}>
                <td>{seq.name}</td>
                <td className="text-right font-mono">{seq.length.toLocaleString()}</td>
                <td><CopyableDigest value={seq.sha512t24u ?? ''} /></td>
                <td>
                  <button
                    className="btn btn--xs btn--outline-secondary"
                    title="View details"
                    onClick={() => setSelectedSeq(seq)}
                  >
                    <Icon name="three-dots" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="card__footer">
          <nav>
            <ul className="pagination justify-center mb-0">
              <li>
                <button
                  className={cn('pagination__page', page === 0 && 'pagination__page--disabled')}
                  disabled={page === 0}
                  onClick={() => setPage(page - 1)}
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
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </button>
              </li>
            </ul>
          </nav>
        </div>
      )}

      {/* Sequence detail modal */}
      {selectedSeq && (
        <BaseModal
          isOpen
          onClose={() => setSelectedSeq(null)}
          title={selectedSeq.name ?? 'Sequence'}
          size="lg"
        >
          <table className="table table--sm mb-6">
            <tbody>
              <tr>
                <td className="text-muted">Length</td>
                <td className="font-mono">{selectedSeq.length.toLocaleString()}</td>
              </tr>
              <tr>
                <td className="text-muted">Alphabet</td>
                <td><span className="badge badge--secondary">{selectedSeq.alphabet}</span></td>
              </tr>
              <tr>
                <td className="text-muted">SHA-512/24u</td>
                <td><CopyableDigest value={selectedSeq.sha512t24u ?? ''} /></td>
              </tr>
              <tr>
                <td className="text-muted">MD5</td>
                <td><CopyableDigest value={selectedSeq.md5 ?? ''} /></td>
              </tr>
              {selectedSeq.description && (
                <tr>
                  <td className="text-muted">Description</td>
                  <td className="text-sm">{selectedSeq.description}</td>
                </tr>
              )}
            </tbody>
          </table>
          {storeUrl && (
            <>
              <h6 className="text-muted mb-2">Code</h6>
              <ul className="tabs tabs--pills mb-4">
                <li>
                  <button
                    className={cn('tab', codeTab === 'cli' && 'tab--active')}
                    onClick={() => setCodeTab('cli')}
                  >
                    CLI
                  </button>
                </li>
                <li>
                  <button
                    className={cn('tab', codeTab === 'python' && 'tab--active')}
                    onClick={() => setCodeTab('python')}
                  >
                    Python
                  </button>
                </li>
              </ul>
              <small className="text-muted block mb-1 text-sm">Get sequence</small>
              <CliCommand
                command={
                  codeTab === 'cli'
                    ? `refget store get --sequence \\\n  ${selectedSeq.sha512t24u} \\\n  --remote ${storeUrl}`
                    : `import refget\n\nstore = refget.RefgetStore("${storeUrl}")\nstore.get("${selectedSeq.sha512t24u}", sequence=True)`
                }
              />
            </>
          )}
        </BaseModal>
      )}
    </>
  );
};

export { SequenceTable };
