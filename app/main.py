import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.model_state import MODEL_VERSION, get_service
from app.routers import auditor, news, unlearning, users
from app.schemas import (
    ClickAck,
    ClickEvent,
    RankedNews,
    RecommendRequest,
    RecommendResponse,
)
from src.db.database import init_db

app = FastAPI(
    title="CryptoForget — Verifiable Machine Unlearning Platform API",
    description=(
        "Production REST framework integrating sharded SISA machine unlearning, "
        "Merkle exclusion proofs, ECDSA deletion certificates, and append-only audit logging."
    ),
    version=MODEL_VERSION,
)

# Enable CORS for React frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(news.router)
app.include_router(users.router)
app.include_router(unlearning.router)
app.include_router(auditor.router)

# Mount static frontend build if present
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="static_assets")

    @app.get("/", include_in_schema=False)
    def serve_frontend_dashboard():
        return FileResponse(FRONTEND_DIST / "index.html")


@app.on_event("startup")
def startup_event() -> None:
    # Initialize database tables
    init_db()
    # Pre-load recommendation model service
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
