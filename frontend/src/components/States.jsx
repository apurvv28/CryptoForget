import Icon from './Icon';

export function SkeletonGrid({ count = 6, variant = 'row' }) {
  return (
    <div
      className={variant === 'feature' ? 'cf-grid-feature' : 'cf-grid-rows'}
      aria-busy="true"
      aria-label="Loading articles"
    >
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className={`cf-skeleton cf-skel cf-skel--${variant}`} />
      ))}
    </div>
  );
}

export function EmptyState({ title, children, action }) {
  return (
    <div className="cf-state">
      <h2>{title}</h2>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ title = 'Could not load this', message, onRetry }) {
  return (
    <div className="cf-state cf-state--error" role="alert">
      <span className="cf-state__icon">
        <Icon name="alert" />
      </span>
      <h2>{title}</h2>
      {message && <p>{message}</p>}
      {onRetry && (
        <button type="button" className="cf-btn cf-btn--ghost" onClick={onRetry}>
          <Icon name="refresh" size={16} /> Try again
        </button>
      )}
    </div>
  );
}