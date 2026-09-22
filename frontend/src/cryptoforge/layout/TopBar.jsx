import { useEffect, useRef, useState } from "react";
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
  const { users, userId, setUserId, user } = useApp();
  const [q, setQ] = useState("");
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  const selectedUser = users.find((item) => item.user_id === userId) || user;
  const selectedUserName = selectedUser?.name || "Demo user";

  useEffect(() => {
    const closeOnOutsideClick = (event) => {
      if (!userMenuRef.current?.contains(event.target)) {
        setUserMenuOpen(false);
      }
    };
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setUserMenuOpen(false);
    };

    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, []);

  const submit = (e) => {
    e.preventDefault();
    const term = q.trim();
    if (term) navigate(`/explore?source=mind&q=${encodeURIComponent(term)}`);
  };

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
        <div className="cf-persona" ref={userMenuRef}>
          <span className="cf-avatar" aria-hidden="true">
            {initials(user, userId)}
          </span>
          <button
            type="button"
            className="cf-persona__trigger"
            aria-haspopup="listbox"
            aria-expanded={userMenuOpen}
            onClick={() => setUserMenuOpen((open) => !open)}
          >
            <span className="cf-persona__body">
              <span className="cf-persona__label">Demo user</span>
              <span className="cf-persona__value">
                {userId} - {selectedUserName}
              </span>
            </span>
            <span className={`cf-persona__chevron${userMenuOpen ? " is-open" : ""}`} aria-hidden="true">
              ▼
            </span>
          </button>

          {userMenuOpen && (
            <div className="cf-persona__menu" role="listbox" aria-label="Select demo user">
              {users.length === 0 ? (
                <button type="button" className="cf-persona__option is-selected" role="option" aria-selected="true">
                  <span>{userId} - Demo user</span>
                  <span aria-hidden="true">✓</span>
                </button>
              ) : (
                users.map((item) => {
                  const selected = item.user_id === userId;
                  return (
                    <button
                      type="button"
                      className={`cf-persona__option${selected ? " is-selected" : ""}`}
                      key={item.user_id}
                      role="option"
                      aria-selected={selected}
                      onClick={() => {
                        setUserId(item.user_id);
                        setUserMenuOpen(false);
                      }}
                    >
                      <span>
                        {item.user_id} - {item.name || "Demo user"}
                        {item.is_unlearned ? " (forgotten)" : ""}
                      </span>
                      {selected && <span aria-hidden="true">✓</span>}
                    </button>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
