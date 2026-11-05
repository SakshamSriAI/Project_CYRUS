"""CYRUS GUARDIAN Audit Logging Subsystem.

Provides an immutable, append-only security ledger in SQLite.
Every security decision, tool execution, and approval event is permanently recorded.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import uuid
from backend.app.database import execute_query, execute_write


async def log_audit_event(
    actor: str,
    action: str,
    target_resource: str,
    risk_level: int,
    decision: str,
    details: Optional[Dict[str, Any]] = None,
) -> str:
    """Records an audit event into the append-only SQLite audit_logs table."""
    event_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    details_json = json.dumps(details or {})

    query = """
    INSERT INTO audit_logs (id, timestamp, actor, action, target_resource, risk_level, decision, details_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    await execute_write(
        query,
        (event_id, timestamp, actor, action, target_resource, risk_level, decision, details_json),
    )
    return event_id


async def get_audit_logs(limit: int = 50, actor: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves recent audit log entries for review in the Security Center."""
    if actor:
        query = """
        SELECT id, timestamp, actor, action, target_resource, risk_level, decision, details_json
        FROM audit_logs
        WHERE actor = ?
        ORDER BY timestamp DESC
        LIMIT ?;
        """
        rows = await execute_query(query, (actor, limit))
    else:
        query = """
        SELECT id, timestamp, actor, action, target_resource, risk_level, decision, details_json
        FROM audit_logs
        ORDER BY timestamp DESC
        LIMIT ?;
        """
        rows = await execute_query(query, (limit,))

    for r in rows:
        try:
            r["details"] = json.loads(r.get("details_json", "{}"))
        except Exception:
            r["details"] = {}
    return rows
