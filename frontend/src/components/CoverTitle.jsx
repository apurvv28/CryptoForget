import { useState } from "react";
import { categoryLabel, toneFor } from "../cryptoforge/lib/format";
import { useApp } from "../cryptoforge/state/AppState";

// Images narrower than this are tracking pixels / icons, not story photos.
const MIN_IMAGE_WIDTH = 120;

/*
 * Category-based fallback images.
 *
 * These are only used when the actual news article does not provide
 * a usable image.
 *
 * Each category has multiple images so different articles can get
 * different fallback images.
 */
const FALLBACK_IMAGES = {
  technology: [
    "https://loremflickr.com/900/600/technology,computer",
    "https://loremflickr.com/900/600/technology,software",
    "https://loremflickr.com/900/600/technology,artificial-intelligence",
    "https://loremflickr.com/900/600/technology,computer,server",
  ],

  business: [
    "https://loremflickr.com/900/600/business,finance",
    "https://loremflickr.com/900/600/business,stock-market",
    "https://loremflickr.com/900/600/business,office",
    "https://loremflickr.com/900/600/finance,money",
  ],

  sports: [
    "https://loremflickr.com/900/600/sports",
    "https://loremflickr.com/900/600/football,soccer",
    "https://loremflickr.com/900/600/cricket",
    "https://loremflickr.com/900/600/tennis",
  ],

  science: [
    "https://loremflickr.com/900/600/science,laboratory",
    "https://loremflickr.com/900/600/science,space",
    "https://loremflickr.com/900/600/science,research",
    "https://loremflickr.com/900/600/technology,science",
  ],

  health: [
    "https://loremflickr.com/900/600/health,medicine",
    "https://loremflickr.com/900/600/medical,hospital",
    "https://loremflickr.com/900/600/doctor,health",
    "https://loremflickr.com/900/600/medicine",
  ],

  entertainment: [
    "https://loremflickr.com/900/600/entertainment,movie",
    "https://loremflickr.com/900/600/music,concert",
    "https://loremflickr.com/900/600/cinema",
    "https://loremflickr.com/900/600/celebrity",
  ],

  technology: [
    "https://loremflickr.com/900/600/technology,computer",
    "https://loremflickr.com/900/600/technology,software",
    "https://loremflickr.com/900/600/technology,artificial-intelligence",
    "https://loremflickr.com/900/600/technology,computer,server",
  ],

  general: [
    "https://loremflickr.com/900/600/news,newspaper",
    "https://loremflickr.com/900/600/news,journalism",
    "https://loremflickr.com/900/600/news,media",
    "https://loremflickr.com/900/600/world,news",
  ],
};


/*
 * Returns a deterministic fallback image.
 *
 * We use the news_id/title so the same article keeps the same image
 * instead of changing every time React renders.
 */
function getFallbackImage(article) {
  const category = String(
    article?.category || article?.subcategory || "general"
  ).toLowerCase();

  let key = "general";

  if (
    category.includes("tech") ||
    category.includes("ai") ||
    category.includes("software")
  ) {
    key = "technology";
  } else if (
    category.includes("business") ||
    category.includes("finance") ||
    category.includes("market")
  ) {
    key = "business";
  } else if (
    category.includes("sport") ||
    category.includes("cricket") ||
    category.includes("football")
  ) {
    key = "sports";
  } else if (
    category.includes("science") ||
    category.includes("research") ||
    category.includes("space")
  ) {
    key = "science";
  } else if (
    category.includes("health") ||
    category.includes("medical")
  ) {
    key = "health";
  } else if (
    category.includes("entertainment") ||
    category.includes("movie") ||
    category.includes("music")
  ) {
    key = "entertainment";
  }

  const images = FALLBACK_IMAGES[key];

  // Create a stable number from the article ID/title.
  const seed = String(
    article?.news_id || article?.title || Math.random()
  );

  let hash = 0;

  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }

  const index = Math.abs(hash) % images.length;

  return images[index];
}


export default function CoverTile({ article, size = "lg" }) {
  const { articleImages } = useApp() ?? {};

  /*
   * Priority:
   *
   * 1. Actual image returned with the article
   * 2. Image found by the progressive image resolver
   * 3. Category-related fallback image
   */
  const realImage =
    article?.image_url ||
    articleImages?.[article?.news_id] ||
    null;

  const fallbackImage = getFallbackImage(article);

  const [imageSrc, setImageSrc] = useState(realImage || fallbackImage);
  const [loadedSrc, setLoadedSrc] = useState(null);
  const [failedFallback, setFailedFallback] = useState(false);

  /*
   * If the actual article image fails:
   * switch to the category-related fallback.
   */
  const handleImageError = () => {
    if (imageSrc !== fallbackImage) {
      setImageSrc(fallbackImage);
      setLoadedSrc(null);
    } else {
      // Both actual and fallback images failed.
      setFailedFallback(true);
    }
  };

  const handleImageLoad = (event) => {
    const width = event.currentTarget.naturalWidth;

    if (width < MIN_IMAGE_WIDTH) {
      handleImageError();
      return;
    }

    setLoadedSrc(imageSrc);
  };

  const showImage = !failedFallback && Boolean(imageSrc);
  const isPhoto = showImage && loadedSrc === imageSrc;

  const hasSource =
    article?.is_live &&
    article?.subcategory &&
    article.subcategory !== "Live News";

  const tone = toneFor(
    hasSource ? article.subcategory : article.category
  );

  const initial = (
    (
      hasSource
        ? article.subcategory
        : categoryLabel(article.category)
    )
      .trim()[0] || "?"
  ).toUpperCase();

  return (
    <div
      className={`cf-cover cf-cover--${size}${
        isPhoto ? " cf-cover--photo" : ""
      }`}
      style={{
        "--cover-bg": tone.bg,
        "--cover-fg": tone.fg,
      }}
      aria-hidden="true"
    >
      {size !== "sm" && (
        <span className="cf-cover__label">
          {categoryLabel(article.category)}
        </span>
      )}

      <span className="cf-cover__initial">
        {initial}
      </span>

      {showImage && (
        <img
          className="cf-cover__img"
          src={imageSrc}
          alt=""
          loading="lazy"
          decoding="async"
          referrerPolicy="no-referrer"
          onLoad={handleImageLoad}
          onError={handleImageError}
        />
      )}
    </div>
  );
}