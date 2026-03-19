import { useState, useMemo } from 'react';
import { CopyableDigest } from './CopyableDigest.jsx';
import { CliCommand } from './CliSnippet.jsx';

const PAGE_SIZE = 50;

/**
 * Paginated sequence table with detail modal.
 *
 * Props:
 *   sequences: array of {name, length, sha512t24u, md5, alphabet, description}
 *   storeUrl: optional store URL for code snippets in modal
 *   sortable: if true, column headers are clickable to sort
 */
const SequenceTable = ({ sequences, storeUrl, sortable = false }) => {
  const [page, setPage] = useState(0);
  const [selectedSeq, setSelectedSeq] = useState(null);
  const [codeTab, setCodeTab] = useState('cli');
  const [sortCol, setSortCol] = useState(null);
  const [sortAsc, setSortAsc] = useState(true);

  const handleSort = (col) => {
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

  const SortIcon = ({ col }) => {
    if (!sortable || sortCol !== col) return null;
    return <i className={`bi bi-caret-${sortAsc ? 'up' : 'down'}-fill ms-1`} />;
  };

  const thStyle = sortable ? { cursor: 'pointer' } : {};

  return (
    <>
      <div className="table-responsive">
        <table className="table table-sm table-hover mb-0">
          <thead>
            <tr>
              <th style={thStyle} onClick={() => handleSort('name')}>
                Name<SortIcon col="name" />
              </th>
              <th className="text-end" style={thStyle} onClick={() => handleSort('length')}>
                Length<SortIcon col="length" />
              </th>
              <th style={thStyle} onClick={() => handleSort('sha512t24u')}>
                SHA-512/24u<SortIcon col="sha512t24u" />
              </th>
              <th style={{ width: '1%' }}></th>
            </tr>
          </thead>
          <tbody>
            {paged.map((seq, i) => (
              <tr key={`${seq.sha512t24u}-${i}`}>
                <td>{seq.name}</td>
                <td className="text-end font-monospace">{seq.length.toLocaleString()}</td>
                <td><CopyableDigest value={seq.sha512t24u} /></td>
                <td>
                  <button
                    className="btn btn-sm btn-outline-secondary py-0 px-1"
                    title="View details"
                    onClick={() => setSelectedSeq(seq)}
                  >
                    <i className="bi bi-three-dots" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="card-footer">
          <nav>
            <ul className="pagination pagination-sm justify-content-center mb-0">
              <li className={`page-item ${page === 0 ? 'disabled' : ''}`}>
                <button className="page-link" onClick={() => setPage(page - 1)}>Previous</button>
              </li>
              <li className="page-item disabled">
                <span className="page-link">Page {page + 1} of {totalPages}</span>
              </li>
              <li className={`page-item ${page >= totalPages - 1 ? 'disabled' : ''}`}>
                <button className="page-link" onClick={() => setPage(page + 1)}>Next</button>
              </li>
            </ul>
          </nav>
        </div>
      )}

      {/* Sequence detail modal */}
      {selectedSeq && (
        <>
          <div className="modal-backdrop fade show" onClick={() => setSelectedSeq(null)} />
          <div className="modal fade show d-block" tabIndex="-1" onClick={() => setSelectedSeq(null)}>
            <div className="modal-dialog modal-lg" onClick={(e) => e.stopPropagation()}>
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">{selectedSeq.name}</h5>
                  <button type="button" className="btn-close" onClick={() => setSelectedSeq(null)} />
                </div>
                <div className="modal-body">
                  <table className="table table-sm mb-4">
                    <tbody>
                      <tr>
                        <td className="text-muted">Length</td>
                        <td className="font-monospace">{selectedSeq.length.toLocaleString()}</td>
                      </tr>
                      <tr>
                        <td className="text-muted">Alphabet</td>
                        <td><span className="badge bg-secondary">{selectedSeq.alphabet}</span></td>
                      </tr>
                      <tr>
                        <td className="text-muted">SHA-512/24u</td>
                        <td><CopyableDigest value={selectedSeq.sha512t24u} /></td>
                      </tr>
                      <tr>
                        <td className="text-muted">MD5</td>
                        <td><CopyableDigest value={selectedSeq.md5} /></td>
                      </tr>
                      {selectedSeq.description && (
                        <tr>
                          <td className="text-muted">Description</td>
                          <td className="small">{selectedSeq.description}</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                  {storeUrl && (
                    <>
                      <h6 className="text-muted mb-2">Code</h6>
                      <ul className="nav nav-pills nav-pills-sm mb-3">
                        <li className="nav-item">
                          <button
                            className={`nav-link py-1 px-2 ${codeTab === 'cli' ? 'active' : ''}`}
                            onClick={() => setCodeTab('cli')}
                          >
                            CLI
                          </button>
                        </li>
                        <li className="nav-item">
                          <button
                            className={`nav-link py-1 px-2 ${codeTab === 'python' ? 'active' : ''}`}
                            onClick={() => setCodeTab('python')}
                          >
                            Python
                          </button>
                        </li>
                      </ul>
                      <small className="text-muted d-block mb-1">Get sequence</small>
                      <CliCommand
                        command={
                          codeTab === 'cli'
                            ? `refget store get --sequence \\\n  ${selectedSeq.sha512t24u} \\\n  --remote ${storeUrl}`
                            : `import refget\n\nstore = refget.RefgetStore("${storeUrl}")\nstore.get("${selectedSeq.sha512t24u}", sequence=True)`
                        }
                      />
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
};

export { SequenceTable };
