import { useState } from 'react';
import type { MouseEvent } from 'react';
import { Icon } from './common/Icon';

interface CopyableDigestProps {
  value: string;
}

/**
 * A monospace digest string with a clipboard icon that changes to a check on copy.
 */
const CopyableDigest = ({ value }: CopyableDigestProps) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = (e: MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <span className="font-mono text-sm">
      {value}
      <button
        type="button"
        className={copied ? 'btn--link ml-2 text-success-fg' : 'btn--link ml-2'}
        title="Copy to clipboard"
        onClick={handleCopy}
      >
        <Icon name={copied ? 'check' : 'clipboard'} />
      </button>
    </span>
  );
};

export { CopyableDigest };
