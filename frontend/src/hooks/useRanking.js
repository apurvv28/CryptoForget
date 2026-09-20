import { useEffect, useState } from "react";
import { api } from "../cryptoforge/api/client";
import { useApp } from "../cryptoforge/state/AppState";

const prevKey = (scope) => `cf.prevRank.${scope}`;
function readPrev(scope) {
  try {
    return JSON.parse(sessionStorage.getItem(prevKey(scope)) || "[]");
  } catch {
    return [];
  }
}
function writePrev(scope, ids) {
  try {
    sessionStorage.setItem(prevKey(scope), JSON.stringify(ids));
  } catch {
    /* storage unavailable */
  }
}

// status: 'idle' | 'loading' | 'ready' | 'off' | 'error'
export function useRanking({ articles, scope }) {
  const { userId, personalization } = useApp();
  const [nonce, setNonce] = useState(0);
  const [state, setState] = useState({
    status: "idle",
    ranked: [],
    meta: null,
    error: null,
  });

  useEffect(() => {
    if (articles.length === 0) {
      setState({ status: "idle", ranked: [], meta: null, error: null });
      return undefined;
    }

    // Forgotten user: skip the model and keep feed order.
    if (personalization === "off") {
      setState({
        status: "off",
        ranked: articles.map((article) => ({ article })),
        meta: null,
        error: null,
      });
      return undefined;
    }

    if (personalization !== "on") return undefined; // still loading, or API offline

    let cancelled = false;
    const pool = articles.slice(0, 100);
    const byId = new Map(pool.map((a) => [a.news_id, a]));

    setState((s) => ({ ...s, status: "loading", error: null }));

    api
      .recommend({
        userId,
        candidateIds: pool.map((a) => a.news_id),
        topK: pool.length,
      })
      .then((res) => {
        if (cancelled) return;

        const seen = new Set();
        const ordered = [];
        for (const r of res.recommendations) {
          const article = byId.get(r.news_id);
          if (article && !seen.has(article.news_id)) {
            seen.add(article.news_id);
            ordered.push({ article, score: r.score });
          }
        }
        // Candidates the model did not return keep their pool order at the end.
        for (const article of pool) {
          if (!seen.has(article.news_id)) ordered.push({ article, score: 0 });
        }

        const scopeKey = `${userId}|${scope}`;
        const prev = readPrev(scopeKey);
        const ranked = ordered.map((item, index) => {
          const before = prev.indexOf(item.article.news_id);
          return { ...item, delta: before === -1 ? null : before - index };
        });
        writePrev(
          scopeKey,
          ranked.map((r) => r.article.news_id),
        );

        setState({
          status: "ready",
          ranked,
          meta: {
            usedLong: res.used_long_term,
            usedShort: res.used_short_term,
            modelVersion: res.model_version,
          },
          error: null,
        });
      })
      .catch((err) => {
        if (!cancelled)
          setState({
            status: "error",
            ranked: [],
            meta: null,
            error: err.message,
          });
      });

    return () => {
      cancelled = true;
    };
  }, [articles, userId, personalization, scope, nonce]);

  return { ...state, refresh: () => setNonce((n) => n + 1) };
}
