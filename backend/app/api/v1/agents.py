"""CYRUS Specialist Agents REST API Endpoints.

Provides:
- Listing registered specialist agents and capabilities.
- Direct task dispatching to specific agents.
- Automatic intent-based delegation.
- Historical task log and status inspection.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.agents.agent_registry import agent_registry

router = APIRouter(prefix="/agents", tags=["Specialist Agents"])


class DispatchTaskPayload(BaseModel):
    task_description: str = Field(..., min_length=1, description="Task instruction for the specialist agent")
    session_id: Optional[str] = Field("sess_default", description="Active session ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional execution context")


class DelegatePayload(BaseModel):
    instruction: str = Field(..., min_length=1, description="User instruction to auto-route to the best specialist agent")
    session_id: Optional[str] = Field("sess_default", description="Active session ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


@router.get("")
async def list_agents():
    """Returns metadata for all registered CYRUS specialist agents."""
    agents = agent_registry.list_agents()
    return {
        "agents": agents,
        "count": len(agents),
        "status": "ALL_AGENTS_OPERATIONAL",
    }


@router.get("/tasks/history")
async def get_task_history(limit: int = 20):
    """Retrieves recent executed tasks across all specialist agents from SQLite."""
    tasks = await agent_registry.list_recent_tasks(limit=limit)
    return {
        "tasks": tasks,
        "count": len(tasks),
    }


@router.get("/{agent_name}")
async def get_agent_details(agent_name: str):
    """Retrieves detailed configuration and capabilities of a specific agent."""
    agent = agent_registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    return {
        "name": agent.name,
        "display_name": agent.display_name,
        "description": agent.metadata.description,
        "domain": agent.metadata.domain,
        "capabilities": agent.metadata.capabilities,
        "icon": agent.metadata.icon,
        "status": agent.metadata.status,
    }


@router.post("/{agent_name}/dispatch")
async def dispatch_task(agent_name: str, payload: DispatchTaskPayload):
    """Dispatches a task directly to a specific specialist agent."""
    agent = agent_registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Specialist agent '{agent_name}' not found")

    result = await agent.execute(
        task_description=payload.task_description,
        session_id=payload.session_id or "sess_default",
        context=payload.context,
    )
    return result


@router.post("/delegate")
async def auto_delegate_task(payload: DelegatePayload):
    """Auto-routes user instruction to the optimal specialist agent based on intent."""
    best_agent = agent_registry.route_intent(payload.instruction)
    if not best_agent:
        # Default to Executive Agent for high-level coordination if no specific domain matched
        best_agent = agent_registry.get_agent("CYRUS_EXECUTIVE")

    if not best_agent:
        raise HTTPException(status_code=500, detail="No suitable specialist agent available.")

    result = await best_agent.execute(
        task_description=payload.instruction,
        session_id=payload.session_id or "sess_default",
        context=payload.context,
    )
    result["delegated_by"] = "auto_router"
    return result
