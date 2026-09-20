import {
  articleMeta,
  articleSummary,
  categoryLabel,
} from "../cryptoforge/lib/format";
import { Link } from "../cryptoforge/router/router";
import CoverTile from "./CoverTile";
import ScoreBar from "./ScoreBar";

// variant: 'feature' (large, cover on top) | 'row' (compact, cover on the left)
export default function ArticleCard({
  article,
  variant = "row",
  score,
  maxScore,
  delta,
}) {
  const to = `/article/${encodeURIComponent(article.news_id)}`;
  const meta = articleMeta(article);
  const summary = variant === "feature" ? articleSummary(article) : "";

  return (
    <article className={`cf-article-card cf-article-card--${variant}`}>
      <Link to={to} className="cf-article-card__link">
        <CoverTile
          article={article}
          size={variant === "feature" ? "lg" : "sm"}
        />
        <div className="cf-article-card__body">
          <div className="cf-article-card__meta">
            <span className="cf-tag">{categoryLabel(article.category)}</span>
            {meta.map((m, i) => (
              <span key={`${m}-${i}`}>{m}</span>
            ))}
          </div>
          <h3 className="cf-article-card__title">{article.title}</h3>
          {summary && <p className="cf-article-card__summary">{summary}</p>}
          {typeof score === "number" && (
            <ScoreBar score={score} max={maxScore} delta={delta} />
          )}
        </div>
      </Link>
    </article>
  );
}
