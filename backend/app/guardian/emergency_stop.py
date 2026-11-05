"""CYRUS GUARDIAN Emergency Stop (CYRUS STOP) Protocol.

Application-level emergency halt mechanism:
1. Immediately rejects any new agent tasks, chat completions, or tool execution.
2. Terminates all active child processes registered in process_registry.
3. Revokes all active temporary session tokens.
4. Preserves audit logs and marks system HALTED.
5. Operates purely via application backend code (independent of LLM behavior).
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict
from backend.app.guardian.audit import log_audit_event
from backend.app.guardian.auth import guardian_auth
from backend.app.lifecycle.process_manager import LifecycleState, process_manager

logger = logging.getLogger("cyrus.guardian.emergency")


class EmergencyHaltController:
    """Manages the CYRUS STOP kill switch."""

    def __init__(self):
        self._halted: bool = False
        self._halt_reason: str = ""
        self._halted_at: str = ""

    @property
    def is_halted(self) -> bool:
        return self._halted

    async def trigger_emergency_stop(
        self,
        reason: str = "Manual emergency halt triggered by user",
        triggered_by: str = "Saksham",
    ) -> Dict[str, Any]:
        """Executes the CYRUS STOP kill switch."""
        self._halted = True
        self._halt_reason = reason
        self._halted_at = datetime.now(timezone.utc).isoformat()

        logger.critical("EMERGENCY STOP ACTIVATED by %s: %s", triggered_by, reason)

        # 1. Invalidate all active session tokens
        guardian_auth.revoke_all_tokens()

        # 2. Terminate all active CYRUS-owned child processes
        term_summary = await process_manager.terminate_cyrus_processes(grace_period_sec=1)

        # 3. Transition process manager to SHUTDOWN
        process_manager.set_state(LifecycleState.SHUTDOWN)

        # 4. Record critical audit ledger entry
        await log_audit_event(
            actor="CYRUS_GUARDIAN",
            action="EMERGENCY_STOP_HALT",
            target_resource="system:all",
            risk_level=4,
            decision="HALTED",
            details={
                "triggered_by": triggered_by,
                "reason": reason,
                "halted_at": self._halted_at,
                "processes_terminated": term_summary,
            },
        )

        return {
            "status": "EMERGENCY_HALTED",
            "message": "CYRUS STOP activated. All task queues, tokens, and child processes terminated.",
            "halted_at": self._halted_at,
            "reason": reason,
            "processes_terminated": term_summary,
        }

    async def reset_emergency_stop(self, reset_by: str = "Saksham") -> Dict[str, Any]:
        """Resets the emergency halt state after verified resolution."""
        if not self._halted:
            return {"status": "ACTIVE", "message": "System is not halted."}

        self._halted = False
        self._halt_reason = ""
        self._halted_at = ""

        process_manager.set_state(LifecycleState.ACTIVE)

        now = datetime.now(timezone.utc).isoformat()
        await log_audit_event(
            actor="CYRUS_GUARDIAN",
            action="EMERGENCY_STOP_RESET",
            target_resource="system:all",
            risk_level=4,
            decision="ALLOWED",
            details={"reset_by": reset_by, "reset_at": now},
        )

        logger.info("Emergency halt reset by %s. System returned to ACTIVE state.", reset_by)
        return {
            "status": "ACTIVE",
            "message": f"Emergency halt cleared by {reset_by}. System restored to operational state.",
            "restored_at": now,
        }


# Global singleton instance
emergency_controller = EmergencyHaltController()
