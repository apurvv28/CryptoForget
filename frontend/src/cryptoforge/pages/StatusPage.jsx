import { useEffect, useState } from 'react';
import { api } from '../api/client';
import PipelineRail from '../../components/PipelineRail';
import { EmptyState, ErrorState } from '../../components/States';
import { useLatestCertificate } from '../../hooks/useLatestCertificate';
import { formatDateTime } from '../lib/time';
import { Link, useLocation } from '../router/router';
import { useApp } from '../state/AppState';

function TimelineItem({ title, time, children }) {
  return (
    <li className="cf-timeline__item">
      <span className="cf-timeline__dot" aria-hidden="true" />
      <div>
        <div className="cf-timeline__head">
          <strong>{title}</strong>
          {time && <span className="cf-timeline__time">{time}</span>}
        </div>
        {children && <div className="cf-timeline__body">{children}</div>}
      </div>
    </li>
  );
}

// Asks the recommendation service what it still holds for this user.
function ServingCheck({ userId }) {
  const [state, setState] = useState({ status: 'idle' });

  const run = async () => {
    setState({ status: 'running' });
    try {
      const pool = await api.mindNews({ limit: 10 });
      const ids = (pool.articles || []).map((a) => a.news_id);
      if (ids.length === 0) throw new Error('No MIND articles were available to probe with.');
      const res = await api.recommend({ userId, candidateIds: ids, topK: ids.length });
      setState({ status: 'done', usedLong: res.used_long_term, usedShort: res.used_short_term });
    } catch (err) {
      setState({ status: 'error', message: err.message });
    }
  };

  const clean = state.status === 'done' && !state.usedLong && !state.usedShort;

  return (
    <section className="cf-card cf-stack-sm">
      <h2>Check the serving model</h2>
      <p>
        Asks the recommendation service whether it still finds a long-term history or recorded clicks
        for <strong>{userId}</strong>. This is a read-only call to <code>POST /recommend</code>.
      </p>
      <div>
        <button
          type="button"
          className="cf-btn cf-btn--ghost"
          onClick={run}
          disabled={state.status === 'running'}
        >
          {state.status === 'running' ? 'Checking…' : 'Run check'}
        </button>
      </div>

      {state.status === 'error' && (
        <div className="cf-notice cf-notice--danger" role="alert">
          <div>{state.message}</div>
        </div>
      )}
      {clean && (
        <div className="cf-notice cf-notice--ok">
          <div>
            <strong>No profile signal found.</strong> The service reports no long-term history and no
            recorded clicks for {userId}.
          </div>
        </div>
      )}
      {state.status === 'done' && !clean && (
        <div className="cf-notice cf-notice--warn">
          <div>
            <strong>The service still holds data for {userId}.</strong> It reports{' '}
            {[state.usedLong && 'a long-term history', state.usedShort && 'recorded clicks']
              .filter(Boolean)
              .join(' and ')}
            . The unlearning engine removed this user from its shard commitments, but the
            recommendation service keeps a separate copy of history and clicks that this endpoint
            does not clear yet. This is a backend gap, not a UI state.
          </div>
        </div>
      )}
    </section>
  );
}

