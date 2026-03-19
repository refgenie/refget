import { useState } from 'react';

/**
 * A monospace digest string with a clipboard icon that changes to a check on copy.
 */
const CopyableDigest = ({ value }) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = (e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <span className="font-monospace small">
      {value}
      <i
        className={`bi ${copied ? 'bi-check-lg text-success' : 'bi-clipboard'} ms-2`}
        role="button"
        title="Copy to clipboard"
        onClick={handleCopy}
        style={{ cursor: 'pointer' }}
      />
    </span>
  );
};

export { CopyableDigest };
