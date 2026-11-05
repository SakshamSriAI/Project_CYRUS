"""CYRUS GUARDIAN Security & Authorization API Endpoints."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.config import settings
from backend.app.guardian.approval import approval_workflow
from backend.app.guardian.audit import get_audit_logs
from backend.app.guardian.emergency_stop import emergency_controller
from backend.app.guardian.permissions import (
    ActionRequest,
    PermissionTier,
    permission_engine,
)

router = APIRouter(prefix="/guardian", tags=["Security & Guardian"])


class ResolveApprovalRequest(BaseModel):
    notes: Optional[str] = Field("", description="Optional notes or rationale for the decision")


class EvaluateActionPayload(BaseModel):
    actor: str = Field(..., description="Agent or caller identifier")
    action_type: str = Field(..., description="Action name e.g. read_file, delete_file")
    target_resource: str = Field(..., description="Resource target path or identifier")
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict)
    session_id: Optional[str] = Field("default", description="Active session ID")


@router.get("/status")
async def get_guardian_status():
    """Returns security status, sandbox boundary, and emergency halt state."""
    pending = await approval_workflow.list_pending_approvals()
    return {
        "status": "HALTED" if emergency_controller.is_halted else "ACTIVE",
        "emergency_halted": emergency_controller.is_halted,
        "sandbox_root": settings.CYRUS_SANDBOX_PATH,
        "permission_tiers": {
            "L1": "READ (Automatic in sandbox)",
            "L2": "PREPARE (Automatic, no side-effects)",
            "L3": "EXECUTE (Policy-gated in sandbox)",
            "L4": "RESTRICTED (Explicit human approval mandatory)",
        },
        "pending_approvals_count": len(pending),
    }


@router.get("/approvals/pending")
async def list_pending_approvals():
    """Lists all active pending Level 4 approval requests awaiting human authorization."""
    requests = await approval_workflow.list_pending_approvals()
    return {"pending_count": len(requests), "requests": requests}


@router.post("/approvals/{request_id}/approve")
async def approve_request(request_id: str, body: ResolveApprovalRequest):
    """Explicitly authorizes a pending Level 4 operation."""
    result = await approval_workflow.resolve_request(
        request_id=request_id,
        approved=True,
        resolved_by="Saksham",
        notes=body.notes or "",
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/approvals/{request_id}/reject")
async def reject_request(request_id: str, body: ResolveApprovalRequest):
    """Explicitly denies a pending Level 4 operation."""
    result = await approval_workflow.resolve_request(
        request_id=request_id,
        approved=False,
        resolved_by="Saksham",
        notes=body.notes or "",
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/evaluate-action")
async def evaluate_action(payload: EvaluateActionPayload):
    """Evaluates an action request and creates an approval request if Level 4."""
    req = ActionRequest(
        actor=payload.actor,
        action_type=payload.action_type,
        target_resource=payload.target_resource,
        payload=payload.payload or {},
    )
    eval_result = permission_engine.evaluate_action(req)

    response_data = {
        "is_allowed": eval_result.is_allowed,
        "risk_level": eval_result.risk_level.value,
        "requires_human_approval": eval_result.requires_human_approval,
        "reason": eval_result.reason,
    }

    # If action requires approval, create an approval request record in SQLite
    if eval_result.requires_human_approval:
        appr = await approval_workflow.create_approval_request(
            actor=payload.actor,
            action_type=payload.action_type,
            target_resource=payload.target_resource,
            consequence_summary=eval_result.reason,
            payload=payload.payload,
            session_id=payload.session_id or "default",
        )
        response_data["approval_request"] = appr

    return response_data


@router.get("/audit/logs")
async def list_audit_logs(limit: int = 50, actor: Optional[str] = None):
    """Returns append-only audit trail logs for security monitoring."""
    logs = await get_audit_logs(limit=limit, actor=actor)
    return {"total_returned": len(logs), "logs": logs}


@router.post("/emergency-stop")
async def trigger_emergency_stop():
    """Activates CYRUS STOP kill switch immediately."""
    result = await emergency_controller.trigger_emergency_stop(
        reason="Triggered via Security API by user",
        triggered_by="Saksham",
    )
    return result


@router.post("/reset-stop")
async def reset_emergency_stop():
    """Resets the emergency halt state after verified resolution."""
    result = await emergency_controller.reset_emergency_stop(reset_by="Saksham")
    return result
