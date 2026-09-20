import { useEffect, useState } from "react";
import ArticleCard from "../../components/ArticleCard";
import Icon from "../../components/Icon";
import SourceToggle from "../../components/SourceToggle";
import { EmptyState, ErrorState, SkeletonGrid } from "../../components/States";
import { useArticlePool } from "../../hooks/useArticlePool";
import { categoriesFor } from "../lib/categories";
import { toneFor } from "../lib/format";
import { navigate, useLocation } from "../router/router";

// The backend filters with a regex (str.contains), so escape the user's text.
const escapeRegex = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export default function ExplorePage() {
  const { query } = useLocation();
  const q = (query.q || "").trim();
  const source = q || query.source === "mind" ? "mind" : "live";
  const cat = query.cat || "all";
  const [term, setTerm] = useState(q);

  useEffect(() => setTerm(q), [q]);

  const go = (next) => {
    const merged = { source, cat, q, ...next };
    const params = new URLSearchParams();
    if (merged.source === "mind") params.set("source", "mind");
    if (merged.cat && merged.cat !== "all") params.set("cat", merged.cat);
    if (merged.q) params.set("q", merged.q);
    const qs = params.toString();
    navigate(`/explore${qs ? `?${qs}` : ""}`, { replace: true });
  };

  const pool = useArticlePool({
    source,
    category: cat,
    search: source === "mind" && q ? escapeRegex(q) : undefined,
    limit: 60,
  });

  const submit = (e) => {
    e.preventDefault();
    go({ source: "mind", q: term.trim() });
  };

  const cats = categoriesFor(source);
  const activeLabel = cats.find((c) => c.id === cat)?.label;

  let body;
  if (pool.status === "error") {
    body = (
      <ErrorState
        title="Could not load articles"
        message={
          q && pool.error.includes("500")
            ? `${pool.error}. The catalog search failed on the server; try a different term.`
            : pool.error
        }
        onRetry={pool.reload}
      />
    );
  } else if (pool.status === "empty") {
    body = (
      <EmptyState title="Nothing found">
        {q
          ? `No MIND articles match “${q}”.`
          : "No articles in this category right now."}
      </EmptyState>
    );
  } else if (pool.status === "loading") {
    body = <SkeletonGrid count={6} variant="row" />;
  } else {
    body = (
      <>
        <div className="cf-section-head">
          <h2>{q ? `Results for “${q}”` : activeLabel || "Articles"}</h2>
          <span className="cf-chip">
            {pool.articles.length} articles, not personalized
          </span>
        </div>
        <div className="cf-grid-rows">
          {pool.articles.map((a) => (
            <ArticleCard key={a.news_id} article={a} variant="row" />
          ))}
        </div>
        {source === "mind" && pool.articles.length >= 60 && (
          <p className="cf-fine">Showing the first 60 matches.</p>
        )}
      </>
    );
  }

  return (
    <div>
      <header className="cf-page-head">
        <h1>Explore</h1>
        <p>
          Browse by category
          {source === "mind" ? " or search the MIND catalog" : ""}. These
          results are not personalized, so opening an article here still records
          a click for the current user.
        </p>
      </header>

      <div className="cf-toolbar">
        <SourceToggle
          value={source}
          onChange={(s) =>
            go({ source: s, cat: "all", q: s === "live" ? "" : q })
          }
        />
        {source === "mind" ? (
          <form className="cf-search" onSubmit={submit} role="search">
            <Icon name="search" size={18} />
            <input
              type="search"
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="Search titles and abstracts"
              aria-label="Search the MIND catalog"
            />
          </form>
        ) : (
          <span className="cf-chip">
            Search is available in the MIND catalog
          </span>
        )}
      </div>

      <div className="cf-topics" role="group" aria-label="Categories">
        {cats.map((c) => {
          const tone = toneFor(c.label);
          return (
            <button
              key={c.id}
              type="button"
              className="cf-topic"
              style={{ "--tone-bg": tone.bg, "--tone-fg": tone.fg }}
              aria-pressed={cat === c.id}
              onClick={() => go({ cat: c.id })}
            >
              {c.label}
            </button>
          );
        })}
      </div>

      {body}
    </div>
  );
}
