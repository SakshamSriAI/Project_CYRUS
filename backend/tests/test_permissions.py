"""Tests for CYRUS GUARDIAN Permission Framework."""

from pathlib import Path
from backend.app.config import settings
from backend.app.guardian.permissions import (
    ActionRequest,
    PermissionEngine,
    PermissionTier,
)


def test_permission_read_within_sandbox():
    engine = PermissionEngine()
    sandbox_file = Path(settings.CYRUS_SANDBOX_PATH) / "README.md"
    req = ActionRequest(
        actor="CORE",
        action_type="read_file",
        target_resource=str(sandbox_file),
    )
    result = engine.evaluate_action(req)
    assert result.is_allowed is True
    assert result.requires_human_approval is False
    assert result.risk_level == PermissionTier.L1_READ


def test_permission_read_outside_sandbox_restricted():
    engine = PermissionEngine()
    external_file = "/etc/passwd"
    req = ActionRequest(
        actor="CORE",
        action_type="read_file",
        target_resource=external_file,
    )
    result = engine.evaluate_action(req)
    assert result.is_allowed is False
    assert result.requires_human_approval is True
    assert result.risk_level == PermissionTier.L4_RESTRICTED


def test_permission_destructive_action_restricted():
    engine = PermissionEngine()
    req = ActionRequest(
        actor="AGENT_DEV",
        action_type="delete_file",
        target_resource=str(Path(settings.CYRUS_SANDBOX_PATH) / "test.txt"),
    )
    result = engine.evaluate_action(req)
    assert result.is_allowed is False
    assert result.requires_human_approval is True
    assert result.risk_level == PermissionTier.L4_RESTRICTED
