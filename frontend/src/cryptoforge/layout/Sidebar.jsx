import Icon from "../../components/Icon";
import { Link, isActive, useLocation } from "../router/router";
import { ROUTES } from "../routes";
import PrivacyCard from "./PrivacyCard";

const GROUPS = [
  { id: "news", label: "News" },
  { id: "data", label: "Your data" },
  { id: "project", label: "Project" },
];

export default function Sidebar({ onNavigate }) {
  const { path } = useLocation();

  return (
    <nav className="cf-sidebar__inner" aria-label="Main">
      <Link to="/" className="cf-brand" onClick={onNavigate}>
        <span className="cf-brand__mark">
          <Icon name="shield" size={18} />
        </span>
        <span className="cf-brand__text">
          <span className="cf-brand__name">CryptoForget</span>
          <span className="cf-brand__tag">Verifiable unlearning</span>
        </span>
      </Link>

      {GROUPS.map((group) => (
        <div className="cf-navgroup" key={group.id}>
          <p className="cf-navgroup__label">{group.label}</p>
          {ROUTES.filter((r) => r.nav !== false && r.group === group.id).map(
            (r) => {
              const active = isActive(path, r.path);
              return (
                <Link
                  key={r.path}
                  to={r.path}
                  className={`cf-navitem ${active ? "is-active" : ""}`}
                  aria-current={active ? "page" : undefined}
                  onClick={onNavigate}
                >
                  <Icon name={r.icon} />
                  <span>{r.label}</span>
                  {!r.component && (
                    <span className="cf-navitem__soon">Soon</span>
                  )}
                </Link>
              );
            },
          )}
        </div>
      ))}

      <PrivacyCard onNavigate={onNavigate} />
    </nav>
  );
}
