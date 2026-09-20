import AlphaChart from '../../components/research/AlphaChart';
import ComparisonBars from '../../components/research/ComparisonBars';
import MetricTable from '../../components/research/MetricTable';
import Icon from '../../components/Icon';
import { MODEL_CONFIG } from '../lib/modelConfig';
import { ALPHA_SWEEP, INTEREST_SHIFT, METRICS, OVERALL_BENCHMARK } from '../lib/researchData';
import { useApp } from '../state/AppState';

function Fact({ label, children }) {
  return (
    <div className="cf-fact">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function RunningModel() {
  const { health } = useApp();
  const d = health.data;
  const num = (v) => (typeof v === 'number' ? v.toLocaleString() : '—');

  return (
    <section className="cf-card cf-stack-sm">
      <h2>Running model (live from /health)</h2>
      {health.online === false ? (
        <div className="cf-notice cf-notice--warn">
          <Icon name="alert" />
          <div>The API is offline, so live values are unavailable. The results below are static.</div>
        </div>
      ) : (
        <dl className="cf-facts">
          <Fact label="Model version">{d?.model_version ?? '—'}</Fact>
          <Fact label="Known users">{num(d?.known_users)}</Fact>
          <Fact label="Content vector dimension">{num(d?.content_vector_dim)}</Fact>
        </dl>
      )}
    </section>
  );
}

export default function ResearchPage() {
  const st = INTEREST_SHIFT.static;
  const dyn = INTEREST_SHIFT.dynamic;
  const allLower = METRICS.every((m) => dyn[m.key] < st[m.key]);
  const deltas = Object.fromEntries(METRICS.map((m) => [m.key, dyn[m.key] - st[m.key]]));

  const rising = METRICS.every((m) =>
    ALPHA_SWEEP.every((r, i) => i === 0 || r[m.key] > ALPHA_SWEEP[i - 1][m.key]),
  );
  const alphaOne = ALPHA_SWEEP[ALPHA_SWEEP.length - 1];
  const maxGap = Math.max(...METRICS.map((m) => Math.abs(alphaOne[m.key] - st[m.key])));

  return (
    <div className="cf-stack">
      <header className="cf-page-head">
        <h1>Research</h1>
        <p>
          Offline experiments for the base recommendation model, evaluated on MIND-small. These are
          static results from your experiments. Nothing here is computed by the API, except the live
          model card.
        </p>
      </header>

      <section className="cf-card cf-finding">
        <span className="cf-finding__tag">Main finding</span>
        <h2>The dynamic model did not outperform the static model</h2>
        <p>
          {allLower
            ? `In the leakage-controlled interest-shift evaluation, the dynamic long + short-term model scored lower than the static content-based model on all six metrics (AUC ${dyn.auc.toFixed(4)} vs ${st.auc.toFixed(4)}). This is an experimental result and is reported as measured.`
            : 'The dynamic and static models are compared below on the leakage-controlled interest-shift evaluation.'}
        </p>
      </section>

      <div className="cf-two">
        <RunningModel />
        <section className="cf-card cf-stack-sm">
          <h2>Configuration</h2>
          <dl className="cf-facts">
            <Fact label="α (long-term weight)">{MODEL_CONFIG.alpha}</Fact>
            <Fact label="λ (recency decay)">{MODEL_CONFIG.decayRate} per hour</Fact>
            <Fact label="Short-term window">{MODEL_CONFIG.windowHours} hours</Fact>
          </dl>
          <p className="cf-fine">
            Backend defaults (ALPHA, DECAY_RATE, SHORT_TERM_WINDOW_HOURS). The API does not report them.
          </p>
        </section>
      </div>

      <section className="cf-card cf-stack">
        <div className="cf-stack-sm">
          <h2>Interest-shift evaluation (leakage-controlled)</h2>
          <p>
            Static content-based model versus the dynamic long + short-term model, with future
            interactions kept out of earlier recommendations.
          </p>
        </div>
        <ComparisonBars />
        <MetricTable
          caption="Interest-shift evaluation: static versus dynamic model"
          firstColumn="Model"
          rows={[
            { label: 'Static content-based', values: st },
            { label: 'Dynamic long + short', values: dyn },
            { label: 'Dynamic − static', values: deltas, emphasis: true, signed: true },
          ]}
        />
      </section>

      <section className="cf-card cf-stack">
        <div className="cf-stack-sm">
          <h2>Alpha sensitivity</h2>
          <p>
            {rising
              ? `Every metric rises as α increases, so adding short-term weight lowered ranking quality in this experiment. α = 1.00 (long-term only) is best on all six metrics and lands within ${maxGap.toFixed(4)} of the static model on every one.`
              : 'The table shows each metric for five values of α.'}
          </p>
        </div>
        <AlphaChart />
        <MetricTable
          caption="Alpha sensitivity"
          firstColumn="α"
          rows={ALPHA_SWEEP.map((r) => ({
            label: r.alpha.toFixed(2),
            values: r,
            emphasis: r.alpha === MODEL_CONFIG.alpha,
          }))}
        />
      </section>

      <section className="cf-card cf-stack">
        <div className="cf-stack-sm">
          <h2>Overall benchmark</h2>
        </div>
        <div className="cf-notice cf-notice--warn">
          <Icon name="alert" />
          <div>
            <strong>Not a leakage-controlled comparison.</strong> The baseline numbers were produced using
            interaction data before evaluation, so they should not be read as a fair comparison against the
            chronological dynamic model. The interest-shift experiment above is the controlled one.
          </div>
        </div>
        <MetricTable
          caption="Overall benchmark of the five models"
          firstColumn="Model"
          rows={OVERALL_BENCHMARK}
        />
      </section>

      <section className="cf-card cf-stack-sm">
        <h2>Method notes</h2>
        <ul className="cf-list cf-list--plain">
          <li>Data: MIND-small (user id, news id, timestamp, click history, clicked and non-clicked impressions, title, abstract, category).</li>
          <li>Signals: clicks only. Likes, dislikes, saves, shares and dwell time are not used.</li>
          <li>Long-term profile: TF-IDF representation of the user's historical clicked articles.</li>
          <li>Short-term profile: clicks in a {MODEL_CONFIG.windowHours}-hour window, weighted by e<sup>−λ·hours</sup> with λ = {MODEL_CONFIG.decayRate}.</li>
          <li>Fusion: α × long-term + (1 − α) × short-term, built chronologically so future interactions never influence earlier recommendations.</li>
          <li>Metrics: AUC, MRR, NDCG@5, NDCG@10, Recall@5, Recall@10.</li>
          <li>In the running API, a user with no history and no clicks gets a score of 0 for every candidate, in the original order. The popularity fallback from the offline experiments is not part of that endpoint.</li>
        </ul>
      </section>
    </div>
  );
}
