"""CYRUS GUARDIAN Human-in-the-Loop Approval Workflow.

Enforces explicit human approval for all Level 4 (Restricted) operations.
Rules:
1. No blanket approvals: approvals apply strictly to one single action request ID.
2. TTL expiration: approvals expire after 10 minutes if unhandled.
3. Consequence disclosure: human must see the exact proposed action and potential consequences.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from backend.app.database import execute_query, execute_write
from backend.app.guardian.audit import log_audit_event

logger = logging.getLogger("cyrus.guardian.approval")


class ApprovalWorkflow:
    """Manages pending approval requests, expiration, and user decisions."""

    async def create_approval_request(
        self,
        actor: str,
        action_type: str,
        target_resource: str,
        consequence_summary: str,
        payload: Optional[Dict[str, Any]] = None,
        session_id: str = "default",
        ttl_minutes: int = 10,
    ) -> Dict[str, Any]:
        """Creates a pending approval request for a sensitive Level 4 operation."""
        req_id = f"appr_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(minutes=ttl_minutes)).isoformat()
        now_iso = now.isoformat()
        payload_json = json.dumps(payload or {})

        query = """
        INSERT INTO approval_requests (
            id, session_id, actor, action_type, target_resource, risk_level,
            consequence_summary, payload_json, status, created_at, expires_at
        ) VALUES (?, ?, ?, ?, ?, 4, ?, ?, 'PENDING', ?, ?);
        """
        await execute_write(
            query,
            (req_id, session_id, actor, action_type, target_resource, consequence_summary, payload_json, now_iso, expires_at),
        )

        # Log audit ledger entry
        await log_audit_event(
            actor=actor,
            action=action_type,
            target_resource=target_resource,
            risk_level=4,
            decision="AWAITING_APPROVAL",
            details={
                "approval_request_id": req_id,
                "consequence_summary": consequence_summary,
                "expires_at": expires_at,
            },
        )

        logger.warning(
            "GUARDIAN Level 4 Action Blocked. Awaiting Approval: %s -> %s on %s (ID: %s)",
            actor, action_type, target_resource, req_id
        )

        return {
            "approval_id": req_id,
            "status": "PENDING",
            "actor": actor,
            "action_type": action_type,
            "target_resource": target_resource,
            "consequence_summary": consequence_summary,
            "expires_at": expires_at,
        }

    async def list_pending_approvals(self) -> List[Dict[str, Any]]:
        """Returns all currently active pending approval requests, expiring any overdue."""
        now_iso = datetime.now(timezone.utc).isoformat()
        # 1. Invalidate expired requests
        expire_query = """
        UPDATE approval_requests
        SET status = 'EXPIRED'
        WHERE status = 'PENDING' AND expires_at < ?;
        """
        await execute_write(expire_query, (now_iso,))

        # 2. Query valid pending requests
        query = """
        SELECT id, session_id, actor, action_type, target_resource, risk_level,
               consequence_summary, payload_json, status, created_at, expires_at
        FROM approval_requests
        WHERE status = 'PENDING'
        ORDER BY created_at DESC;
        """
        rows = await execute_query(query)
        for r in rows:
            try:
                r["payload"] = json.loads(r.get("payload_json", "{}"))
            except Exception:
                r["payload"] = {}
        return rows

    async def resolve_request(
        self,
        request_id: str,
        approved: bool,
        resolved_by: str = "Saksham",
        notes: str = "",
    ) -> Dict[str, Any]:
        """Processes the human decision (Approve or Reject) for an action request."""
        now_iso = datetime.now(timezone.utc).isoformat()

        # Check existing request
        rows = await execute_query("SELECT * FROM approval_requests WHERE id = ?", (request_id,))
        if not rows:
            return {"success": False, "error": f"Approval request '{request_id}' not found."}

        req = rows[0]
        if req["status"] != "PENDING":
            return {
                "success": False,
                "error": f"Request cannot be modified; current status is '{req['status']}'.",
            }

        # Check expiration
        if req["expires_at"] < now_iso:
            await execute_write("UPDATE approval_requests SET status = 'EXPIRED' WHERE id = ?", (request_id,))
            return {"success": False, "error": "This approval request has expired (10 minute TTL exceeded)."}

        new_status = "APPROVED" if approved else "REJECTED"
        update_query = """
        UPDATE approval_requests
        SET status = ?, resolved_at = ?, resolved_by = ?
        WHERE id = ?;
        """
        await execute_write(update_query, (new_status, now_iso, resolved_by, request_id))

        # Record decision in immutable audit log
        await log_audit_event(
            actor="GUARDIAN_SECURITY",
            action=f"APPROVAL_{new_status}",
            target_resource=req["target_resource"],
            risk_level=4,
            decision="APPROVED_BY_USER" if approved else "DENIED",
            details={
                "approval_id": request_id,
                "resolved_by": resolved_by,
                "action_type": req["action_type"],
                "notes": notes,
            },
        )

        logger.info("Approval request %s resolved by %s: %s", request_id, resolved_by, new_status)
        return {
            "success": True,
            "approval_id": request_id,
            "status": new_status,
            "resolved_by": resolved_by,
            "resolved_at": now_iso,
        }


# Global singleton instance
approval_workflow = ApprovalWorkflow()