export default function StatusPage() {
  const { query } = useLocation();
  const { userId, health } = useApp();
  const cert = useLatestCertificate();
  const requestId = query.request || cert.certificate?.request_id || null;

  const [req, setReq] = useState({ status: 'idle', data: null, error: null });
  const [block, setBlock] = useState(null);

  useEffect(() => {
    if (!requestId || health.online !== true) return undefined;
    let cancelled = false;
    setReq({ status: 'loading', data: null, error: null });
    setBlock(null);

    api
      .unlearningStatus(requestId)
      .then((data) => {
        if (!cancelled) setReq({ status: 'ready', data, error: null });
      })
      .catch((err) => {
        if (!cancelled) setReq({ status: 'error', data: null, error: err.message });
      });

    // The ledger block for this request carries the request id in its metrics.
    api
      .auditTrail()
      .then((trail) => {
        if (cancelled) return;
        setBlock((trail.blocks || []).find((b) => b.metrics?.request_id === requestId) ?? null);
      })
      .catch(() => {
        if (!cancelled) setBlock(null);
      });

    return () => {
      cancelled = true;
    };
  }, [requestId, health.online]);

  const head = (
    <>
      <header className="cf-page-head">
        <h1>Unlearning status</h1>
        <p>The state of the latest unlearning request, as recorded by the backend.</p>
      </header>
      <PipelineRail current="/status" />
    </>
  );

  if (!requestId && (cert.status === 'loading' || health.online === null)) {
    return (
      <div>
        {head}
        <div className="cf-skeleton" style={{ height: 220 }} aria-busy="true" />
      </div>
    );
  }

  if (!requestId) {
    return (
      <div>
        {head}
        <EmptyState
          title={`No unlearning request found for ${userId}`}
          action={
            <Link to="/forget" className="cf-btn cf-btn--soft">
              Forget my data
            </Link>
          }
        >
          {cert.status === 'error'
            ? cert.error
            : 'Submit a forget request first. The status appears here once the backend has recorded it.'}
        </EmptyState>
      </div>
    );
  }

  if (req.status === 'error') {
    return (
      <div>
        {head}
        <ErrorState title="Could not load this request" message={req.error} />
      </div>
    );
  }

  if (req.status !== 'ready') {
    return (
      <div>
        {head}
        <div className="cf-skeleton" style={{ height: 220 }} aria-busy="true" />
      </div>
    );
  }

  const d = req.data;
  const completed = d.status === 'completed';
  const certMatches = cert.status === 'ready' && cert.certificate.request_id === requestId;
  const shards = (d.affected_shards || []).map((s) => `Shard ${s}`).join(', ');

  return (
    <div>
      {head}

      <div className="cf-two cf-two--wide">
        <section className="cf-card cf-stack">
          <div className="cf-stack-sm">
            <h2>Request</h2>
            <code className="cf-reqid">{d.request_id}</code>
            <div className="cf-chips">
              <span className={`cf-chip ${completed ? 'cf-chip--ok' : 'cf-chip--warn'}`}>
                Status: {d.status}
              </span>
              <span className="cf-chip">{d.deletion_type}</span>
              <span className="cf-chip">User {d.user_id}</span>
            </div>
          </div>

          <ol className="cf-timeline">
            <TimelineItem title="Request received" time={formatDateTime(d.created_at)}>
              Recorded with deletion path {d.deletion_type}.
            </TimelineItem>

            <TimelineItem
              title={completed ? 'Unlearning completed' : `Unlearning: ${d.status}`}
              time={d.completed_at ? formatDateTime(d.completed_at) : undefined}
            >
              {shards ? `Affected shard: ${shards.replace('Shard ', '')}.` : 'No shard reported.'}
            </TimelineItem>

            {certMatches && (
              <TimelineItem
                title="Certificate issued"
                time={formatDateTime(cert.certificate.timestamp)}
              >
                <code>{cert.certificate.certificate_id}</code>,{' '}
                <Link to="/verification" className="cf-linkbtn">
                  verify it
                </Link>
                .
              </TimelineItem>
            )}

            {block && (
              <TimelineItem title="Recorded in the audit ledger" time={formatDateTime(block.timestamp)}>
                Block #{block.block_id}, <code>{block.action}</code>.
              </TimelineItem>
            )}
          </ol>

          {!certMatches && cert.status !== 'loading' && (
            <p className="cf-fine">
              The latest certificate on file for {userId} belongs to a different request, so it is not
              shown in this timeline.
            </p>
          )}
        </section>

        <div className="cf-stack">
          <ServingCheck userId={d.user_id} />
          <Link to="/verification" className="cf-btn cf-btn--primary cf-btn--block">
            Go to verification
          </Link>
        </div>
      </div>
    </div>
  );
}