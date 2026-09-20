import { useEffect, useState } from 'react';
import { api } from '../../cryptoforge/api/client';
import { formatDateTime } from '../../cryptoforge/lib/time';
import { HashValue } from '../CopyButton';
import Icon from '../Icon';

const isGenesis = (hash) => /^0+$/.test(hash || '');

export default function AuditLedgerPanel({ highlightRequestId }) {
  const [state, setState] = useState({ status: 'loading', trail: null, error: null });
  const [showAll, setShowAll] = useState(false);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, status: 'loading', error: null }));
    api
      .auditTrail()
      .then((trail) => {
        if (!cancelled) setState({ status: 'ready', trail, error: null });
      })
      .catch((err) => {
        if (!cancelled) setState({ status: 'error', trail: null, error: err.message });
      });
    return () => {
      cancelled = true;
    };
  }, [nonce]);

  const { trail } = state;
  const blocks = trail ? [...(trail.blocks || [])].reverse() : [];
  const visible = showAll ? blocks : blocks.slice(0, 6);

  return (
    <section className="cf-card cf-stack">
      <div className="cf-section-head">
        <h2>Audit ledger</h2>
        <button type="button" className="cf-btn cf-btn--ghost" onClick={() => setNonce((n) => n + 1)}>
          <Icon name="refresh" size={16} /> Reload
        </button>
      </div>

      {state.status === 'loading' && <div className="cf-skeleton" style={{ height: 120 }} aria-busy="true" />}

      {state.status === 'error' && (
        <div className="cf-notice cf-notice--danger" role="alert">
          <Icon name="alert" />
          <div>{state.error}</div>
        </div>
      )}

      {state.status === 'ready' && (
        <>
          <div className={`cf-notice ${trail.ledger_integrity_valid ? 'cf-notice--ok' : 'cf-notice--danger'}`}>
            <Icon name={trail.ledger_integrity_valid ? 'shield-check' : 'alert'} />
            <div>
              <strong>{trail.integrity_message}</strong> {trail.total_blocks} block
              {trail.total_blocks === 1 ? '' : 's'}. Each block's hash covers the hash of the block
              before it.
            </div>
          </div>

          {blocks.length === 0 ? (
            <p className="cf-muted">The ledger is empty.</p>
          ) : (
            <ol className="cf-blocks">
              {visible.map((b) => {
                const linked = highlightRequestId && b.metrics?.request_id === highlightRequestId;
                return (
                  <li key={b.block_id} className={`cf-block ${linked ? 'is-linked' : ''}`}>
                    <div className="cf-block__head">
                      <strong>Block #{b.block_id}</strong>
                      <code className="cf-block__action">{b.action}</code>
                      {linked && <span className="cf-chip cf-chip--accent">This request</span>}
                      <span className="cf-block__time">{formatDateTime(b.timestamp)}</span>
                    </div>
                    <dl className="cf-kv cf-kv--tight">
                      <div className="cf-kv__row">
                        <dt>Previous hash</dt>
                        <dd>
                          {isGenesis(b.prev_hash) ? (
                            <span className="cf-muted">genesis (all zeros)</span>
                          ) : (
                            <HashValue value={b.prev_hash} />
                          )}
                        </dd>
                      </div>
                      <div className="cf-kv__row">
                        <dt>Payload hash</dt>
                        <dd><HashValue value={b.payload_hash} /></dd>
                      </div>
                      <div className="cf-kv__row">
                        <dt>Block hash</dt>
                        <dd><HashValue value={b.curr_hash} /></dd>
                      </div>
                    </dl>
                  </li>
                );
              })}
            </ol>
          )}

          {blocks.length > 6 && (
            <div>
              <button type="button" className="cf-btn cf-btn--ghost" onClick={() => setShowAll((v) => !v)}>
                {showAll ? 'Show fewer' : `Show all ${blocks.length} blocks`}
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}