import { useState } from 'react';
import { copyToClipboard } from '../../utilities';
import { Icon } from '../common/Icon';
import type { SeqColDigestResult } from '../../types';

interface SeqColResultProps {
  result: SeqColDigestResult | null;
  fileName: string | null;
  onCompare: () => void;
  onDownloadJson: (level: 'level1' | 'level2' | 'uncollated') => void;
  onDownloadRgsi: () => void;
  onCopyJson: () => void;
}

export default function SeqColResult({
  result,
  fileName,
  onCompare,
  onDownloadJson,
  onDownloadRgsi,
  onCopyJson,
}: SeqColResultProps) {
  // The Bootstrap dropdown plugin is gone; the JSON menu is React state now.
  const [jsonMenuOpen, setJsonMenuOpen] = useState(false);

  if (!result) return null;

  return (
    <div className="card mt-6">
      <div className="card__header flex justify-between items-center">
        <div>
          <strong>Sequence Collection</strong>
          <span className="text-muted ml-2">({fileName})</span>
        </div>
        <div className="btn-group">
          <button
            className="btn btn--outline-primary"
            onClick={onCompare}
            title="Compare with database"
          >
            <Icon name="arrow-left-right" className="mr-1" />
            Compare
          </button>
          <button
            className="btn btn--outline-secondary"
            onClick={onCopyJson}
            title="Copy JSON to clipboard"
          >
            <Icon name="clipboard" className="mr-1" />
            Copy JSON
          </button>
          <div className="dropdown">
            <button
              type="button"
              className="btn btn--outline-secondary"
              aria-expanded={jsonMenuOpen}
              onClick={() => setJsonMenuOpen((open) => !open)}
              title="Download as JSON"
            >
              <Icon name="download" className="mr-1" />
              JSON
              <Icon name="caret-down" />
            </button>
            {jsonMenuOpen && (
              <ul className="dropdown__menu">
                <li>
                  <button
                    className="dropdown__item"
                    onClick={() => {
                      setJsonMenuOpen(false);
                      onDownloadJson('level2');
                    }}
                  >
                    Level 2 (arrays)
                  </button>
                </li>
                <li>
                  <button
                    className="dropdown__item"
                    onClick={() => {
                      setJsonMenuOpen(false);
                      onDownloadJson('uncollated');
                    }}
                  >
                    Uncollated (records)
                  </button>
                </li>
                <li>
                  <button
                    className="dropdown__item"
                    onClick={() => {
                      setJsonMenuOpen(false);
                      onDownloadJson('level1');
                    }}
                  >
                    Level 1 (digests)
                  </button>
                </li>
              </ul>
            )}
          </div>
          <button
            className="btn btn--outline-secondary"
            onClick={onDownloadRgsi}
            title="Download as RGSI"
          >
            <Icon name="download" className="mr-1" />
            RGSI
          </button>
        </div>
      </div>
      <div className="card__body">
        {/* Main digest */}
        <div className="mb-4">
          <label className="form-label text-muted text-sm">Collection Digest</label>
          <div className="flex items-center gap-2">
            <code className="text-lg select-all">{result.digest}</code>
            <button
              className="btn btn--sm btn--outline-secondary"
              onClick={() => copyToClipboard(result.digest)}
              title="Copy digest"
            >
              <Icon name="clipboard" />
            </button>
            <a
              href={`/collection/${result.digest}`}
              className="btn btn--sm btn--outline-primary"
              title="Look up in database"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Icon name="database" className="mr-1" />
              Lookup
            </a>
          </div>
        </div>

        {/* Level 1 digests */}
        <div className="mb-4">
          <label className="form-label text-muted text-sm">Level 1 Digests</label>
          <table className="table table--sm mb-0">
            <tbody>
              <tr>
                <td className="text-muted">names</td>
                <td><code className="code code--inline">{result.names_digest}</code></td>
              </tr>
              <tr>
                <td className="text-muted">sequences</td>
                <td><code className="code code--inline">{result.sequences_digest}</code></td>
              </tr>
              <tr>
                <td className="text-muted">lengths</td>
                <td><code className="code code--inline">{result.lengths_digest}</code></td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Sequences */}
        <div>
          <label className="form-label text-muted text-sm">
            Sequences ({result.n_sequences})
          </label>
          <div className="scroll-panel">
            <table className="table table--sm table--striped mb-0">
              <thead className="sticky bg-surface">
                <tr>
                  <th>Name</th>
                  <th>Length</th>
                  <th>Alphabet</th>
                  <th>SHA512t24u</th>
                </tr>
              </thead>
              <tbody>
                {result.sequences.map((seq, i) => (
                  <tr key={i}>
                    <td>{seq.name}</td>
                    <td>{seq.length.toLocaleString()}</td>
                    <td><span className="badge badge--secondary">{seq.alphabet}</span></td>
                    <td><code className="code text-sm">{seq.sha512t24u}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
