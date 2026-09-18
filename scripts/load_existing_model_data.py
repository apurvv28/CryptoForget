"""
Loader script for Phase 0: System Foundations & Model Integration.

Maps existing MIND user histories (`models/user_histories.joblib`) and content model metadata
into the CryptoForget database, assigns SISA shard IDs (S=5), and initializes the Genesis audit log block.
"""

import hashlib
import sys
from pathlib import Path
from typing import Dict, List

import joblib

# Make src importable regardless of CWD
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import MODELS_DIR, SISA_NUM_SHARDS
from src.crypto.audit_log import AuditLedger
from src.db.database import get_db_session, init_db
from src.db.models import AuditLogEntry, User, UserInteractionRecord


def get_user_shard_id(user_id: str, num_shards: int = SISA_NUM_SHARDS) -> int:
    """Deterministically maps a user_id to a SISA shard ID (0 to num_shards-1)."""
    hash_digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    return int(hash_digest, 16) % num_shards


def compute_interaction_leaf_hash(user_id: str, news_ids: List[str]) -> str:
    """Computes a SHA-256 leaf hash for a user's interaction profile."""
    content = f"{user_id}:{' '.join(news_ids)}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_model_data(limit_users: int = 1000) -> None:
    """Loads MIND user histories into SQLite database and initializes Genesis audit block.
    By default loads up to `limit_users` to keep DB lightweight while representing full population."""
    init_db()
    user_histories_path = MODELS_DIR / "user_histories.joblib"
    content_model_path = MODELS_DIR / "content_model.joblib"

    if not user_histories_path.exists() or not content_model_path.exists():
        raise FileNotFoundError(
            f"Model artifacts not found in {MODELS_DIR}. Ensure content_model.joblib and user_histories.joblib exist."
        )

    print(f"Loading user histories from {user_histories_path} ...")
    user_histories: Dict[str, List[str]] = joblib.load(user_histories_path)
    total_known_users = len(user_histories)
    print(f"  Total users in joblib: {total_known_users}")

    with get_db_session() as session:
        ledger = AuditLedger(session)

        # Check if already initialized
        existing_user_count = session.query(User).count()
        if existing_user_count > 0:
            print(f"Database already contains {existing_user_count} users. Skipping ingestion.")
            return

        # 1. Initialize Genesis block in audit log if empty
        if session.query(AuditLogEntry).count() == 0:
            ledger.append_block("GENESIS_INIT", "Genesis Block - CryptoForget System Initialization")
            print("Genesis audit log block created.")

        # 2. Ingest user records and interaction histories
        users_to_process = list(user_histories.items())[:limit_users]
        print(f"Ingesting {len(users_to_process)} user profiles into database...")

        user_objects = []
        interaction_objects = []

        for user_id, history in users_to_process:
            shard_id = get_user_shard_id(user_id)
            user_obj = User(user_id=user_id, consent_status=True, shard_id=shard_id)
            user_objects.append(user_obj)

            leaf_hash = compute_interaction_leaf_hash(user_id, history)
            for news_id in history:
                interaction_objects.append(
                    UserInteractionRecord(
                        user_id=user_id,
                        news_id=news_id,
                        shard_id=shard_id,
                        leaf_hash=leaf_hash,
                    )
                )

        session.bulk_save_objects(user_objects)
        session.bulk_save_objects(interaction_objects)
        session.commit()

        # Record ingestion audit entry
        ledger.append_block("DATA_INGESTION", f"Ingested {len(users_to_process)} MIND users across {SISA_NUM_SHARDS} SISA shards")
        print(f"Successfully ingested {len(user_objects)} users and {len(interaction_objects)} interactions into database!")


if __name__ == "__main__":
    load_model_data()
