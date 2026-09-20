import { INTEREST_SHIFT, METRICS } from '../../cryptoforge/lib/researchData';

export default function ComparisonBars() {
  return (
    <div className="cf-cmp" role="group" aria-label="Static versus dynamic model, interest-shift evaluation">
      <div className="cf-cmp__legend">
        <span><i className="cf-cmp__key cf-cmp__key--static" /> Static content-based</span>
        <span><i className="cf-cmp__key cf-cmp__key--dynamic" /> Dynamic long + short</span>
      </div>

      {METRICS.map((m) => {
        const s = INTEREST_SHIFT.static[m.key];
        const d = INTEREST_SHIFT.dynamic[m.key];
        const delta = d - s;
        return (
          <div className="cf-cmp__row" key={m.key}>
            <div className="cf-cmp__label">{m.label}</div>
            <div className="cf-cmp__bars">
              <div className="cf-cmp__bar">
                <div className="cf-cmp__fill cf-cmp__fill--static" style={{ width: `${s * 100}%` }} />
                <span>{s.toFixed(4)}</span>
              </div>
              <div className="cf-cmp__bar">
                <div className="cf-cmp__fill cf-cmp__fill--dynamic" style={{ width: `${d * 100}%` }} />
                <span>{d.toFixed(4)}</span>
              </div>
            </div>
            <span className={`cf-chip ${delta < 0 ? 'cf-chip--warn' : 'cf-chip--ok'}`}>
              {delta > 0 ? '+' : ''}{delta.toFixed(4)}
            </span>
          </div>
        );
      })}
      <p className="cf-fine">Bars span 0 to 1. The chip is dynamic minus static.</p>
    </div>
  );
}
