import { useEffect, useState } from "react";
import { api } from "../cryptoforge/api/client";
import { useApp } from "../cryptoforge/state/AppState";

export function useArticlePool({ source, category, search, limit = 40 }) {
  const { health, cacheArticles } = useApp();
  const [state, setState] = useState({
    status: "loading",
    articles: [],
    error: null,
  });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (health.online === null) return undefined; // wait for the first health check
    if (health.online === false) {
      setState({
        status: "error",
        articles: [],
        error:
          "Cannot reach the CryptoForget API. Start the backend and try again.",
      });
      return undefined;
    }

    const controller = new AbortController();
    const opts = { signal: controller.signal };
    const cat = category && category !== "all" ? category : undefined;

    setState((s) => ({ ...s, status: "loading", error: null }));

    const request =
      source === "live"
        ? api.liveNews({ category: cat, limit }, opts)
        : api.mindNews({ category: cat, search, limit }, opts);

    request
      .then((data) => {
        const articles = (data.articles || []).filter(
          (a) => a.news_id && a.title,
        );
        cacheArticles(articles);
        setState({
          status: articles.length ? "ready" : "empty",
          articles,
          error: null,
        });
      })
      .catch((err) => {
        if (err.name === "AbortError") return;
        setState({ status: "error", articles: [], error: err.message });
      });

    return () => controller.abort();
  }, [source, category, search, limit, nonce, health.online, cacheArticles]);

  return { ...state, reload: () => setNonce((n) => n + 1) };
}
