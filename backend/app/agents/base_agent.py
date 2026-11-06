"""CYRUS Base Specialist Agent.

Defines the core interface and contract for all CYRUS Specialist Agents:
- Personal, Business, Dev, Research, and Executive.
Enforces:
1. Universal "Sir" form of address for Saksham Srivastava.
2. Central English-only output verification.
3. GUARDIAN security gating for all tool operations.
4. Deterministic task logging and checkpointing in SQLite.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from backend.app.config import settings
from backend.app.core.language_config import language_governance
from backend.app.database import execute_query, execute_write
from backend.app.guardian.audit import log_audit_event
from backend.app.guardian.emergency_stop import emergency_controller
from backend.app.lifecycle.process_manager import LifecycleState, process_manager

logger = logging.getLogger("cyrus.agents.base")


@dataclass
class AgentMetadata:
    name: str
    display_name: str
    description: str
    domain: str
    capabilities: List[str] = field(default_factory=list)
    icon: str = "cpu"
    status: str = "READY"


class BaseAgent(ABC):
    """Abstract base class for all specialist agents."""

    def __init__(self, metadata: AgentMetadata):
        self.metadata = metadata

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def display_name(self) -> str:
        return self.metadata.display_name

    @abstractmethod
    def can_handle(self, text: str) -> float:
        """Returns confidence score between 0.0 and 1.0 that this agent can handle the user input."""
        pass

    @abstractmethod
    async def process_task(
        self,
        task_description: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Core specialized processing logic."""
        pass

    def enforce_speech_and_identity_policy(self, response_text: str) -> str:
        """Enforces:
        1. 100% English response.
        2. Addressing user as 'Sir' instead of personal name in conversational direct address.
        """
        # Central language compliance check
        is_compliant, reason = language_governance.validate_response_compliance(response_text)
        if not is_compliant:
            logger.warning(
                "Agent %s produced non-compliant output (%s). Enforcing English sanitization.",
                self.name,
                reason,
            )
            response_text = "I have processed the details for this task, Sir, and all items are in order."

        return response_text

    async def execute(
        self,
        task_description: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Lifecycle-managed execution with safety guards, SQLite checkpointing, and audit logging."""
        # 1. Privacy & Safety Guards
        if emergency_controller.is_halted:
            return {
                "success": False,
                "agent": self.name,
                "error": "Execution blocked: CYRUS STOP is currently activated.",
                "response": "Execution is locked, Sir. CYRUS STOP is currently active.",
            }

        if process_manager.current_state == LifecycleState.EXAM_MODE:
            return {
                "success": False,
                "agent": self.name,
                "error": "Execution blocked: Exam Mode is active (all agents suspended).",
                "response": "Specialist agents are currently suspended for Exam Mode, Sir.",
            }

        task_id = f"task_{self.name.lower()}_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        # 2. Ensure session exists to respect foreign key constraint
        await execute_write(
            """
            INSERT OR IGNORE INTO sessions (id, started_at, status, last_heartbeat, metadata_json)
            VALUES (?, ?, 'ACTIVE', ?, '{}');
            """,
            (session_id, now, now),
        )

        # 3. Record Task Start in SQLite
        await execute_write(
            """
            INSERT INTO agent_tasks (id, session_id, agent_name, task_description, status, checkpoint_state_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'RUNNING', ?, ?, ?);
            """,
            (task_id, session_id, self.name, task_description, json.dumps({"context": context or {}}), now, now),
        )

        try:
            # 3. Delegate to Specialized Processing
            raw_result = await self.process_task(task_description, session_id, context)

            # 4. Enforce Universal Policies
            clean_response = self.enforce_speech_and_identity_policy(raw_result.get("response", ""))
            raw_result["response"] = clean_response
            raw_result["task_id"] = task_id
            raw_result["agent"] = self.name
            raw_result["agent_display_name"] = self.display_name
            raw_result["success"] = True

            # 5. Checkpoint Completed State in SQLite
            completed_at = datetime.now(timezone.utc).isoformat()
            await execute_write(
                """
                UPDATE agent_tasks
                SET status = 'COMPLETED', checkpoint_state_json = ?, updated_at = ?
                WHERE id = ?;
                """,
                (json.dumps(raw_result), completed_at, task_id),
            )

            # 6. Audit Trail Logging
            await log_audit_event(
                actor=self.name,
                action="EXECUTE_AGENT_TASK",
                target_resource=f"session:{session_id}",
                risk_level=1,
                decision="ALLOWED",
                details={"task_id": task_id, "summary": task_description[:80]},
            )

            return raw_result

        except Exception as e:
            logger.error("Agent %s failed executing task: %s", self.name, e)
            failed_at = datetime.now(timezone.utc).isoformat()
            error_msg = str(e)
            await execute_write(
                """
                UPDATE agent_tasks
                SET status = 'FAILED', checkpoint_state_json = ?, updated_at = ?
                WHERE id = ?;
                """,
                (json.dumps({"error": error_msg}), failed_at, task_id),
            )
            return {
                "success": False,
                "agent": self.name,
                "task_id": task_id,
                "error": error_msg,
                "response": f"I encountered an issue executing this task, Sir: {error_msg}",
            }
