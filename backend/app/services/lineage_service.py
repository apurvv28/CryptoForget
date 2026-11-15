"""
Data Lineage and Inventory Service.

Maintains restricted lineage graph per Doc 05 §5:
  subject pseudonym -> record IDs -> dataset version -> shard -> slice -> model version

Enforces:
1. No non-consented record enters training manifests (Engineering Rule #1).
2. Pseudonymous subject and record IDs (Doc 05 §10).
3. Data Inventory summary (Doc 02 FR-04).
"""

from datetime import datetime, timezone
import hashlib
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import ConsentEvent
from app.models.conversation import Message
from app.models.training_record import TrainingRecord
from app.models.user import User
from app.schemas.consent import DataCategoryInventory, DataInventoryResponse
from app.services.consent_service import consent_service

PSEUDONYM_SALT = "cryptoforget-pseudonym-salt-2026"


class LineageService:
    """Manages record pseudonymization and training eligibility lineage."""

    def generate_pseudonymous_subject_id(self, user_id: int) -> str:
        """Computes a one-way pseudonymous subject ID."""
        digest = hashlib.sha256(f"{PSEUDONYM_SALT}:subject:{user_id}".encode()).hexdigest()
        return f"subj_{digest[:16]}"

    def generate_record_id(self, message_id: int) -> str:
        """Computes an opaque record ID."""
        digest = hashlib.sha256(f"{PSEUDONYM_SALT}:record:{message_id}:{uuid.uuid4()}".encode()).hexdigest()
        return f"rec_{digest[:16]}"

    async def register_message_lineage(
        self,
        message: Message,
        user_id: int,
        db: AsyncSession,
    ) -> TrainingRecord:
        """
        Creates a training lineage record for a conversation message.
        Checks current active consent. Only marks eligible if consent is currently GRANTED.
        """
        consent_status = await consent_service.get_current_consent(db, user_id=user_id)
        latest_event_id = consent_status.history[0].id if consent_status.history else None

        text_digest = hashlib.sha256(message.content.encode("utf-8")).hexdigest()
        pseudonymous_subject = self.generate_pseudonymous_subject_id(user_id)
        record_id = self.generate_record_id(message.id)

        training_record = TrainingRecord(
            record_id=record_id,
            pseudonymous_subject_id=pseudonymous_subject,
            message_id=message.id,
            text_digest=text_digest,
            is_eligible_for_training=consent_status.training_consent,
            consent_event_id=latest_event_id if consent_status.training_consent else None,
            dataset_version="v1.0" if consent_status.training_consent else None,
            shard_id=None,
            slice_id=None,
            is_tombstoned=False,
        )
        db.add(training_record)
        await db.commit()
        await db.refresh(training_record)
        return training_record

    async def get_data_inventory(self, db: AsyncSession, user_id: int | None = None) -> DataInventoryResponse:
        """
        Produces data inventory summary per Doc 02 FR-04.
        """
        if not user_id:
            user = await consent_service.get_or_create_default_user(db)
            user_id = user.id

        # Count total messages
        msg_stmt = select(func.count(Message.id))
        total_msgs = (await db.execute(msg_stmt)).scalar() or 0

        # Count training eligible records
        elig_stmt = select(func.count(TrainingRecord.id)).where(
            TrainingRecord.is_eligible_for_training == True,
            TrainingRecord.is_tombstoned == False,
        )
        eligible_count = (await db.execute(elig_stmt)).scalar() or 0

        # Count records actually partitioned into model shards
        used_stmt = select(func.count(TrainingRecord.id)).where(
            TrainingRecord.shard_id.isnot(None),
            TrainingRecord.is_tombstoned == False,
        )
        used_count = (await db.execute(used_stmt)).scalar() or 0

        consent = await consent_service.get_current_consent(db, user_id=user_id)

        categories = [
            DataCategoryInventory(
                category="Account Identity",
                purpose="Authentication & session security",
                storage_location="SQLite (data/cryptoforget.db)",
                retention_period="Until account deletion",
                training_eligible=False,
                count=1,
            ),
            DataCategoryInventory(
                category="Chat Conversation History",
                purpose="Service display & chat context",
                storage_location="SQLite (conversations, messages)",
                retention_period="User-managed / standard retention",
                training_eligible=consent.training_consent,
                count=total_msgs,
            ),
            DataCategoryInventory(
                category="Consent Audit Events",
                purpose="Privacy preference verification",
                storage_location="SQLite (consent_events)",
                retention_period="Permanent audit trail",
                training_eligible=False,
                count=consent.events_count,
            ),
            DataCategoryInventory(
                category="SISA Training Records",
                purpose="Model fine-tuning & unlearning lineage",
                storage_location="SQLite (training_records) & AWS S3",
                retention_period="Until consent withdrawal or deletion request",
                training_eligible=consent.training_consent,
                count=eligible_count,
            ),
        ]

        return DataInventoryResponse(
            total_messages_stored=total_msgs,
            training_eligible_messages=eligible_count,
            messages_used_in_model=used_count,
            training_consent_active=consent.training_consent,
            categories=categories,
            policy_version=consent.policy_version,
        )


# Global singleton
lineage_service = LineageService()
