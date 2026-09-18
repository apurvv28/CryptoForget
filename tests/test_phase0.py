import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import SISA_NUM_SHARDS
from src.db.database import drop_db, get_db_session, init_db
from src.db.models import AuditLogEntry, User, UserInteractionRecord
from scripts.load_existing_model_data import get_user_shard_id, load_model_data


def test_db_initialization():
    drop_db()
    init_db()
    with get_db_session() as session:
        assert session is not None


def test_user_shard_id_partitioning():
    shard_0 = get_user_shard_id("U1000", num_shards=SISA_NUM_SHARDS)
    assert 0 <= shard_0 < SISA_NUM_SHARDS
    assert get_user_shard_id("U1000", num_shards=SISA_NUM_SHARDS) == shard_0


def test_data_ingestion_and_audit_log():
    drop_db()
    load_model_data(limit_users=50)

    with get_db_session() as session:
        user_count = session.query(User).count()
        interaction_count = session.query(UserInteractionRecord).count()
        audit_blocks = session.query(AuditLogEntry).all()

        assert user_count >= 50
        assert interaction_count > 0
        assert len(audit_blocks) >= 2  # Genesis block + Ingestion block
        assert audit_blocks[0].action == "GENESIS_INIT"
        assert audit_blocks[1].action == "DATA_INGESTION"
        assert audit_blocks[1].prev_hash == audit_blocks[0].curr_hash
