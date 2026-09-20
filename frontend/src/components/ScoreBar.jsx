export default function ScoreBar({ score, max, delta }) {
  const pct = max > 0 ? Math.max(3, Math.round((score / max) * 100)) : 0;
  const moved = typeof delta === 'number' && delta !== 0;

  return (
    <div
      className="cf-score"
      title="Cosine similarity between your dynamic profile and this article's TF-IDF vector. The bar is scaled to the best match in this list."
    >
      <div className="cf-score__head">
        <span>Match</span>
        <span className="cf-score__value">{score.toFixed(3)}</span>
        {moved && (
          <span
            className={`cf-delta ${delta > 0 ? 'is-up' : 'is-down'}`}
            aria-label={`Moved ${delta > 0 ? 'up' : 'down'} ${Math.abs(delta)} places since the last ranking`}
          >
            {delta > 0 ? '▲' : '▼'} {Math.abs(delta)}
          </span>
        )}
      </div>
      <div className="cf-score__track">
        <div className="cf-score__fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}