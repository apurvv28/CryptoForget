import Icon from "../../components/Icon";

export default function ComingNext({ route }) {
  const plan = route.plan || {};
  return (
    <div>
      <header className="cf-page-head">
        <h1>{route.label}</h1>
        {plan.summary && <p>{plan.summary}</p>}
      </header>

      <section className="cf-card cf-soon">
        <h2>Not built yet</h2>
        <p>
          This screen arrives in a later batch. It will read from these real
          backend endpoints:
        </p>
        <ul className="cf-endpoints">
          {(plan.uses || []).map((u) => (
            <li key={u}>
              <code>{u}</code>
            </li>
          ))}
        </ul>
        {plan.missing && (
          <div className="cf-notice cf-notice--warn">
            <Icon name="alert" />
            <div>
              <strong>Backend capability missing.</strong> {plan.missing}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
