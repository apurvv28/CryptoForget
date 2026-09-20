import ArticleCard from "../../components/ArticleCard";
import Icon from "../../components/Icon";
import { EmptyState, ErrorState, SkeletonGrid } from "../../components/States";
import { useArticlePool } from "../../hooks/useArticlePool";

export default function HeadlinesPage() {
  const pool = useArticlePool({ source: "live", category: "all", limit: 30 });
  const featured = pool.articles.slice(0, 3);
  const rest = pool.articles.slice(3);

  let body;
  if (pool.status === "error") {
    body = (
      <ErrorState
        title="Could not load headlines"
        message={pool.error}
        onRetry={pool.reload}
      />
    );
  } else if (pool.status === "empty") {
    body = (
      <EmptyState title="No headlines returned">
        The backend could not fetch the live RSS feed. It needs internet access.
      </EmptyState>
    );
  } else if (pool.status === "loading") {
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
        <section className="cf-section cf-section--first">
          <div className="cf-section-head">
            <h2>Featured</h2>
          </div>
          <div className="cf-grid-feature">
            {featured.map((a) => (
              <ArticleCard key={a.news_id} article={a} variant="feature" />
            ))}
          </div>
        </section>
        {rest.length > 0 && (
          <section className="cf-section">
            <div className="cf-section-head">
              <h2>Today's headlines</h2>
            </div>
            <div className="cf-grid-rows">
              {rest.map((a) => (
                <ArticleCard key={a.news_id} article={a} variant="row" />
              ))}
            </div>
          </section>
        )}
      </>
    );
  }

  return (
    <div>
      <header className="cf-page-head">
        <h1>Headlines</h1>
        <p>
          Latest headlines from Google News RSS, fetched by the backend. Not
          personalized and not ranked by popularity.
        </p>
      </header>

      <div className="cf-toolbar">
        <span className="cf-chip">Not personalized</span>
        <button
          type="button"
          className="cf-btn cf-btn--ghost"
          onClick={pool.reload}
        >
          <Icon name="refresh" size={16} /> Refresh
        </button>
      </div>

      {body}
    </div>
  );
}
