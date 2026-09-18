from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.agents.user_simulator import get_agent_manager
from src.db.database import get_db

router = APIRouter(prefix="/api/v1/users", tags=["User Agents"])


class OnboardUserRequest(BaseModel):
    user_id: str = Field(..., description="Unique User ID (e.g. U1020)")
    name: Optional[str] = Field(None, description="Full Name")
    email: Optional[str] = Field(None, description="Email Address")


@router.get("", response_model=List[Dict[str, Any]])
def list_user_agents():
    """Returns the list of 15-20 virtual simulated user agents in the population."""
    mgr = get_agent_manager()
    return mgr.list_agents()


@router.get("/{user_id}", response_model=Dict[str, Any])
def get_user_agent(user_id: str):
    """Retrieves profile details for a single virtual user agent."""
    mgr = get_agent_manager()
    agent = mgr.get_agent(user_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"User agent {user_id} not found.")
    return agent.to_dict()


@router.post("/onboard", response_model=Dict[str, Any])
def onboard_user_agent(req: OnboardUserRequest):
    """Onboards a new simulated user agent into the virtual population."""
    mgr = get_agent_manager()
    agent = mgr.add_agent(user_id=req.user_id, name=req.name, email=req.email)
    return agent.to_dict()


@router.post("/reset-all-deletions", response_model=Dict[str, Any])
def reset_all_user_deletions(db: Session = Depends(get_db)):
    """Undoes all deletion requests, restores data consent for all users, and enables full model personalization."""
    from src.crypto.audit_log import AuditLedger
    from src.db.models import DeletionCertificate, DeletionRequest, User

    # 1. Update Database User consent status
    db.query(User).update({User.consent_status: True})

    # 2. Clear deletion requests and certificates
    db.query(DeletionCertificate).delete()
    db.query(DeletionRequest).delete()

    # 3. Log audit event
    ledger = AuditLedger(db)
    ledger.append_block("SYSTEM_CONSENT_RESTORED_ALL", "Restored model consent and undid all deletion requests across all user agents.")

    db.commit()

    # 4. Reset in-memory virtual agents
    mgr = get_agent_manager()
    mgr.reset_all_agents()

    return {
        "status": "SUCCESS",
        "message": "Successfully restored consent for all users and undid all deletion requests.",
        "active_users_count": len(mgr.list_agents()),
    }
