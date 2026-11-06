"""CYRUS GUARDIAN Permission Framework.

Defines the 4-tier permission model and validates action requests
before any tool execution is attempted. Zero external dependencies.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, Optional
from backend.app.config import settings


class PermissionTier(IntEnum):
    """The four deterministic permission levels enforced by CYRUS GUARDIAN."""
    L1_READ = 1        # Read approved files, inspect status
    L2_PREPARE = 2     # Draft plans, generate diffs, format responses
    L3_EXECUTE = 3     # Write within sandbox, run unit tests, set alarms
    L4_RESTRICTED = 4  # Delete, change configs, external calls, shell scripts


@dataclass
class ActionRequest:
    """Encapsulates a proposed action requested by an agent or user."""
    actor: str
    action_type: str
    target_resource: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of GUARDIAN's security evaluation of an ActionRequest."""
    is_allowed: bool
    requires_human_approval: bool
    risk_level: PermissionTier
    reason: str


class PermissionEngine:
    """Evaluates proposed actions against sandbox boundaries and permission rules."""

    def __init__(self, sandbox_root: Optional[Path] = None):
        self.sandbox_root = (sandbox_root or Path(settings.CYRUS_SANDBOX_PATH)).resolve()

    def is_path_in_sandbox(self, target_path_str: str) -> bool:
        """Verifies if the target path resides strictly inside the authorized sandbox."""
        try:
            target = Path(target_path_str).resolve()
            return target == self.sandbox_root or self.sandbox_root in target.parents
        except Exception:
            return False

    def evaluate_action(self, request: ActionRequest) -> EvaluationResult:
        """Evaluates an action request and returns the permission decision."""
        action = request.action_type.lower()
        target = request.target_resource

        # High-Risk / Destructive Operations: Always L4 Restricted
        destructive_keywords = [
            "delete", "remove", "drop", "truncate", "kill", "format", "rmdir", "unlink",
            "reset_hard", "force_push", "clean_fd",
        ]
        if any(keyword in action for keyword in destructive_keywords):
            return EvaluationResult(
                is_allowed=False,
                requires_human_approval=True,
                risk_level=PermissionTier.L4_RESTRICTED,
                reason="Destructive action detected. Explicit user approval is mandatory.",
            )

        # File & Codebase Inspection Operations (L1 Read)
        read_keywords = ["read", "cat", "ls", "find", "inspect", "status", "diff", "log", "symbol", "tree", "doc"]
        if any(keyword in action for keyword in read_keywords):
            if self.is_path_in_sandbox(target):
                return EvaluationResult(
                    is_allowed=True,
                    requires_human_approval=False,
                    risk_level=PermissionTier.L1_READ,
                    reason="Read access within authorized sandbox approved.",
                )
            else:
                return EvaluationResult(
                    is_allowed=False,
                    requires_human_approval=True,
                    risk_level=PermissionTier.L4_RESTRICTED,
                    reason=f"Path '{target}' is outside the authorized sandbox. Explicit approval required.",
                )

        # Web Research & Public Information Gathering (L1 / L2 Read-Only)
        if action in ["web_search", "web_research", "fetch_url"]:
            return EvaluationResult(
                is_allowed=True,
                requires_human_approval=False,
                risk_level=PermissionTier.L1_READ,
                reason="Read-only public web research query permitted.",
            )

        if "write" in action or "create" in action or action in ["touch", "mkdir", "git_commit", "git_add"]:
            if self.is_path_in_sandbox(target):
                return EvaluationResult(
                    is_allowed=True,
                    requires_human_approval=False,
                    risk_level=PermissionTier.L3_EXECUTE,
                    reason="Write access within authorized sandbox allowed.",
                )
            else:
                return EvaluationResult(
                    is_allowed=False,
                    requires_human_approval=True,
                    risk_level=PermissionTier.L4_RESTRICTED,
                    reason="Write access outside sandbox is forbidden without explicit approval.",
                )

        # Planning / Drafting (Level 2)
        if "plan" in action or "draft" in action or "format" in action:
            return EvaluationResult(
                is_allowed=True,
                requires_human_approval=False,
                risk_level=PermissionTier.L2_PREPARE,
                reason="Preparation and planning actions carry no state side-effects.",
            )

        # Default fallback for unclassified actions
        return EvaluationResult(
            is_allowed=False,
            requires_human_approval=True,
            risk_level=PermissionTier.L4_RESTRICTED,
            reason=f"Unclassified action '{action}' defaults to Level 4 Restricted.",
        )


permission_engine = PermissionEngine()
