from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.agents.user_simulator import get_agent_manager

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
