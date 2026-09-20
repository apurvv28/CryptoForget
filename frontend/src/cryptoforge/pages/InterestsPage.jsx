import { useEffect, useMemo, useState } from 'react';
import RecencyChart from '../../components/RecencyChart';
import { EmptyState, ErrorState } from '../../components/States';
import Icon from '../../components/Icon';
import { useProfileProbe } from '../../hooks/useProfileProbe';
import { categoryLabel, timeAgo, toneFor } from '../lib/format';
import { MODEL_CONFIG, recencyWeight } from '../lib/modelConfig';
import { Link } from '../router/router';
import { useApp } from '../state/AppState';

function fusionSummary(probe) {
  if (probe.usedLong && probe.usedShort) {
    return `Both profiles exist, so they are fused with α = ${MODEL_CONFIG.alpha}.`;
  }
  if (probe.usedLong) return 'Only the long-term profile exists, so the dynamic profile equals it.';
  if (probe.usedShort) return 'Only the short-term profile exists, so the dynamic profile equals it.';
  return 'Neither profile exists yet, so every candidate scores 0 and the feed keeps its original order.';
}

export default function InterestsPage() {
  const { userId, personalization, clicks, backendClickTotal, clearClickLog } = useApp();
  const probe = useProfileProbe();
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 60000);
    return () => clearInterval(id);
  }, []);

  const items = useMemo(
    () =>
      clicks.map((c) => {
        const hours = Math.max(0, (now - new Date(c.at).getTime()) / 3600000);
        return {
          ...c,
          hours,
          inWindow: hours <= MODEL_CONFIG.windowHours,
          weight: recencyWeight(hours),
        };
      }),
    [clicks, now],
  );
  const inWindow = items.filter((i) => i.inWindow).length;

  const categories = useMemo(() => {
    const counts = new Map();
    items.forEach((i) => counts.set(i.category, (counts.get(i.category) || 0) + 1));
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6);
  }, [items]);

  const head = (
    <header className="cf-page-head">
      <h1>My interests</h1>
      <p>
        How the model sees <strong>{userId}</strong>: a long-term profile from clicked-article history,
        a short-term profile from recent clicks, fused into one dynamic profile.
      </p>
    </header>
  );

  if (personalization === 'unavailable') {
    return (
      <div>
        {head}
        <ErrorState title="API offline" message="Start the backend to read the profile state." />
      </div>
    );
  }

  if (personalization === 'off') {
    return (
      <div>
        {head}
        <section className="cf-card cf-stack-sm">
          <h2>No profile is in use for {userId}</h2>
          <p>
            This user was forgotten, so personalization is off and there is no interest profile to show.
          </p>
          <div className="cf-actions">
            <Link to="/verification" className="cf-btn cf-btn--soft">View verification</Link>
            <Link to="/privacy" className="cf-btn cf-btn--ghost">Privacy &amp; consent</Link>
          </div>
        </section>
      </div>
    );
  }

  const ready = probe.status === 'ready';
  const flag = (on, yes, no) =>
    ready ? (
      <span className={`cf-chip ${on ? 'cf-chip--ok' : 'cf-chip--warn'}`}>{on ? yes : no}</span>
    ) : (
      <span className="cf-chip">{probe.status === 'error' ? 'Unavailable' : 'Checking…'}</span>
    );

  return (
    <div>
      {head}

      {probe.status === 'error' && (
        <div className="cf-notice cf-notice--danger cf-mb" role="alert">
          <Icon name="alert" />
          <div>
            <strong>Could not read the profile state.</strong> {probe.error}{' '}
            <button type="button" className="cf-linkbtn" onClick={probe.refresh}>Retry</button>
          </div>
        </div>
      )}

      <div className="cf-trio">
        <section className="cf-card cf-profile">
          <span className="cf-profile__tag">Long-term profile</span>
          {flag(probe.usedLong, 'History found', 'No history')}
          <p>
            Built from the articles this user clicked in the MIND data, as TF-IDF vectors of the article
            text.
          </p>
        </section>

        <section className="cf-card cf-profile">
          <span className="cf-profile__tag">Short-term profile</span>
          {flag(probe.usedShort, 'Clicks recorded', 'No clicks yet')}
          <p>
            Built from clicks in the last {MODEL_CONFIG.windowHours} hours. Newer clicks count more.
          </p>
          <p className="cf-fine">
            This browser's log: {inWindow} of {items.length} click{items.length === 1 ? '' : 's'} inside the window.
            {ready && probe.usedShort && items.length === 0 && ' The backend holds clicks from another session.'}
          </p>
          {ready && !probe.usedShort && items.length > 0 && (
            <p className="cf-fine">
              The backend reports no clicks for {userId}, so its short-term profile is empty. Its click
              store is kept in memory and is cleared when the backend restarts.
            </p>
          )}
        </section>

        <section className="cf-card cf-profile cf-profile--fused">
          <span className="cf-profile__tag">Dynamic profile</span>
          <code className="cf-formula">α × long-term + (1 − α) × short-term</code>
          <p>{ready ? fusionSummary(probe) : 'Reading which profiles exist…'}</p>
          <p className="cf-fine">
            The backend defaults are α = {MODEL_CONFIG.alpha}, λ = {MODEL_CONFIG.decayRate} per hour and a{' '}
            {MODEL_CONFIG.windowHours}-hour window. The API does not report them, so these are documented
            values, not a live reading.
          </p>
        </section>
      </div>

      <section className="cf-section">
        <div className="cf-section-head">
          <h2>Your recent clicks and their weight</h2>
          {items.length > 0 && (
            <span className="cf-chip">
              {backendClickTotal != null
                ? `Backend reports ${backendClickTotal} click${backendClickTotal === 1 ? '' : 's'} for ${userId}`
                : `${items.length} click${items.length === 1 ? '' : 's'} sent from this browser`}
            </span>
          )}
        </div>

        {items.length === 0 ? (
          <EmptyState
            title="No clicks from this browser yet"
            action={<Link to="/" className="cf-btn cf-btn--soft">Open your feed</Link>}
          >
            Open a few articles and they appear here with the recency weight the model gives them.
          </EmptyState>
        ) : (
          <div className="cf-two cf-two--wide">
            <div className="cf-card">
              <RecencyChart clicks={items} />
            </div>

            <div className="cf-card cf-stack-sm">
              <h2>Latest clicks</h2>
              <ul className="cf-clicks">
                {items.slice(0, 8).map((c, i) => (
                  <li className="cf-click" key={`${c.news_id}-${c.at}-${i}`}>
                    <Link to={`/article/${encodeURIComponent(c.news_id)}`} className="cf-click__title">
                      {c.title}
                    </Link>
                    <div className="cf-click__meta">
                      <span className="cf-tag">{categoryLabel(c.category)}</span>
                      <span>{timeAgo(c.at)}</span>
                    </div>
                    <div className="cf-click__weight">
                      <span className={`cf-chip ${c.inWindow ? 'cf-chip--ok' : ''}`}>
                        {c.inWindow ? 'In window' : 'Not counted'}
                      </span>
                      <div className="cf-weightbar" aria-hidden="true">
                        <div style={{ width: `${c.inWindow ? c.weight * 100 : 0}%` }} />
                      </div>
                      <span className="cf-click__w">{c.inWindow ? c.weight.toFixed(2) : '—'}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </section>

      {items.length > 0 && (
        <section className="cf-section">
          <div className="cf-section-head">
            <h2>Categories you opened</h2>
          </div>
          <div className="cf-card cf-stack-sm">
            <ul className="cf-catbars">
              {categories.map(([cat, n]) => (
                <li key={cat}>
                  <span className="cf-catbars__name">{categoryLabel(cat)}</span>
                  <div className="cf-catbars__track">
                    <div style={{ width: `${(n / items.length) * 100}%`, background: toneFor(cat).fg }} />
                  </div>
                  <span className="cf-catbars__n">{n}</span>
                </li>
              ))}
            </ul>
            <p className="cf-fine">
              Counted from this browser's click log. It is a summary of your clicks, not the model's
              internal vector.
            </p>
            <div>
              <button type="button" className="cf-btn cf-btn--ghost" onClick={clearClickLog}>
                Clear this browser's click log
              </button>
            </div>
            <p className="cf-fine">Local only. Clicks already sent to the backend are not affected.</p>
          </div>
        </section>
      )}

      <div className="cf-notice cf-section">
        <Icon name="info" />
        <div>
          <strong>Backend capability missing.</strong> The API does not expose the profile vector, its
          top terms, or the length of the long-term history, so this page cannot show what the profile
          contains. It shows what the API reports plus this browser's click log.
        </div>
      </div>
    </div>
  );
}
