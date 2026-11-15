"""
Consent Service — Manages immutable consent events and training eligibility.

Enforces:
1. Consent defaults to OFF (Doc 02 FR-03).
2. Explicit, affirmative, versioned consent events (Doc 05 §3).
3. Immediate exclusion upon consent withdrawal (Doc 01 §4).
"""

from datetime import datetime, timezone
import hashlib
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import ConsentEvent
from app.models.user import User
from app.schemas.consent import (
    ConsentEventOut,
    ConsentStatusResponse,
    ConsentUpdateRequest,
)


class ConsentService:
    """Manages versioned, immutable user consent state."""

    async def get_or_create_default_user(self, db: AsyncSession) -> User:
        """Retrieves or initializes the default local user session."""
        stmt = select(User).where(User.username == "default_user")
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                username="default_user",
                email="user@cryptoforget.local",
                hashed_password="mock_hashed_password_for_dev",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    async def get_current_consent(self, db: AsyncSession, user_id: int | None = None) -> ConsentStatusResponse:
        """
        Gets the current effective consent status.
        Defaults to False if no events exist (Engineering Rule #2).
        """
        if not user_id:
            user = await self.get_or_create_default_user(db)
            user_id = user.id

        # Query latest consent events ordered by effective timestamp
        stmt = select(ConsentEvent).where(ConsentEvent.user_id == user_id).order_by(desc(ConsentEvent.effective_timestamp))
        res = await db.execute(stmt)
        events = list(res.scalars().all())

        if not events:
            # Consent defaults to OFF
            return ConsentStatusResponse(
                training_consent=False,
                purpose="model_training",
                scope="conversational_ai_finetuning",
                policy_version="1.0",
                last_updated=None,
                events_count=0,
                history=[],
            )

        latest = events[0]
        is_active = latest.status == "granted"

        return ConsentStatusResponse(
            training_consent=is_active,
            purpose=latest.purpose,
            scope=latest.scope,
            policy_version=latest.policy_version,
            last_updated=latest.effective_timestamp,
            events_count=len(events),
            history=[ConsentEventOut.model_validate(e) for e in events[:10]],
        )

    async def update_consent(
        self,
        request: ConsentUpdateRequest,
        db: AsyncSession,
        user_id: int | None = None,
    ) -> ConsentStatusResponse:
        """
        Records an immutable consent grant or withdrawal event.
        """
        if not user_id:
            user = await self.get_or_create_default_user(db)
            user_id = user.id

        now = datetime.now(timezone.utc)
        status = "granted" if request.training_consent else "withdrawn"
        scope = "conversational_ai_finetuning"

        audit_hash = ConsentEvent.compute_audit_hash(
            user_id=user_id,
            status=status,
            purpose=request.purpose,
            scope=scope,
            policy_version=request.policy_version,
            timestamp_iso=now.isoformat(),
        )

        event = ConsentEvent(
            user_id=user_id,
            status=status,
            purpose=request.purpose,
            scope=scope,
            policy_version=request.policy_version,
            effective_timestamp=now,
            audit_hash=audit_hash,
        )
        db.add(event)
        await db.commit()

        return await self.get_current_consent(db, user_id=user_id)


# Global singleton
consent_service = ConsentService()
