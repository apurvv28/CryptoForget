import { Link } from '../cryptoforge/router/router';
import { useApp } from '../cryptoforge/state/AppState';

const STEPS = [
  { to: '/', label: 'Personalization' },
  { to: '/privacy', label: 'Your data' },
  { to: '/forget', label: 'Forget' },
  { to: '/status', label: 'Unlearning' },
  { to: '/verification', label: 'Verification' },
];

export default function PipelineRail({ current }) {
  const { personalization } = useApp();
  const stateText = { on: 'On', off: 'Off' }[personalization];

  return (
    <ol className="cf-rail" aria-label="CryptoForget pipeline">
      {STEPS.map((step, i) => {
        const isCurrent = step.to === current;
        return (
          <li key={step.to} className={`cf-rail__step ${isCurrent ? 'is-current' : ''}`}>
            <Link to={step.to} aria-current={isCurrent ? 'step' : undefined}>
              <span className="cf-rail__num">{i + 1}</span>
              <span className="cf-rail__text">
                <span className="cf-rail__label">{step.label}</span>
                {step.to === '/' && stateText && (
                  <span className={`cf-rail__state cf-rail__state--${personalization}`}>{stateText}</span>
                )}
              </span>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}