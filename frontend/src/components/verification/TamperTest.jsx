import { useState } from 'react';
import { api } from '../../cryptoforge/api/client';
import { ResultBanner } from './VerdictCard';

const FIELDS = [
  { id: 'user_id', label: 'User id' },
  { id: 'new_merkle_root', label: 'New Merkle root' },
  { id: 'new_model_hash', label: 'New model hash' },
];

function alter(certificate, field) {
  const value = String(certificate[field] ?? '');
  if (field === 'user_id') return { ...certificate, user_id: `${value}x` };
  return { ...certificate, [field]: `${value[0] === '0' ? '1' : '0'}${value.slice(1)}` };
}

export default function TamperTest({ certificate }) {
  const [field, setField] = useState('user_id');
  const [state, setState] = useState({ status: 'idle', result: null, error: null });

  const run = async () => {
    setState({ status: 'running', result: null, error: null });
    try {
      const result = await api.verifyCertificate(alter(certificate, field));
      setState({ status: 'done', result, error: null });
    } catch (err) {
      setState({ status: 'error', result: null, error: err.message });
    }
  };

  return (
    <section className="cf-card cf-stack-sm">
      <h2>Tamper test</h2>
      <p>
        Changes one field in a <strong>local copy</strong> of the certificate and sends it to the same
        verifier. Nothing is stored. The signature covers these fields, so the backend should reject
        the copy.
      </p>
      <div className="cf-inline">
        <label className="cf-selectwrap">
          <span className="cf-selectwrap__label">Field to change</span>
          <select className="cf-select" value={field} onChange={(e) => setField(e.target.value)}>
            {FIELDS.map((f) => (
              <option key={f.id} value={f.id}>
                {f.label}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="cf-btn cf-btn--soft"
          onClick={run}
          disabled={state.status === 'running'}
        >
          {state.status === 'running' ? 'Verifying…' : 'Alter and verify'}
        </button>
      </div>

      {state.status === 'error' && (
        <div className="cf-notice cf-notice--danger" role="alert">
          <div>{state.error}</div>
        </div>
      )}
      {state.status === 'done' && (
        <>
          <ResultBanner result={state.result} />
          <p className="cf-fine">
            {state.result.is_valid
              ? 'Unexpected: the backend accepted a modified certificate.'
              : 'This is the correct outcome for a modified certificate.'}
          </p>
        </>
      )}
    </section>
  );
}