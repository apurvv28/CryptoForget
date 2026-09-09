from fastapi import FastAPI, HTTPException

from app.model_state import MODEL_VERSION, get_service
from app.schemas import (
    ClickAck,
    ClickEvent,
    RankedNews,
    RecommendRequest,
    RecommendResponse,
)

app = FastAPI(
    title="CryptoForget Recommendation Service",
    description=(
        "Serves the dynamic (long-term + short-term) content-based news "
        "recommendation model over HTTP."
    ),
    version=MODEL_VERSION,
)


@app.on_event("startup")
def load_model() -> None:
    # Fails fast at container startup if artifacts are missing, instead of
    # failing on the first request.
    get_service()


@app.get("/health")
def health():
    svc = get_service()
    return {
        "status": "ok",
        "model_version": MODEL_VERSION,
        "known_users": len(svc.user_histories),
        "content_vector_dim": svc.content_model.get_dimension(),
    }


@app.post("/clicks", response_model=ClickAck)
def record_click(event: ClickEvent):
    svc = get_service()
    total = svc.record_click(event.user_id, event.news_id, event.time)
    return ClickAck(
        status="recorded",
        user_id=event.user_id,
        news_id=event.news_id,
        total_clicks_for_user=total,
    )


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    svc = get_service()
    try:
        result = svc.recommend(
            user_id=req.user_id,
            candidate_news_ids=req.candidate_news_ids,
            top_k=req.top_k,
            history_override=req.history,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return RecommendResponse(
        user_id=req.user_id,
        recommendations=[
            RankedNews(news_id=news_id, score=score)
            for news_id, score in result["ranked"]
        ],
        model_version=MODEL_VERSION,
        used_long_term=result["used_long_term"],
        used_short_term=result["used_short_term"],
    )
