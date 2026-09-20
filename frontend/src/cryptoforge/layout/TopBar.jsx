import { useState } from "react";
import Icon from "../../components/Icon";
import { navigate } from "../router/router";
import { useApp } from "../state/AppState";

function initials(user, userId) {
  if (user?.name) {
    return user.name
      .split(" ")
      .map((w) => w[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  }
  return userId?.slice(-2) ?? "?";
}

export default function TopBar({ onMenu }) {
  const { health, users, userId, setUserId, user } = useApp();
  const [q, setQ] = useState("");

  const submit = (e) => {
    e.preventDefault();
    const term = q.trim();
    if (term) navigate(`/explore?source=mind&q=${encodeURIComponent(term)}`);
  };

  const status =
    health.online === null ? "checking" : health.online ? "online" : "offline";
  const statusLabel = {
    checking: "Checking API",
    online: "API online",
    offline: "API offline",
  }[status];

  return (
    <header className="cf-topbar">
      <button
        type="button"
        className="cf-iconbtn cf-topbar__menu"
        onClick={onMenu}
        aria-label="Open menu"
      >
        <Icon name="menu" size={20} />
      </button>

      <form className="cf-search" onSubmit={submit} role="search">
        <Icon name="search" size={18} />
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search the MIND catalog"
          aria-label="Search the MIND catalog"
        />
      </form>

      <div className="cf-topbar__right">
        {health.data?.model_version && (
          <span
            className="cf-chip cf-topbar__model"
            title="Model version reported by /health"
          >
            Model {health.data.model_version}
          </span>
        )}

        <span className={`cf-status cf-status--${status}`}>
          <span className="cf-status__dot" />
          <span className="cf-status__text">{statusLabel}</span>
        </span>

        <label className="cf-persona">
          <span className="cf-avatar" aria-hidden="true">
            {initials(user, userId)}
          </span>
          <span className="cf-persona__body">
            <span className="cf-persona__label">Demo user</span>
            <select
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              aria-label="Switch demo user"
            >
              {users.length === 0 && <option value={userId}>{userId}</option>}
              {users.map((u) => (
                <option key={u.user_id} value={u.user_id}>
                  {u.user_id} · {u.name}
                  {u.is_unlearned ? " (forgotten)" : ""}
                </option>
              ))}
            </select>
          </span>
        </label>
      </div>
    </header>
  );
}
