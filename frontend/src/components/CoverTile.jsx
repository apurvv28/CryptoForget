import { categoryLabel, toneFor } from "../cryptoforge/lib/format";

export default function CoverTile({ article, size = "lg" }) {
  const hasSource =
    article.is_live &&
    article.subcategory &&
    article.subcategory !== "Live News";
  const tone = toneFor(hasSource ? article.subcategory : article.category);
  const initial = (
    (hasSource
      ? article.subcategory
      : categoryLabel(article.category)
    ).trim()[0] || "?"
  ).toUpperCase();

  return (
    <div
      className={`cf-cover cf-cover--${size}`}
      style={{ "--cover-bg": tone.bg, "--cover-fg": tone.fg }}
      aria-hidden="true"
    >
      {size !== "sm" && (
        <span className="cf-cover__label">
          {categoryLabel(article.category)}
        </span>
      )}
      <span className="cf-cover__initial">{initial}</span>
    </div>
  );
}
