"""
API Router — aggregates all v1 endpoint routers.

Routers will be added as each phase is implemented.
"""

from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.consent import router as consent_router
from app.api.v1.data_inventory import router as inventory_router
from app.api.v1.deletion import router as deletion_router
from app.api.v1.certificates import router as certificates_router
from app.api.v1.transparency import router as transparency_router

api_router = APIRouter(prefix="/api/v1")

# Phase 1: Chat
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])

# Phase 2: Consent & Data Inventory
api_router.include_router(consent_router, prefix="/consent", tags=["consent"])
api_router.include_router(inventory_router, prefix="/data-inventory", tags=["inventory"])

# Phase 5: Deletion & Pre-Tombstoning (RC2)
api_router.include_router(deletion_router, prefix="/deletion-requests", tags=["deletion"])

# Phase 7: Certificates & Merkle Transparency Log (RC1)
api_router.include_router(certificates_router, prefix="/certificates", tags=["certificates"])
api_router.include_router(transparency_router, prefix="/transparency", tags=["transparency"])

# Phase 1: Auth
# from app.api.v1.auth import router as auth_router
# api_router.include_router(auth_router, prefix="/auth", tags=["auth"])

# Phase 2: Consent
# from app.api.v1.consent import router as consent_router
# api_router.include_router(consent_router, prefix="/consent", tags=["consent"])

# Phase 5: Deletion
# from app.api.v1.deletion import router as deletion_router
# api_router.include_router(deletion_router, prefix="/deletion-requests", tags=["deletion"])

# Phase 7: Certificates
# from app.api.v1.certificates import router as certificates_router
# api_router.include_router(certificates_router, prefix="/certificates", tags=["certificates"])
