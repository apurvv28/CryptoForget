import { useState } from 'react';
import { api } from '../api/client';
import Icon from '../../components/Icon';
import PipelineRail from '../../components/PipelineRail';
import { ErrorState } from '../../components/States';
import { useLatestCertificate } from '../../hooks/useLatestCertificate';
import { Link } from '../router/router';
import { useApp } from '../state/AppState';

function Fact({ label, children }) {
  return (
    <div className="cf-fact">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function DemoControls() {
  const { refreshUser, refreshUsers } = useApp();
  const [step, setStep] = useState('idle'); // idle | confirm | running | done | error
  const [message, setMessage] = useState('');

  const run = async () => {
    setStep('running');
    try {
      const res = await api.resetAllDeletions();
      await Promise.all([refreshUsers(), refreshUser()]);
      setMessage(res?.message || 'Demo state restored.');
      setStep('done');
    } catch (err) {
      setMessage(err.message);
      setStep('error');
    }
  };

  return (
    <section className="cf-card cf-stack-sm cf-demo">
      <h2>Demo controls</h2>
      <p>
        Restores consent for <strong>every</strong> demo user, deletes all deletion requests and
        certificates from the database, and logs an audit event. Ledger blocks are kept. It does not
        restore the unlearning engine's shard data, so forgetting the same user again before the
        backend restarts finds nothing left to remove.
      </p>

      {step === 'idle' && (
        <div>
          <button type="button" className="cf-btn cf-btn--ghost" onClick={() => setStep('confirm')}>
            Reset demo state…
          </button>
        </div>
      )}
      {step === 'confirm' && (
        <div className="cf-actions">
          <button type="button" className="cf-btn cf-btn--danger" onClick={run}>
            Yes, reset for all users
          </button>
          <button type="button" className="cf-btn cf-btn--ghost" onClick={() => setStep('idle')}>
            Cancel
          </button>
        </div>
      )}
      {step === 'running' && <p>Resetting…</p>}
      {(step === 'done' || step === 'error') && (
        <div className={`cf-notice ${step === 'done' ? 'cf-notice--ok' : 'cf-notice--danger'}`}>
          <div>
            {message}{' '}
            <button type="button" className="cf-linkbtn" onClick={() => setStep('idle')}>
              Dismiss
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

export default function PrivacyPage() {
  const { user, userId, userError, personalization, clicks, backendClickTotal } = useApp();
  const cert = useLatestCertificate();

  if (personalization === 'unavailable') {
    return (
      <ErrorState
        title="API offline"
        message="Start the backend to read your consent state."
      />
    );
  }
  if (userError) {
    return <ErrorState title={`Could not load ${userId}`} message={userError} />;
  }

  const on = personalization === 'on';
  const off = personalization === 'off';
  const tone = on ? 'on' : off ? 'off' : 'idle';

  return (
    <div>
      <header className="cf-page-head">
        <h1>Privacy &amp; consent</h1>
        <p>
          The consent state the backend holds for <strong>{userId}</strong>, and what the
          recommendation model learns from.
        </p>
      </header>

      <PipelineRail current="/privacy" />

      <div className="cf-stack">
        <section className={`cf-card cf-consent cf-consent--${tone}`}>
          <span className="cf-consent__icon">
            <Icon name={off ? 'shield-check' : 'lock'} size={24} />
          </span>
          <div className="cf-stack-sm">
            <h2>
              {on && 'Personalization is on'}
              {off && 'Personalization is off'}
              {!on && !off && 'Checking your consent state…'}
            </h2>
            <p>
              {on &&
                'Articles you open are sent to the recommendation model as clicks, and your feed is ranked using your profile.'}
              {off &&
                'This user was forgotten. Feeds skip the recommendation model and no new clicks are sent.'}
              {!on && !off && 'Reading the state from the backend.'}
            </p>
            <div className="cf-actions">
              {on && (
                <Link to="/forget" className="cf-btn cf-btn--danger">
                  Forget my data
                </Link>
              )}
              {off && (
                <>
                  <Link to="/status" className="cf-btn cf-btn--soft">
                    Unlearning status
                  </Link>
                  <Link to="/verification" className="cf-btn cf-btn--ghost">
                    View verification
                  </Link>
                </>
              )}
            </div>
            <p className="cf-fine">
              The API offers one consent action: Forget. There is no per-user switch to turn
              personalization back on.
            </p>
          </div>
        </section>

        <div className="cf-two">
          <section className="cf-card cf-stack-sm">
            <h2>Backend record</h2>
            <dl className="cf-facts">
              <Fact label="Demo user">{userId}</Fact>
              <Fact label="Name (generated persona)">{user?.name ?? '—'}</Fact>
              <Fact label="Consent">
                {user ? (
                  <span className={`cf-chip ${user.consent_status === false ? 'cf-chip--warn' : 'cf-chip--ok'}`}>
                    {user.consent_status === false ? 'Withdrawn' : 'Granted'}
                  </span>
                ) : (
                  '—'
                )}
              </Fact>
              <Fact label="Forgotten">
                {user ? (user.is_unlearned ? 'Yes' : 'No') : '—'}
              </Fact>
              <Fact label="Data shard">{user?.shard_id ?? '—'}</Fact>
              <Fact label="Deletion certificate">
                {cert.status === 'ready' && (
                  <Link to="/verification" className="cf-linkbtn">
                    {cert.certificate.certificate_id}
                  </Link>
                )}
                {cert.status === 'none' && 'None issued'}
                {cert.status === 'loading' && '…'}
                {cert.status === 'error' && 'Unavailable'}
              </Fact>
            </dl>
          </section>

          <section className="cf-card cf-stack-sm">
            <h2>Interaction data</h2>
            <dl className="cf-facts">
              <Fact label="Clicks sent from this browser">{clicks.length}</Fact>
              <Fact label="Clicks the backend reports">
                {backendClickTotal ?? 'Known after you open an article'}
              </Fact>
            </dl>
            <p className="cf-fine">
              The browser log is a local copy of the clicks this UI sent. It is cleared when you
              forget your data.
            </p>
          </section>
        </div>

        <section className="cf-card cf-stack-sm">
          <h2>What the recommendation model learns from</h2>
          <div className="cf-two">
            <div>
              <h3 className="cf-h3">Used</h3>
              <ul className="cf-list cf-list--yes">
                <li>Articles you clicked, as your long-term history</li>
                <li>When you clicked, so recent clicks count more (24-hour short-term window)</li>
                <li>Each article's title, abstract and category</li>
              </ul>
            </div>
            <div>
              <h3 className="cf-h3">Not used</h3>
              <ul className="cf-list cf-list--no">
                <li>Likes and dislikes</li>
                <li>Saves and bookmarks</li>
                <li>Shares</li>
                <li>Dwell time or reading duration</li>
              </ul>
            </div>
          </div>
        </section>

        <DemoControls />
      </div>
    </div>
  );
}