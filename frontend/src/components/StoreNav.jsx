import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useExplorerStore } from '../stores/explorerStore.js';
import { CliCommand } from './CliSnippet.jsx';

const StoreNav = ({ active, storeUrlParam, collectionDigest }) => {
  const [showCode, setShowCode] = useState(false);
  const [codeTab, setCodeTab] = useState('cli');
  const { storeUrl } = useExplorerStore();

  const remote = storeUrl || new URLSearchParams(storeUrlParam).get('url') || '';

  const items = [
    { key: 'overview', label: 'Overview', path: '/explore/store', icon: 'bi-house' },
    { key: 'sequences', label: 'Sequences', path: '/explore/store/sequences', icon: 'bi-list-ol' },
    { key: 'aliases', label: 'Aliases', path: '/explore/store/aliases', icon: 'bi-tag' },
  ];

  const snippetGroups = [
    {
      heading: 'Setup',
      snippets: [
        {
          label: 'Subscribe to this remote store',
          cli: `refget config add store \\
  ${remote}`,
          python: `import refget

refget.config.add("store", "${remote}")`,
        },
      ],
    },
    {
      heading: 'Browse',
      snippets: [
        {
          label: 'List collections',
          cli: `refget store list \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.list()`,
        },
        {
          label: 'List sequences',
          cli: `refget store list --sequences \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.list(sequences=True)`,
        },
        {
          label: 'Store statistics',
          cli: `refget store stats \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
print(store)`,
        },
      ],
    },
  ];

  if (collectionDigest) {
    snippetGroups.push({
      heading: 'Collection',
      snippets: [
        {
          label: 'Get collection metadata',
          cli: `refget store get \\
  ${collectionDigest} \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.get("${collectionDigest}")`,
        },
        {
          label: 'Pull collection to local cache',
          cli: `refget store pull \\
  ${collectionDigest} \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.pull("${collectionDigest}")`,
        },
        {
          label: 'Export as FASTA',
          cli: `refget store export \\
  ${collectionDigest} \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.export("${collectionDigest}")`,
        },
        {
          label: 'Generate .fai index',
          cli: `refget store fai \\
  ${collectionDigest} \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.fai("${collectionDigest}")`,
        },
        {
          label: 'Generate chrom.sizes',
          cli: `refget store chrom-sizes \\
  ${collectionDigest} \\
  --remote ${remote}`,
          python: `import refget

store = refget.RefgetStore("${remote}")
store.chrom_sizes("${collectionDigest}")`,
        },
      ],
    });
  }

  return (
    <div className="mb-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4 className="fw-light mb-0">
          <i className="bi bi-archive me-2" />
          RefgetStore Explorer
        </h4>
        <div>
          <button
            className="btn btn-sm btn-outline-secondary me-2"
            onClick={() => setShowCode(true)}
          >
            <i className="bi bi-code-slash me-1" />
            Code
          </button>
          <Link to="/explore" className="btn btn-sm btn-outline-secondary">
            <i className="bi bi-arrow-left me-1" />
            Change Store
          </Link>
        </div>
      </div>

      {/* Code Snippets Modal */}
      {showCode && (
        <>
          <div className="modal-backdrop fade show" onClick={() => setShowCode(false)} />
          <div className="modal fade show d-block" tabIndex="-1" onClick={() => setShowCode(false)}>
            <div className="modal-dialog modal-lg" onClick={(e) => e.stopPropagation()}>
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">
                    <i className="bi bi-code-slash me-2" />
                    Code Snippets
                  </h5>
                  <button type="button" className="btn-close" onClick={() => setShowCode(false)} />
                </div>
                <div className="modal-body">
                  <ul className="nav nav-pills mb-3">
                    <li className="nav-item">
                      <button
                        className={`nav-link ${codeTab === 'cli' ? 'active' : ''}`}
                        onClick={() => setCodeTab('cli')}
                      >
                        <i className="bi bi-terminal me-1" />
                        CLI
                      </button>
                    </li>
                    <li className="nav-item">
                      <button
                        className={`nav-link ${codeTab === 'python' ? 'active' : ''}`}
                        onClick={() => setCodeTab('python')}
                      >
                        <i className="bi bi-filetype-py me-1" />
                        Python
                      </button>
                    </li>
                  </ul>

                  {snippetGroups.map((group, gi) => (
                    <div key={gi} className={gi < snippetGroups.length - 1 ? 'mb-4' : ''}>
                      <h6 className="text-muted mb-2">{group.heading}</h6>
                      {group.snippets.map((snippet, i) => (
                        <div key={i} className={i < group.snippets.length - 1 ? 'mb-3' : ''}>
                          <small className="text-muted d-block mb-1">{snippet.label}</small>
                          <CliCommand command={snippet[codeTab]} />
                        </div>
                      ))}
                    </div>
                  ))}
                  <hr />
                  <small className="text-muted">
                    Install: <code>pip install refget</code>
                  </small>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      <ul className="nav nav-tabs mb-3">
        {items.map((item) => (
          <li className="nav-item" key={item.key}>
            <Link
              to={`${item.path}${storeUrlParam}`}
              className={`nav-link ${active === item.key ? 'active' : ''}`}
            >
              <i className={`bi ${item.icon} me-1`} />
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
};

export { StoreNav };
