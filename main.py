"""
CryptoForget Serving Entrypoint

Allows running the FastAPI recommendation service directly from the project root:
    uvicorn main:app --reload
"""

from app.main import app

__all__ = ["app"]
