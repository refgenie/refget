import { useState } from 'react';
import { Icon } from './common/Icon';
import { BaseModal } from './common/BaseModal';
import { cn } from '../utils/cn';

/**
 * A copyable CLI command snippet.
 * Shows a monospace command with a copy button.
 */
const CliCommand = ({ command }: { command: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(command).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  return (
    <div className="flex items-start mb-1">
      <pre className="cli-command flex-grow text-left mb-0">
        <code>{command}</code>
      </pre>
      <button
        className="btn--link text-muted ml-2 mt-1"
        onClick={handleCopy}
        title="Copy to clipboard"
      >
        <Icon name={copied ? 'check' : 'clipboard'} className={copied ? 'text-success-fg' : undefined} />
      </button>
    </div>
  );
};

export interface CliCommandEntry {
  label?: string;
  command: string;
}

/** A collapsible panel of CLI commands for a given context. */
const CliSnippet = ({ commands }: { commands?: CliCommandEntry[] }) => {
  const [open, setOpen] = useState(false);

  if (!commands || commands.length === 0) return null;

  return (
    <div className="mt-4">
      <button
        className="btn btn--sm btn--outline-secondary"
        onClick={() => setOpen(!open)}
      >
        <Icon name="terminal" className="mr-1" />
        CLI
        <Icon name={open ? 'chevron-down' : 'chevron-right'} />
      </button>
      {open && (
        <div className="mt-2 p-4 bg-surface-muted rounded border">
          {commands.map(({ label, command }, i) => (
            <div key={i} className="mb-2">
              {label && <small className="text-muted block mb-1 text-sm">{label}</small>}
              <CliCommand command={command} />
            </div>
          ))}
          <small className="text-muted block mt-2 text-sm">
            Install: <code className="code code--inline">pip install refget</code>
          </small>
        </div>
      )}
    </div>
  );
};

export interface CodeSnippet {
  label?: string;
  cli: string;
  python: string;
}

/** A small icon button for table rows that opens a modal with CLI/Python snippets. */
const RowCodeButton = ({
  snippets,
  title = 'Code',
}: {
  snippets: CodeSnippet[];
  title?: string;
}) => {
  const [show, setShow] = useState(false);
  const [tab, setTab] = useState<'cli' | 'python'>('cli');

  return (
    <>
      <button
        className="btn--link text-muted"
        onClick={() => setShow(true)}
        title={title}
      >
        <Icon name="code" />
      </button>
      <BaseModal isOpen={show} onClose={() => setShow(false)} title={title} size="lg">
        <ul className="tabs tabs--pills mb-4">
          <li>
            <button
              className={cn('tab', tab === 'cli' && 'tab--active')}
              onClick={() => setTab('cli')}
            >
              <Icon name="terminal" className="mr-1" />
              CLI
            </button>
          </li>
          <li>
            <button
              className={cn('tab', tab === 'python' && 'tab--active')}
              onClick={() => setTab('python')}
            >
              <Icon name="python" className="mr-1" />
              Python
            </button>
          </li>
        </ul>
        {snippets.map((snippet, i) => (
          <div key={i} className={i < snippets.length - 1 ? 'mb-4' : ''}>
            {snippet.label && (
              <small className="text-muted block mb-1 text-sm">{snippet.label}</small>
            )}
            <CliCommand command={snippet[tab]} />
          </div>
        ))}
      </BaseModal>
    </>
  );
};

export { CliSnippet, CliCommand, RowCodeButton };
