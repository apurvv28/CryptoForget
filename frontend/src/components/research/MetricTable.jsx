import { METRICS } from '../../cryptoforge/lib/researchData';

// rows: [{ label, values: { auc, mrr, ... }, emphasis?, signed? }]
export default function MetricTable({ caption, firstColumn, rows }) {
  const fmt = (v, signed) => `${signed && v > 0 ? '+' : ''}${v.toFixed(4)}`;

  return (
    <div className="cf-tablewrap" tabIndex={0} role="region" aria-label={caption}>
      <table className="cf-table">
        <caption className="cf-sr">{caption}</caption>
        <thead>
          <tr>
            <th scope="col">{firstColumn}</th>
            {METRICS.map((m) => (
              <th key={m.key} scope="col">{m.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className={row.emphasis ? 'is-emphasis' : ''}>
              <th scope="row">{row.label}</th>
              {METRICS.map((m) => (
                <td key={m.key}>{fmt(row.values[m.key], row.signed)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
