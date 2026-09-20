import Icon from '../Icon';

export function ResultBanner({ result, size = 'md' }) {
  const ok = Boolean(result.is_valid);
  const target = result.target_max_latency_ms;
  const within = typeof target === 'number' && result.verification_time_ms <= target;

  return (
    <div className={`cf-verdict cf-verdict--${ok ? 'ok' : 'bad'} cf-verdict--${size}`} role="status">
      <span className="cf-verdict__icon">
        <Icon name={ok ? 'shield-check' : 'alert'} size={size === 'lg' ? 28 : 20} />
      </span>
      <div className="cf-verdict__body">
        <strong>{ok ? 'Verified' : 'Rejected'}</strong>
        <p>{result.message}</p>
        <div className="cf-chips">
          <span className="cf-chip">Backend check: {result.verification_time_ms} ms</span>
          {typeof target === 'number' && (
            <span className={`cf-chip ${within ? 'cf-chip--ok' : 'cf-chip--warn'}`}>
              {within ? `Within the ${target} ms target` : `Over the ${target} ms target`}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function VerdictCard({ verify, certificate, onRerun }) {
  return (
    <section className="cf-card cf-stack-sm" aria-live="polite">
      <div className="cf-section-head">
        <h2>Verification result</h2>
        <button
          type="button"
          className="cf-btn cf-btn--ghost"
          onClick={onRerun}
          disabled={verify.status === 'running'}
        >
          <Icon name="refresh" size={16} /> Verify again
        </button>
      </div>

      {(verify.status === 'idle' || verify.status === 'running') && (
        <div className="cf-skeleton" style={{ height: 96 }} aria-busy="true" />
      )}
      {verify.status === 'error' && (
        <div className="cf-notice cf-notice--danger" role="alert">
          <Icon name="alert" />
          <div>
            <strong>Could not run the verification.</strong> {verify.error}
          </div>
        </div>
      )}
      {verify.status === 'done' && <ResultBanner result={verify.result} size="lg" />}

      <p className="cf-fine">
        Checked by <code>POST /api/v1/verify-certificate</code> for {certificate.certificate_id}.
      </p>
    </section>
  );
}