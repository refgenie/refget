import { useState } from 'react';

/**
 * A copyable CLI command snippet.
 * Shows a monospace command with a copy button.
 */
const CliCommand = ({ command }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(command).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  return (
    <div className="d-flex align-items-start mb-1">
      <pre className="bg-light px-2 py-1 rounded flex-grow-1 small mb-0 text-start" style={{ whiteSpace: 'pre-wrap' }}><code>{command}</code></pre>
      <button
        className="btn btn-sm btn-link text-muted p-0 ms-2 mt-1"
        onClick={handleCopy}
        title="Copy to clipboard"
      >
        <i className={`bi ${copied ? 'bi-check-lg text-success' : 'bi-clipboard'}`} />
      </button>
    </div>
  );
};

/**
 * A collapsible panel of CLI commands for a given context.
 * Props:
 *   commands: [{label, command}]
 */
const CliSnippet = ({ commands }) => {
  const [open, setOpen] = useState(false);

  if (!commands || commands.length === 0) return null;

  return (
    <div className="mt-3">
      <button
        className="btn btn-sm btn-outline-secondary"
        onClick={() => setOpen(!open)}
      >
        <i className={`bi bi-terminal me-1`} />
        CLI {open ? '▾' : '▸'}
      </button>
      {open && (
        <div className="mt-2 p-3 bg-light rounded border">
          {commands.map(({ label, command }, i) => (
            <div key={i} className="mb-2">
              {label && <small className="text-muted d-block mb-1">{label}</small>}
              <CliCommand command={command} />
            </div>
          ))}
          <small className="text-muted d-block mt-2">
            Install: <code>pip install refget</code>
          </small>
        </div>
      )}
    </div>
  );
};

/**
 * A small icon button for table rows that opens a modal with CLI/Python snippets.
 * Props:
 *   snippets: [{ label, cli, python }]
 *   title: modal title
 */
const RowCodeButton = ({ snippets, title = 'Code' }) => {
  const [show, setShow] = useState(false);
  const [tab, setTab] = useState('cli');

  return (
    <>
      <button
        className="btn btn-sm btn-link text-muted p-0"
        onClick={() => setShow(true)}
        title={title}
      >
        <i className="bi bi-code-slash" />
      </button>
      {show && (
        <>
          <div className="modal-backdrop fade show" onClick={() => setShow(false)} />
          <div className="modal fade show d-block" tabIndex="-1" onClick={() => setShow(false)}>
            <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
              <div className="modal-content">
                <div className="modal-header py-2">
                  <h6 className="modal-title">
                    <i className="bi bi-code-slash me-2" />
                    {title}
                  </h6>
                  <button type="button" className="btn-close" onClick={() => setShow(false)} />
                </div>
                <div className="modal-body">
                  <ul className="nav nav-pills nav-pills-sm mb-3">
                    <li className="nav-item">
                      <button
                        className={`nav-link py-1 px-2 ${tab === 'cli' ? 'active' : ''}`}
                        onClick={() => setTab('cli')}
                      >
                        <i className="bi bi-terminal me-1" />
                        CLI
                      </button>
                    </li>
                    <li className="nav-item">
                      <button
                        className={`nav-link py-1 px-2 ${tab === 'python' ? 'active' : ''}`}
                        onClick={() => setTab('python')}
                      >
                        <i className="bi bi-filetype-py me-1" />
                        Python
                      </button>
                    </li>
                  </ul>
                  {snippets.map((snippet, i) => (
                    <div key={i} className={i < snippets.length - 1 ? 'mb-3' : ''}>
                      {snippet.label && <small className="text-muted d-block mb-1">{snippet.label}</small>}
                      <CliCommand command={snippet[tab]} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
};

export { CliSnippet, CliCommand, RowCodeButton };
