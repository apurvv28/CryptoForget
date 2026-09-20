import { useState } from 'react';
import { api } from '../api/client';
import PipelineRail from '../../components/PipelineRail';
import { ErrorState } from '../../components/States';
import { Link, navigate } from '../router/router';
import { useApp } from '../state/AppState';

const PATHS = [
  {
    id: 'Path B',
    title: 'Path B: SISA shard retraining',
    text: 'Post-training. Removes the user from the affected SISA shard and runs the shard retraining step. This is the backend default.',
  },
  {
    id: 'Path A',
    title: 'Path A: Pre-training tombstoning',
    text: 'Removes the user from the shard partition before training, so their history is excluded. No shard retraining step.',
  },
];

const BACKEND_STEPS = [
  'Locates the user in their SISA shard.',
  'Runs the chosen path and removes the user from that shard.',
  'Withdraws consent and turns personalization off for the user.',
  'Signs a deletion certificate (ECDSA) that includes a Merkle proof.',
  'Appends a block to the hash-chained audit ledger.',
];

export default function ForgetPage() {
  const { userId, personalization, refreshUser, refreshUsers, clearClickLog } = useApp();
  const [path, setPath] = useState('Path B');
  const [confirmed, setConfirmed] = useState(false);
  const [phase, setPhase] = useState('idle'); // idle | submitting | error
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    if (!confirmed || phase === 'submitting') return;
    setPhase('submitting');
    setError('');
    try {
      const res = await api.deleteUser({ userId, deletionType: path });
      clearClickLog();
      await Promise.all([refreshUser(), refreshUsers()]);
      const requestId = res.certificate?.request_id;
      navigate(requestId ? `/status?request=${encodeURIComponent(requestId)}` : '/status');
    } catch (err) {
      setError(err.message);
      setPhase('error');
    }
  };

  if (personalization === 'unavailable') {
    return <ErrorState title="API offline" message="Start the backend to submit a request." />;
  }

  return (
    <div>
      <header className="cf-page-head">
        <h1>Forget my data</h1>
        <p>
          Ask CryptoForget to remove <strong>{userId}</strong> from the recommendation system. The
          backend runs the unlearning step and returns a signed certificate you can verify.
        </p>
      </header>

      <PipelineRail current="/forget" />

      {personalization === 'off' ? (
        <section className="cf-card cf-stack-sm">
          <h2>{userId} has already been forgotten</h2>
          <p>
            Personalization is off for this user. You can review the request and check the
            certificate.
          </p>
          <div className="cf-actions">
            <Link to="/status" className="cf-btn cf-btn--soft">
              Unlearning status
            </Link>
            <Link to="/verification" className="cf-btn cf-btn--ghost">
              View verification
            </Link>
          </div>
        </section>
      ) : (
        <div className="cf-two cf-two--wide">
          <form className="cf-card cf-stack" onSubmit={submit}>
            <fieldset className="cf-fieldset" disabled={phase === 'submitting'}>
              <legend>Choose the unlearning path</legend>
              {PATHS.map((p) => (
                <label key={p.id} className={`cf-choice ${path === p.id ? 'is-selected' : ''}`}>
                  <input
                    type="radio"
                    name="path"
                    value={p.id}
                    checked={path === p.id}
                    onChange={() => setPath(p.id)}
                  />
                  <span className="cf-choice__text">
                    <strong>{p.title}</strong>
                    <span>{p.text}</span>
                  </span>
                </label>
              ))}
            </fieldset>

            <label className="cf-check">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />
              <span>
                I understand that personalization will be turned off for {userId} and that this can't
                be undone from this screen.
              </span>
            </label>

            {phase === 'error' && (
              <div className="cf-notice cf-notice--danger" role="alert">
                <div>
                  <strong>The request failed.</strong> {error}
                </div>
              </div>
            )}

            <div>
              <button
                type="submit"
                className="cf-btn cf-btn--danger"
                disabled={!confirmed || phase === 'submitting' || personalization !== 'on'}
              >
                {phase === 'submitting' ? 'Submitting request…' : `Forget ${userId}`}
              </button>
            </div>
          </form>

          <aside className="cf-card cf-stack-sm">
            <h2>What the backend does</h2>
            <ol className="cf-steps">
              {BACKEND_STEPS.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ol>
            <p className="cf-fine">
              The request runs synchronously. When it finishes you are taken to the real status and
              certificate returned by the API.
            </p>
          </aside>
        </div>
      )}
    </div>
  );
}