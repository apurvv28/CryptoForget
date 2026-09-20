import { useState } from 'react';
import { api } from '../../cryptoforge/api/client';
import { ResultBanner } from './VerdictCard';

export default function PasteVerify({ certificate }) {
  const [text, setText] = useState('');
  const [state, setState] = useState({ status: 'idle', result: null, error: null });

  const run = async () => {
    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch {
      setState({ status: 'error', result: null, error: 'That is not valid JSON.' });
      return;
    }
    setState({ status: 'running', result: null, error: null });
    try {
      const result = await api.verifyCertificate(parsed);
      setState({ status: 'done', result, error: null });
    } catch (err) {
      setState({ status: 'error', result: null, error: err.message });
    }
  };

  return (
    <section className="cf-card cf-stack-sm">
      <h2>Verify any certificate</h2>
      <p>
        Paste a deletion certificate (JSON) to check it independently, for example one downloaded by
        an auditor.
      </p>
      <textarea
        className="cf-textarea"
        rows={7}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder='{"certificate_id": "CERT-…", …}'
        aria-label="Certificate JSON"
        spellCheck={false}
      />
      <div className="cf-actions">
        <button
          type="button"
          className="cf-btn cf-btn--soft"
          onClick={run}
          disabled={!text.trim() || state.status === 'running'}
        >
          {state.status === 'running' ? 'Verifying…' : 'Verify pasted certificate'}
        </button>
        {certificate && (
          <button
            type="button"
            className="cf-btn cf-btn--ghost"
            onClick={() => setText(JSON.stringify(certificate, null, 2))}
          >
            Load the current certificate
          </button>
        )}
      </div>

      {state.status === 'error' && (
        <div className="cf-notice cf-notice--danger" role="alert">
          <div>{state.error}</div>
        </div>
      )}
      {state.status === 'done' && <ResultBanner result={state.result} />}
    </section>
  );
}