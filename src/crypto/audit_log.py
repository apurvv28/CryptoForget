import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.db.models import AuditLogEntry


def format_timestamp(ts: Optional[datetime]) -> str:
    """Formats datetime deterministically to ISO 8601 UTC string."""
    if ts is None:
        return ""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_block_hash(prev_hash: str, action: str, payload_hash: str, timestamp_str: str) -> str:
    """Computes deterministic current block hash from prev_hash, action, payload_hash, and timestamp."""
    block_contents = f"{prev_hash}:{action}:{payload_hash}:{timestamp_str}"
    return hashlib.sha256(block_contents.encode("utf-8")).hexdigest()


class AuditLedger:
    """Hash-chained append-only audit ledger manager."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def append_block(self, action: str, payload: str, metrics: Optional[Dict[str, Any]] = None) -> AuditLogEntry:
        """Appends a new block to the audit ledger chained to the previous block's hash."""
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        # Get latest block hash (or default to Genesis zero hash)
        last_block = (
            self.session.query(AuditLogEntry)
            .order_by(AuditLogEntry.block_id.desc())
            .first()
        )
        prev_hash = last_block.curr_hash if last_block else "0" * 64

        now = datetime.now(timezone.utc)
        now_str = format_timestamp(now)

        curr_hash = compute_block_hash(prev_hash, action, payload_hash, now_str)

        block = AuditLogEntry(
            timestamp=now,
            action=action,
            payload_hash=payload_hash,
            metrics_json=json.dumps(metrics) if metrics else None,
            prev_hash=prev_hash,
            curr_hash=curr_hash,
        )

        self.session.add(block)
        self.session.commit()
        self.session.refresh(block)
        return block

    def verify_ledger_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verifies the complete hash chain integrity of all blocks in the database.
        Returns (True, None) if intact, or (False, error_msg) if tampering is detected.
        """
        blocks = (
            self.session.query(AuditLogEntry)
            .order_by(AuditLogEntry.block_id.asc())
            .all()
        )

        if not blocks:
            return True, None

        expected_prev_hash = "0" * 64

        for block in blocks:
            if block.prev_hash != expected_prev_hash:
                return False, f"Hash chain broken at block {block.block_id}: expected prev_hash {expected_prev_hash}, got {block.prev_hash}"

            timestamp_str = format_timestamp(block.timestamp)
            recomputed_hash = compute_block_hash(
                block.prev_hash, block.action, block.payload_hash, timestamp_str
            )

            if block.curr_hash != recomputed_hash:
                return False, f"Block {block.block_id} hash mismatch: stored {block.curr_hash}, recomputed {recomputed_hash}"

            expected_prev_hash = block.curr_hash

        return True, None

    def get_all_blocks(self) -> List[Dict[str, Any]]:
        blocks = (
            self.session.query(AuditLogEntry)
            .order_by(AuditLogEntry.block_id.asc())
            .all()
        )
        return [b.to_dict() for b in blocks]
