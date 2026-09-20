import Icon from "../../components/Icon";
import { Link, isActive, useLocation } from "../router/router";

const ITEMS = [
  { to: "/", label: "For you", icon: "sparkles" },
  { to: "/headlines", label: "Headlines", icon: "newspaper" },
  { to: "/explore", label: "Explore", icon: "compass" },
  { to: "/privacy", label: "Privacy", icon: "lock" },
];

export default function MobileNav({ onMenu }) {
  const { path } = useLocation();
  return (
    <nav className="cf-mobilenav" aria-label="Quick navigation">
      {ITEMS.map((item) => {
        const active = isActive(path, item.to);
        return (
          <Link
            key={item.to}
            to={item.to}
            className={`cf-mobilenav__item ${active ? "is-active" : ""}`}
            aria-current={active ? "page" : undefined}
          >
            <Icon name={item.icon} size={20} />
            <span>{item.label}</span>
          </Link>
        );
      })}
      <button type="button" className="cf-mobilenav__item" onClick={onMenu}>
        <Icon name="menu" size={20} />
        <span>Menu</span>
      </button>
    </nav>
  );
}
