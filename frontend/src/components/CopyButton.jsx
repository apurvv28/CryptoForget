import { useState } from 'react';

export function CopyButton({ value, label = 'Copy value' }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <button type="button" className="cf-copy" onClick={copy} aria-label={label}>
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

export function HashValue({ value, head = 12, tail = 8, full = false }) {
  if (!value) return <span className="cf-muted">—</span>;
  const text = String(value);
  const shown =
    full || text.length <= head + tail + 1 ? text : `${text.slice(0, head)}…${text.slice(-tail)}`;

  return (
    <span className="cf-hash">
      <code title={text}>{shown}</code>
      <CopyButton value={text} />
    </span>
  );
}