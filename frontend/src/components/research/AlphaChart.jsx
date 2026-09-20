import { useState } from 'react';
import { MODEL_CONFIG } from '../../cryptoforge/lib/modelConfig';
import { ALPHA_SWEEP, METRICS } from '../../cryptoforge/lib/researchData';

const W = 640;
const H = 290;
const M = { l: 54, r: 28, t: 30, b: 48 };

export default function AlphaChart() {
  const [metric, setMetric] = useState('auc');
  const label = METRICS.find((m) => m.key === metric).label;

  const values = ALPHA_SWEEP.map((r) => r[metric]);
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const pad = (hi - lo) * 0.2 || 0.01;
  const yMin = lo - pad;
  const yMax = hi + pad;

  const x = (a) => M.l + a * (W - M.l - M.r);
  const y = (v) => M.t + (1 - (v - yMin) / (yMax - yMin)) * (H - M.t - M.b);
  const ticks = Array.from({ length: 4 }, (_, i) => yMin + (i / 3) * (yMax - yMin));
  const line = ALPHA_SWEEP.map((r) => `${x(r.alpha).toFixed(1)},${y(r[metric]).toFixed(1)}`).join(' ');

  return (
    <div className="cf-achart">
      <div className="cf-chiprow" role="group" aria-label="Metric">
        {METRICS.map((m) => (
          <button
            key={m.key}
            type="button"
            className="cf-pill"
            aria-pressed={metric === m.key}
            onClick={() => setMetric(m.key)}
          >
            {m.label}
          </button>
        ))}
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${label} for each alpha value, from ${values[0].toFixed(4)} at alpha 0 to ${values[values.length - 1].toFixed(4)} at alpha 1`}>
        {ticks.map((t) => (
          <g key={t}>
            <line className="cf-rchart__grid" x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} />
            <text x={M.l - 8} y={y(t) + 4} textAnchor="end">{t.toFixed(3)}</text>
          </g>
        ))}
        {ALPHA_SWEEP.map((r) => (
          <text key={r.alpha} x={x(r.alpha)} y={H - M.b + 20} textAnchor="middle">{r.alpha.toFixed(2)}</text>
        ))}
        <text x={(M.l + W - M.r) / 2} y={H - 6} textAnchor="middle">α (weight of the long-term profile)</text>

        <polyline className="cf-achart__line" points={line} />
        {ALPHA_SWEEP.map((r) => {
          const configured = r.alpha === MODEL_CONFIG.alpha;
          return (
            <g key={r.alpha}>
              {configured && <circle className="cf-achart__ring" cx={x(r.alpha)} cy={y(r[metric])} r="11" />}
              <circle className="cf-achart__dot" cx={x(r.alpha)} cy={y(r[metric])} r="5" />
              <text x={x(r.alpha)} y={y(r[metric]) - 16} textAnchor="middle" className="cf-achart__value">
                {r[metric].toFixed(4)}
              </text>
            </g>
          );
        })}
      </svg>
      <p className="cf-fine">
        α = 0 uses only the short-term profile and α = 1 only the long-term profile. The ring marks the
        configured α = {MODEL_CONFIG.alpha}. The vertical axis does not start at zero.
      </p>
    </div>
  );
}
