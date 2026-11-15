"""Public verification API endpoints — Phase 7."""

from fastapi import APIRouter

router = APIRouter()

# GET /verify/{certificate_id} — Public verification page (Phase 7)
# GET /.well-known/verification-keys.json — Public signing keys (Phase 7)
# GET /api/v1/transparency/{id} — Public audit inclusion proof (Phase 7)
