from typing import Any, Dict, List, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.config import DATA_DIR
from src.data.live_news import fetch_live_news_articles
from src.data.loader import load_news

router = APIRouter(prefix="/api/v1/news", tags=["News Catalog"])

# Cache loaded news dataframe
_news_df_cache: Optional[pd.DataFrame] = None
_live_articles_store: Dict[str, Dict[str, Any]] = {}


def get_cached_news_df() -> pd.DataFrame:
    global _news_df_cache
    if _news_df_cache is None:
        try:
            _news_df_cache = load_news(str(DATA_DIR))
        except Exception:
            _news_df_cache = pd.DataFrame(columns=["news_id", "category", "subcategory", "title", "abstract", "url"])
    return _news_df_cache


@router.get("/live", response_model=Dict[str, Any])
def get_live_news(
    category: Optional[str] = Query(None, description="Category filter (technology, business, sports, etc.)"),
    limit: int = Query(25, ge=1, le=100),
):
    """Fetches real-time live news articles from global RSS feeds and indexes them for model vectorization."""
    from app.model_state import get_service

    live_articles = fetch_live_news_articles(category=category, limit=limit)
    svc = get_service()

    # Dynamically vectorize live articles into the TF-IDF recommendation model
    for item in live_articles:
        _live_articles_store[item["news_id"]] = item
        svc.content_model.add_dynamic_article(
            news_id=item["news_id"],
            title=item["title"],
            abstract=item["abstract"],
        )

    return {
        "status": "success",
        "category": category or "all",
        "total": len(live_articles),
        "articles": live_articles,
    }


@router.get("", response_model=Dict[str, Any])
def list_news(
    category: Optional[str] = Query(None, description="Filter by category (e.g. news, sports, finance)"),
    search: Optional[str] = Query(None, description="Search in title or abstract"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_live: bool = Query(True, description="Blend real-time live RSS news articles"),
):
    """Returns paginated news articles, blending MIND dataset catalog with real-time live RSS news."""
    from app.model_state import get_service

    df = get_cached_news_df()
    live_items = []

    if include_live:
        try:
            live_items = fetch_live_news_articles(category=category, limit=10)
            svc = get_service()
            for item in live_items:
                _live_articles_store[item["news_id"]] = item
                svc.content_model.add_dynamic_article(
                    news_id=item["news_id"],
                    title=item["title"],
                    abstract=item["abstract"],
                )
        except Exception:
            live_items = []

    clean_articles = []
    # Prepend live articles if offset is 0
    if offset == 0 and live_items:
        clean_articles.extend(live_items[:5])

    if not df.empty:
        filtered = df
        if category and category.lower() != "all":
            filtered = filtered[filtered["category"].str.lower() == category.lower()]

        if search:
            search_lower = search.lower()
            filtered = filtered[
                filtered["title"].str.lower().str.contains(search_lower)
                | filtered["abstract"].str.lower().str.contains(search_lower)
            ]

        page_items = filtered.iloc[offset : offset + limit].to_dict(orient="records")

        for item in page_items:
            clean_articles.append({
                "news_id": str(item.get("news_id", "")),
                "category": str(item.get("category", "General")),
                "subcategory": str(item.get("subcategory", "")),
                "title": str(item.get("title", "")),
                "abstract": str(item.get("abstract", "")),
                "url": str(item.get("url", "")),
                "is_live": False,
            })

    return {
        "total": len(clean_articles),
        "offset": offset,
        "limit": limit,
        "articles": clean_articles,
    }


@router.get("/{news_id}", response_model=Dict[str, Any])
def get_news_article(news_id: str):
    """Retrieves details for a single news article (MIND catalog or Live RSS)."""
    if news_id in _live_articles_store:
        item = _live_articles_store[news_id]
        return {
            "news_id": item["news_id"],
            "category": item.get("category", "General"),
            "subcategory": item.get("subcategory", "Live News"),
            "title": item.get("title", ""),
            "abstract": item.get("abstract", ""),
            "url": item.get("url", ""),
            "is_live": True,
        }

    df = get_cached_news_df()
    match = df[df["news_id"] == news_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"News article {news_id} not found.")

    row = match.iloc[0].to_dict()
    return {
        "news_id": str(row.get("news_id", "")),
        "category": str(row.get("category", "General")),
        "subcategory": str(row.get("subcategory", "")),
        "title": str(row.get("title", "")),
        "abstract": str(row.get("abstract", "")),
        "url": str(row.get("url", "")),
        "is_live": False,
    }
