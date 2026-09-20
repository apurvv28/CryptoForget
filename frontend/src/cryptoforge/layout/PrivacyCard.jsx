import Icon from "../../components/Icon";
import { Link } from "../router/router";
import { useApp } from "../state/AppState";

export default function PrivacyCard({ onNavigate }) {
  const { personalization, clicks } = useApp();

  const variants = {
    loading: {
      tone: "idle",
      icon: "lock",
      title: "Checking privacy status",
      text: "Reading your consent state from the backend.",
    },
    unavailable: {
      tone: "idle",
      icon: "alert",
      title: "API offline",
      text: "Start the backend to see your privacy status.",
    },
    on: {
      tone: "on",
      icon: "lock",
      title: "Personalization is on",
      text: "Articles you open update your profile. You can ask to be forgotten at any time.",
      cta: { to: "/forget", label: "Forget my data" },
    },
    off: {
      tone: "off",
      icon: "shield-check",
      title: "Personalization is off",
      text: "This user was forgotten. Feeds no longer use a personal profile.",
      cta: { to: "/verification", label: "View verification" },
    },
  };
  const v = variants[personalization];

  return (
    <section
      className={`cf-privacy cf-privacy--${v.tone}`}
      aria-label="Data and privacy"
    >
      <span className="cf-privacy__icon">
        <Icon name={v.icon} size={18} />
      </span>
      <h2>{v.title}</h2>
      <p>{v.text}</p>
      {personalization === "on" && (
        <p className="cf-privacy__meta">
          Clicks sent from this browser: <strong>{clicks.length}</strong>
        </p>
      )}
      {v.cta && (
        <Link
          to={v.cta.to}
          className="cf-btn cf-btn--soft cf-btn--block"
          onClick={onNavigate}
        >
          {v.cta.label}
        </Link>
      )}
    </section>
  );
}
