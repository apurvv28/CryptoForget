import { useEffect, useState } from "react";
import { api } from "../cryptoforge/api/client";
import { useApp } from "../cryptoforge/state/AppState";

// Live stories get their image resolved server-side; ask again while it finishes.
const IMAGE_POLL_DELAYS = [1500, 3000, 5000, 8000, 12000];

export function useArticlePool({ source, category, search, limit = 40 }) {
  const { health, cacheArticles, addArticleImages } = useApp();
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
    let timer = null;

    const pollImages = (ids, attempt) => {
      if (!ids.length || attempt >= IMAGE_POLL_DELAYS.length) return;
      timer = setTimeout(async () => {
        try {
          const res = await api.newsImages(ids, opts);
          if (res.images && Object.keys(res.images).length) {
            addArticleImages(res.images);
          }
          // `pending` is still resolving; `missing` has no image, keep its cover.
          pollImages(res.pending || [], attempt + 1);
        } catch {
          /* aborted or offline: images are optional, covers stay */
        }
      }, IMAGE_POLL_DELAYS[attempt]);
    };

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
        if (source === "live") {
          pollImages(
            articles.filter((a) => !a.image_url).map((a) => a.news_id),
            0,
          );
        }
      })
      .catch((err) => {
        if (err.name === "AbortError") return;
        setState({ status: "error", articles: [], error: err.message });
      });

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [
    source, category, search, limit, nonce, health.online,
    cacheArticles, addArticleImages,
  ]);

  return { ...state, reload: () => setNonce((n) => n + 1) };
}
