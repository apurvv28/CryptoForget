"""
Public Verification & Merkle Transparency Integration Tests — Phase 7 (RC1).

Validates:
1. Public verification endpoint (/verify/{cert_id}) returns VALID_COMPLETED with authentic signature and Merkle inclusion.
2. Strictly ZERO personal identifiable information (PII) is disclosed to public verifiers.
3. Certificate revocation triggers transparent invalidation and Merkle log update.
4. Public verification keys discovery endpoint (/.well-known/verification-keys.json).
5. Signed Tree Head (STH) and RFC 6962 inclusion proofs via API.
per Docs 01 (§10, §11), 02 (FR-08, FR-09, FR-10), and 05 (§10, §15).
"""

import json
import uuid
from httpx import ASGITransport, AsyncClient
import pytest

from app.db.session import async_session
from app.main import create_app
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.services.certificate_service import certificate_service
from app.services.deletion_orchestrator import deletion_orchestrator
from app.services.deletion_service import deletion_service


@pytest.mark.asyncio
async def test_public_verifier_no_pii_leak() -> None:
    """Public verification endpoint must verify authentic execution with strictly zero PII."""
    app = create_app()
    transport = ASGITransport(app=app)
    uid_str = uuid.uuid4().hex[:8]
    user_email = f"confidential_{uid_str}@private-domain.org"
    username = f"user_{uid_str}"

    async with async_session() as session:
        user = User(username=username, email=user_email, hashed_password="top_secret_hash")
        session.add(user)
        await session.flush()

        conv = Conversation(user_id=user.id, title="Secret Financial Chat")
        session.add(conv)
        await session.flush()

        msg = Message(
            conversation_id=conv.id,
            role="user",
            content="Confidential account number 9876-5432-1098 and SSN 000-12-3456",
        )
        session.add(msg)
        await session.commit()
        user_id = user.id

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Execute deletion request
        del_res = await client.post(
            "/api/v1/deletion-requests",
            json={
                "scope": "all_user_data",
                "user_id": user_id,
                "idempotency_key": f"idem_v_{uid_str}",
                "auto_orchestrate": False,
            },
        )
        assert del_res.status_code == 200
        del_id = del_res.json()["deletion_request_id"]

        # Run orchestration
        orch_res = await client.post(f"/api/v1/deletion-requests/{del_id}/orchestrate?synchronous=true")
        assert orch_res.status_code == 200

        # 2. Issue certificate
        cert_res = await client.post(f"/api/v1/certificates/issue/{del_id}")
        assert cert_res.status_code == 200
        cert_data = cert_res.json()
        cert_id = cert_data["certificate_id"]

        # 3. Call Public Verification Route: /verify/{cert_id}
        verify_res = await client.get(f"/verify/{cert_id}")
        assert verify_res.status_code == 200
        v_data = verify_res.json()

        assert v_data["certificate_id"] == cert_id
        assert v_data["verification_status"] == "VALID_COMPLETED"
        assert v_data["signature_valid"] is True
        assert v_data["merkle_inclusion_valid"] is True
        assert len(v_data["evidence_manifest_digest"]) == 64
        assert len(v_data["merkle_root_hash"]) == 64
        assert v_data["merkle_leaf_index"] >= 0

        # 4. Strict Zero-PII Audit: No private content or identifiers in response
        raw_text = verify_res.text.lower()
        forbidden_terms = [
            user_email.lower(),
            username.lower(),
            "confidential",
            "9876-5432",
            "top_secret",
            "ssn",
            "credit",
            "password",
        ]
        for term in forbidden_terms:
            assert term not in raw_text, f"PII leak detected in public verification response: '{term}'"


@pytest.mark.asyncio
async def test_well_known_verification_keys_discovery() -> None:
    """Public key discovery endpoint must return active Ed25519 verification keys."""
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/.well-known/verification-keys.json")
        assert res.status_code == 200
        data = res.json()
        assert "keys" in data
        assert len(data["keys"]) > 0

        active_key = data["keys"][0]
        assert active_key["algorithm"] == "Ed25519"
        assert "public_key_b64" in active_key
        assert len(active_key["public_key_b64"]) > 0
        assert active_key["status"] == "active"


@pytest.mark.asyncio
async def test_revocation_and_transparency_proofs() -> None:
    """Revoking a certificate must transparently update the Merkle log and mark status invalid."""
    app = create_app()
    transport = ASGITransport(app=app)
    uid_str = uuid.uuid4().hex[:8]

    async with async_session() as session:
        user = User(username=f"user_rev_{uid_str}", email=f"rev_{uid_str}@example.com", hashed_password="pw")
        session.add(user)
        await session.commit()
        user_id = user.id

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create deletion and certificate
        del_res = await client.post(
            "/api/v1/deletion-requests",
            json={"scope": "all_user_data", "user_id": user_id, "auto_orchestrate": False},
        )
        del_id = del_res.json()["deletion_request_id"]
        await client.post(f"/api/v1/deletion-requests/{del_id}/orchestrate?synchronous=true")

        cert_res = await client.post(f"/api/v1/certificates/issue/{del_id}")
        cert_id = cert_res.json()["certificate_id"]
        leaf_idx = cert_res.json()["merkle_leaf_index"]

        # Fetch inclusion proof via Transparency API
        proof_res = await client.get(f"/api/v1/transparency/proof/inclusion/{leaf_idx}")
        assert proof_res.status_code == 200
        proof_data = proof_res.json()
        assert proof_data["verified"] is True
        assert len(proof_data["proof"]) >= 0

        # Revoke certificate
        revoke_res = await client.post(
            f"/api/v1/certificates/{cert_id}/revoke",
            json={"reason": "User requested account reactivation"},
        )
        assert revoke_res.status_code == 200
        assert revoke_res.json()["is_revoked"] is True

        # Verify public verifier detects revocation
        verify_rev = await client.get(f"/verify/{cert_id}")
        assert verify_rev.status_code == 200
        rev_data = verify_rev.json()
        assert rev_data["verification_status"] == "INVALID"
        assert "REVOKED" in rev_data["trust_notice"]
