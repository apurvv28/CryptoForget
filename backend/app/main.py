"""
CryptoForget FastAPI Application Entry Point.

Privacy-Preserving Conversational AI with SISA Unlearning
and Verifiable Deletion.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.db.base import Base
from app.db.session import engine
import app.models  # Register all ORM models with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle."""
    # Ensure SQLite tables exist on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CryptoForget",
        description="Privacy-Preserving Conversational AI with SISA Unlearning",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "model": "distilgpt2-82M"}

    # Phase 7: Public Key Discovery (RFC 8032 / Doc 01 §11)
    @app.get("/.well-known/verification-keys.json")
    async def get_verification_keys():
        from app.crypto.signing import key_manager
        return key_manager.get_verification_keys_doc()

    # Phase 7: Public Certificate Verification (Doc 01 §10, Doc 05 §10)
    @app.get("/verify/{certificate_id}")
    @app.get("/api/v1/verify/{certificate_id}")
    async def verify_certificate_endpoint(certificate_id: str):
        from app.db.session import async_session
        from app.services.certificate_service import certificate_service
        async with async_session() as session:
            return await certificate_service.verify_public_certificate(
                certificate_id=certificate_id,
                db=session,
            )

    # Register API routers
    app.include_router(api_router)

    return app


app = create_app()
