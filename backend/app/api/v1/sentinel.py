"""CYRUS SENTINEL Proactive Surveillance API Router.

Provides endpoints for:
- Daemon status and Apple Silicon sleep/shutdown boundary limitations.
- Monitored services telemetry, latency metrics, and manual ping triggers.
- Classified events stream (Level 1 Info, Level 2 Important, Level 3 Critical).
- Simulated website downtime drill verification (<30s detection).
- Telegram alert testing and dispatch.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from backend.app.sentinel.models import EventSeverity, SentinelEvent
from backend.app.sentinel.telegram_notifier import telegram_notifier
from backend.app.sentinel.watcher import sentinel_watcher

router = APIRouter(prefix="/sentinel", tags=["CYRUS SENTINEL Surveillance & Proactive Monitoring"])


# --- Request Models ---

class AddMonitorRequest(BaseModel):
    name: str = Field(..., description="Display name for monitored endpoint")
    target_url: str = Field(..., description="Target URL or endpoint (http/https)")
    interval_seconds: int = Field(default=30, ge=5, le=3600, description="Ping interval in seconds")
    expected_status_code: int = Field(default=200, description="Expected HTTP response status code")


# --- Endpoints ---

@router.get("/status")
async def get_sentinel_status() -> Dict[str, Any]:
    """Returns real-time surveillance daemon status and machine boundary limitations."""
    status = await sentinel_watcher.get_daemon_status()
    return {
        "is_running": status.is_running,
        "lifecycle_state": status.lifecycle_state,
        "active_monitors_count": status.active_monitors_count,
        "services_up_count": status.services_up_count,
        "services_down_count": status.services_down_count,
        "services_degraded_count": status.services_degraded_count,
        "last_cycle_timestamp": status.last_cycle_timestamp,
        "limitations_notice": status.limitations_notice,
    }


@router.get("/monitors")
async def list_monitors() -> Dict[str, Any]:
    """Retrieves all monitored endpoints with real-time latency and status."""
    monitors = await sentinel_watcher.get_monitors()
    return {
        "count": len(monitors),
        "monitors": [
            {
                "id": m.id,
                "name": m.name,
                "target_url": m.target_url,
                "check_type": m.check_type.value,
                "interval_seconds": m.interval_seconds,
                "expected_status_code": m.expected_status_code,
                "is_active": m.is_active,
                "current_status": m.current_status.value,
                "last_checked_at": m.last_checked_at,
                "last_latency_ms": round(m.last_latency_ms, 1) if m.last_latency_ms is not None else None,
                "consecutive_failures": m.consecutive_failures,
            }
            for m in monitors
        ],
    }


@router.post("/monitors")
async def add_monitor(request: AddMonitorRequest) -> Dict[str, Any]:
    """Registers a new endpoint to monitor."""
    try:
        mon = await sentinel_watcher.add_monitor(
            name=request.name,
            target_url=request.target_url,
            interval_seconds=request.interval_seconds,
            expected_status_code=request.expected_status_code,
        )
        return {
            "success": True,
            "monitor": {
                "id": mon.id,
                "name": mon.name,
                "target_url": mon.target_url,
                "status": mon.current_status.value,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add monitor: {e}")


@router.post("/monitors/{monitor_id}/check-now")
async def trigger_manual_check(monitor_id: str) -> Dict[str, Any]:
    """Triggers an immediate health-check ping on a specific monitor."""
    result = await sentinel_watcher.execute_monitor_check(monitor_id)
    return result


@router.get("/events")
async def list_events(
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, IMPORTANT, CRITICAL"),
) -> Dict[str, Any]:
    """Retrieves event logs and alert notifications."""
    events = await sentinel_watcher.get_events(limit=limit, severity=severity)
    return {
        "count": len(events),
        "events": [
            {
                "id": e.id,
                "monitor_id": e.monitor_id,
                "monitor_name": e.monitor_name,
                "severity": e.severity.value,
                "title": e.title,
                "message": e.message,
                "latency_ms": round(e.latency_ms, 1) if e.latency_ms is not None else None,
                "status_code": e.status_code,
                "is_resolved": e.is_resolved,
                "telegram_dispatched": e.telegram_dispatched,
                "created_at": e.created_at,
            }
            for e in events
        ],
    }


@router.post("/simulate-downtime")
async def simulate_downtime(
    monitor_id: Optional[str] = Query(None, description="Specific monitor ID or omit for default mock service")
) -> Dict[str, Any]:
    """Simulates mock website downtime, verifying SENTINEL triggers Level 3 Critical alert within 30 seconds."""
    drill_result = await sentinel_watcher.simulate_downtime(monitor_id=monitor_id)
    return drill_result


@router.post("/telegram/test")
async def test_telegram_alert() -> Dict[str, Any]:
    """Sends a test Telegram alert notification."""
    test_event = SentinelEvent(
        id="test_evt_001",
        monitor_id="mon_test",
        monitor_name="SENTINEL Notification Verification Drill",
        severity=EventSeverity.CRITICAL,
        title="Diagnostic Health Verification",
        message="This is an authorized diagnostic test alert from CYRUS SENTINEL.",
        latency_ms=12.4,
        status_code=503,
        is_resolved=False,
    )
    result = await telegram_notifier.send_alert(
        test_event, "CYRUS Health Surveillance", "http://127.0.0.1:8000/diagnostics"
    )
    return result
