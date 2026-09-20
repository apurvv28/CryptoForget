import {
  createContext, useCallback, useContext, useEffect, useMemo, useRef, useState,
} from 'react';
import { api } from '../api/client';

const AppContext = createContext(null);
export const useApp = () => useContext(AppContext);

const USER_KEY = 'cf.userId';
const clicksKey = (uid) => `cf.clicks.${uid}`;

function readJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}
function writeJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage unavailable */
  }
}

export function AppProvider({ children }) {
  const [health, setHealth] = useState({ online: null, data: null });
  const [users, setUsers] = useState([]);
  const [userId, setUserIdState] = useState(() => readJSON(USER_KEY, 'U1000'));
  const [user, setUser] = useState(null);
  const [userError, setUserError] = useState(null);
  const [clicks, setClicks] = useState([]);
  const [backendClickTotal, setBackendClickTotal] = useState(null);
  const articleCache = useRef(new Map());

  // ---- API health (poll) ----
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const data = await api.health();
        if (alive) setHealth({ online: true, data });
      } catch {
        if (alive) setHealth({ online: false, data: null });
      }
    };
    tick();
    const id = setInterval(tick, 10000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  // ---- Demo user list ----
  const refreshUsers = useCallback(async () => {
    try {
      const list = await api.listUsers();
      setUsers(list);
      setUserIdState((current) =>
        list.some((u) => u.user_id === current) ? current : list[0]?.user_id ?? current,
      );
    } catch {
      /* keep previous list */
    }
  }, []);

  useEffect(() => {
    if (health.online) refreshUsers();
  }, [health.online, refreshUsers]);

  // ---- Selected user (consent / unlearned state comes from the backend) ----
  const refreshUser = useCallback(async () => {
    if (!userId) return null;
    try {
      const u = await api.getUser(userId);
      setUser(u);
      setUserError(null);
      return u;
    } catch (err) {
      setUser(null);
      setUserError(err.message);
      return null;
    }
  }, [userId]);

  useEffect(() => {
    if (health.online) refreshUser();
  }, [health.online, refreshUser]);

  useEffect(() => {
    setClicks(readJSON(clicksKey(userId), []));
    setBackendClickTotal(null);
  }, [userId]);

  const setUserId = useCallback((id) => {
    setUser(null);
    setUserIdState(id);
    writeJSON(USER_KEY, id);
  }, []);

  // ---- Derived personalization state ----
  const personalizationActive =
    Boolean(user) && user.consent_status !== false && !user.is_unlearned;

  let personalization = 'loading';
  if (health.online === false) personalization = 'unavailable';
  else if (user) personalization = personalizationActive ? 'on' : 'off';

  // ---- Interactions ----
  const recordClick = useCallback(
    async (article) => {
      if (!user || !personalizationActive) {
        return { sent: false, reason: 'personalization_off' };
      }
      const ack = await api.recordClick({ userId, newsId: article.news_id });
      const entry = {
        news_id: article.news_id,
        title: article.title,
        category: article.category,
        source: article.subcategory,
        is_live: Boolean(article.is_live),
        at: new Date().toISOString(),
      };
      setClicks((prev) => {
        const next = [entry, ...prev].slice(0, 200);
        writeJSON(clicksKey(userId), next);
        return next;
      });
      setBackendClickTotal(ack.total_clicks_for_user);
      return { sent: true, ack };
    },
    [user, personalizationActive, userId],
  );

  const clearClickLog = useCallback(() => {
    setClicks([]);
    writeJSON(clicksKey(userId), []);
  }, [userId]);

  // ---- Article cache (so detail pages can open live articles instantly) ----
  const cacheArticles = useCallback((list) => {
    list.forEach((a) => articleCache.current.set(a.news_id, a));
  }, []);
  const getCachedArticle = useCallback((id) => articleCache.current.get(id), []);

  const value = useMemo(
    () => ({
      health, users, userId, setUserId, user, userError,
      refreshUser, refreshUsers,
      personalization, personalizationActive,
      clicks, backendClickTotal, recordClick, clearClickLog,
      cacheArticles, getCachedArticle,
    }),
    [
      health, users, userId, setUserId, user, userError, refreshUser, refreshUsers,
      personalization, personalizationActive, clicks, backendClickTotal,
      recordClick, clearClickLog, cacheArticles, getCachedArticle,
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}