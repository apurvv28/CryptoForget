import { MODEL_CONFIG, recencyWeight } from '../cryptoforge/lib/modelConfig';

const W = 640;
const H = 280;
const M = { l: 46, r: 18, t: 18, b: 46 };
const MAX_HOURS = 48;
const X_TICKS = [0, 6, 12, 18, 24, 36, 48];
const Y_TICKS = [0, 0.25, 0.5, 0.75, 1];

// clicks: [{ hours, weight, inWindow, title }]
export default function RecencyChart({ clicks }) {
  const { decayRate, windowHours } = MODEL_CONFIG;
  const x = (h) => M.l + (h / MAX_HOURS) * (W - M.l - M.r);
  const y = (w) => M.t + (1 - w) * (H - M.t - M.b);

  const curve = (from, to) => {
    const pts = [];
    for (let h = from; h <= to + 1e-9; h += 0.5) {
      pts.push(`${x(h).toFixed(1)},${y(recencyWeight(h, decayRate)).toFixed(1)}`);
    }
    return pts.join(' ');
  };

  const visible = clicks.filter((c) => c.hours <= MAX_HOURS);
  const hidden = clicks.length - visible.length;

  return (
    <figure className="cf-rchart">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`Recency weight falls from 1 at the moment of a click to ${recencyWeight(windowHours).toFixed(2)} after ${windowHours} hours. Clicks older than ${windowHours} hours are not counted.`}
      >
        <rect
          className="cf-rchart__window"
          x={x(0)}
          y={M.t}
          width={x(windowHours) - x(0)}
          height={H - M.t - M.b}
        />
        {Y_TICKS.map((t) => (
          <g key={t}>
            <line className="cf-rchart__grid" x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} />
            <text x={M.l - 8} y={y(t) + 4} textAnchor="end">{t}</text>
          </g>
        ))}
        {X_TICKS.map((t) => (
          <text key={t} x={x(t)} y={H - M.b + 18} textAnchor="middle">{t}</text>
        ))}
        <text x={(M.l + W - M.r) / 2} y={H - 6} textAnchor="middle">hours since the click</text>
        <text x={x(windowHours / 2)} y={M.t + 14} textAnchor="middle" className="cf-rchart__tag">
          counted (last {windowHours} h)
        </text>

        <polyline className="cf-rchart__curve" points={curve(0, windowHours)} />
        <polyline className="cf-rchart__curve cf-rchart__curve--off" points={curve(windowHours, MAX_HOURS)} />

        {visible.map((c, i) => (
          <circle
            key={`${c.news_id}-${i}`}
            cx={x(c.hours)}
            cy={y(c.weight)}
            r="5.5"
            className={`cf-rchart__dot ${c.inWindow ? '' : 'is-off'}`}
          >
            <title>
              {c.title} · {c.hours.toFixed(1)} h ago · weight {c.weight.toFixed(2)}
              {c.inWindow ? '' : ' (outside the window, not counted)'}
            </title>
          </circle>
        ))}
      </svg>
      <figcaption>
        Curve: weight = e<sup>−λ·hours</sup> with λ = {decayRate} per hour. Dots are your real clicks.
        {hidden > 0 && ` ${hidden} older click${hidden === 1 ? ' is' : 's are'} beyond ${MAX_HOURS} h and not drawn.`}
      </figcaption>
    </figure>
  );
}
