import ArticleCard from "../../components/ArticleCard";
import CategoryChips from "../../components/CategoryChips";
import Icon from "../../components/Icon";
import SourceToggle from "../../components/SourceToggle";
import { EmptyState, ErrorState, SkeletonGrid } from "../../components/States";
import { useArticlePool } from "../../hooks/useArticlePool";
import { useRanking } from "../../hooks/useRanking";
import { categoriesFor } from "../lib/categories";
import { useSessionState } from "../lib/useSessionState";
import { useApp } from "../state/AppState";

export default function HomePage() {
  const { userId, personalization, userError } = useApp();
  const [source, setSource] = useSessionState("cf.home.source", "live");
  const [category, setCategory] = useSessionState("cf.home.category", "all");

  const pool = useArticlePool({
    source,
    category,
    limit: source === "live" ? 40 : 60,
  });
  const ranking = useRanking({
    articles: pool.articles,
    scope: `${source}|${category}`,
  });

  const changeSource = (next) => {
    setSource(next);
    setCategory("all");
  };

  const rankingFailed = ranking.status === "error";
  const items = rankingFailed
    ? pool.articles.map((article) => ({ article }))
    : ranking.ranked;
  const meta = ranking.meta;
  const coldStart =
    ranking.status === "ready" && meta && !meta.usedLong && !meta.usedShort;
  const personalized = ranking.status === "ready" && !coldStart;
  const maxScore = personalized
    ? Math.max(...items.map((i) => i.score ?? 0), 0)
    : 0;

  const feature = items.slice(0, 3);
  const rest = items.slice(3);
  const card = (item, variant) => (
    <ArticleCard
      key={item.article.news_id}
      article={item.article}
      variant={variant}
      score={personalized ? item.score : undefined}
      maxScore={maxScore}
      delta={item.delta}
    />
  );

  let body;
  if (personalization === "loading" && userError) {
    body = (
      <ErrorState title={`Could not load ${userId}`} message={userError} />
    );
  } else if (pool.status === "error") {
    body = (
      <ErrorState
        title="Could not load articles"
        message={pool.error}
        onRetry={pool.reload}
      />
    );
  } else if (pool.status === "empty") {
    body = (
      <EmptyState
        title="No articles returned"
        action={
          source === "live" ? (
            <button
              type="button"
              className="cf-btn cf-btn--soft"
              onClick={() => changeSource("mind")}
            >
              Switch to the MIND catalog
            </button>
          ) : null
        }
      >
        {source === "live"
          ? "The backend could not fetch live headlines (it needs internet access). The MIND catalog works offline."
          : "No articles match this category."}
      </EmptyState>
    );
  } else if (pool.status === "loading" || items.length === 0) {
    body = (
      <>
        <SkeletonGrid count={3} variant="feature" />
        <div className="cf-section">
          <SkeletonGrid count={6} variant="row" />
        </div>
      </>
    );
  } else {
    body = (
      <>
        {personalization === "off" && (
          <div className="cf-notice cf-notice--warn cf-mb">
            <Icon name="shield-check" />
            <div>
              <strong>Personalization is off for {userId}.</strong> This user's
              data was forgotten, so this feed skips the recommendation model
              and shows articles in feed order.
            </div>
          </div>
        )}

        {coldStart && (
          <div className="cf-notice cf-mb">
            <Icon name="info" />
            <div>
              <strong>No profile signal for {userId} yet.</strong> The model has
              no history and no recorded clicks for this user, so every score is
              0 and the order below is the original feed order. Open a few
              articles, then come back to see the ranking change.
            </div>
          </div>
        )}

        {rankingFailed && (
          <div className="cf-notice cf-notice--danger cf-mb">
            <Icon name="alert" />
            <div>
              <strong>Ranking failed.</strong> {ranking.error} Showing articles
              in feed order.{" "}
              <button
                type="button"
                className="cf-linkbtn"
                onClick={ranking.refresh}
              >
                Retry ranking
              </button>
            </div>
          </div>
        )}

        {ranking.status === "ready" && meta && (
          <div className="cf-signals">
            <span
              className={`cf-chip ${meta.usedLong ? "cf-chip--ok" : ""}`}
              title="True when the model found a MIND click history for this user."
            >
              Long-term profile:{" "}
              {meta.usedLong ? "history found" : "no history"}
            </span>
            <span
              className={`cf-chip ${meta.usedShort ? "cf-chip--ok" : ""}`}
              title="True when the backend holds clicks for this user. The model weights clicks from the last 24 hours."
            >
              Short-term signal:{" "}
              {meta.usedShort ? "clicks recorded" : "none yet"}
            </span>
            <span className="cf-chip">Model {meta.modelVersion}</span>
            <span className="cf-chip">{items.length} candidates ranked</span>
          </div>
        )}

        <section className="cf-section cf-section--first">
          <div className="cf-section-head">
            <h2>{personalized ? "Top picks for you" : "Top of the feed"}</h2>
          </div>
          <div className="cf-grid-feature">
            {feature.map((item) => card(item, "feature"))}
          </div>
        </section>

        {rest.length > 0 && (
          <section className="cf-section">
            <div className="cf-section-head">
              <h2>{personalized ? "More for you" : "More articles"}</h2>
            </div>
            <div className="cf-grid-rows">
              {rest.map((item) => card(item, "row"))}
            </div>
          </section>
        )}
      </>
    );
  }

  return (
    <div>
      <header className="cf-page-head">
        <h1>For you</h1>
        <p>
          Articles ranked by the dynamic long-term and short-term profile of{" "}
          <strong>{userId}</strong>. Each open counts as a click the model can
          learn from.
        </p>
      </header>

      <div className="cf-toolbar">
        <SourceToggle value={source} onChange={changeSource} />
        <button
          type="button"
          className="cf-btn cf-btn--ghost"
          onClick={pool.reload}
        >
          <Icon name="refresh" size={16} /> Refresh ranking
        </button>
      </div>

      <CategoryChips
        options={categoriesFor(source)}
        value={category}
        onChange={setCategory}
      />

      {body}
    </div>
  );
}
