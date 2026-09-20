import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import CoverTile from "../../components/CoverTile";
import Icon from "../../components/Icon";
import { ErrorState } from "../../components/States";
import { articleMeta, articleSummary, categoryLabel } from "../lib/format";
import { Link, navigate } from "../router/router";
import { useApp } from "../state/AppState";

function InteractionCard({ click, userId }) {
  let chip = <span className="cf-chip">Sending…</span>;
  let text = "Sending this view to the recommendation service.";

  if (click.status === "recorded") {
    chip = <span className="cf-chip cf-chip--ok">Sent to the model</span>;
    text = `Recorded as a click for ${click.userId}. The backend now holds ${click.total} click${
      click.total === 1 ? "" : "s"
    } for this user.`;
  } else if (click.status === "skipped") {
    chip = <span className="cf-chip cf-chip--warn">Not sent</span>;
    text = `Personalization is off for ${userId}, so this view was not sent to the model.`;
  } else if (click.status === "error") {
    chip = <span className="cf-chip cf-chip--danger">Failed</span>;
    text = click.message;
  }

  return (
    <section className="cf-card cf-side-card" aria-live="polite">
      <h2>Model interaction</h2>
      {chip}
      <p>{text}</p>
      {click.status === "recorded" && (
        <>
          <p>
            Clicks from the last 24 hours shape the short-term profile, and
            newer clicks count more.
          </p>
          <Link to="/" className="cf-btn cf-btn--soft cf-btn--block">
            See how your feed changed
          </Link>
        </>
      )}
      <p className="cf-side-card__fine">
        The model learns from clicks only. Likes, saves and reading time are not
        used.
      </p>
    </section>
  );
}

export default function ArticlePage({ id }) {
  const {
    health,
    userId,
    personalization,
    recordClick,
    getCachedArticle,
    cacheArticles,
  } = useApp();
  const [article, setArticle] = useState(() => getCachedArticle(id) ?? null);
  const [loadError, setLoadError] = useState(null);
  const [click, setClick] = useState({ status: "idle" });
  const sentFor = useRef(null);

  // Load from the API when the article was not opened from a list (e.g. page refresh).
  useEffect(() => {
    if (article || health.online === null) return undefined;
    if (health.online === false) {
      setLoadError("Cannot reach the CryptoForget API.");
      return undefined;
    }
    let cancelled = false;
    api
      .getNews(id)
      .then((a) => {
        if (cancelled) return;
        cacheArticles([a]);
        setArticle(a);
      })
      .catch((err) => {
        if (!cancelled)
          setLoadError(err.status === 404 ? "not_found" : err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [id, article, health.online, cacheArticles]);

  // Opening an article = one click event for the current demo user.
  useEffect(() => {
    if (!article || personalization === "loading") return;
    if (sentFor.current === article.news_id) return;
    sentFor.current = article.news_id;

    if (personalization !== "on") {
      setClick({ status: "skipped" });
      return;
    }
    setClick({ status: "sending" });
    recordClick(article)
      .then((res) =>
        setClick(
          res.sent
            ? {
                status: "recorded",
                total: res.ack.total_clicks_for_user,
                userId: res.ack.user_id,
              }
            : { status: "skipped" },
        ),
      )
      .catch((err) => setClick({ status: "error", message: err.message }));
  }, [article, personalization, recordClick]);

  const goBack = () =>
    window.history.length > 1 ? window.history.back() : navigate("/");

  if (loadError) {
    return (
      <div>
        <button type="button" className="cf-back" onClick={goBack}>
          <Icon name="arrow-left" size={16} /> Back
        </button>
        <ErrorState
          title="Article not available"
          message={
            loadError === "not_found"
              ? "This article could not be found. Live articles are held in the backend’s memory and disappear when it restarts."
              : loadError
          }
        />
      </div>
    );
  }

  if (!article) {
    return (
      <div>
        <div
          className="cf-skeleton"
          style={{ height: 320, marginTop: 24 }}
          aria-busy="true"
        />
      </div>
    );
  }

  const meta = articleMeta(article);
  const summary = articleSummary(article, 400);

  return (
    <div>
      <button type="button" className="cf-back" onClick={goBack}>
        <Icon name="arrow-left" size={16} /> Back
      </button>

      <div className="cf-article">
        <article className="cf-article__main">
          <CoverTile article={article} size="xl" />
          <div className="cf-article__meta">
            <span className="cf-tag">{categoryLabel(article.category)}</span>
            {meta.map((m, i) => (
              <span key={`${m}-${i}`}>{m}</span>
            ))}
            <span>{article.is_live ? "Live news" : "MIND catalog"}</span>
          </div>
          <h1 className="cf-article__title">{article.title}</h1>
          {summary && <p className="cf-article__abstract">{summary}</p>}
          {article.url && (
            <div className="cf-article__actions">
              <a
                className="cf-btn cf-btn--primary"
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Icon name="external" size={16} /> Read on source
              </a>
            </div>
          )}
        </article>

        <aside className="cf-article__aside">
          <InteractionCard click={click} userId={userId} />
        </aside>
      </div>
    </div>
  );
}
