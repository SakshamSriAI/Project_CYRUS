"""CYRUS SENTINEL Specialist Agent.

Manages:
- Proactive background health-checks (local services, websites, gateways).
- Incident triage & event severity classification (Level 1 Info, Level 2 Important, Level 3 Critical).
- Proactive Telegram alerting for Level 3 Critical outages.
- Transparent reporting on local Apple Silicon M5 sleep/shutdown monitoring limitations.
Always addresses the user as "Sir".
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import AgentMetadata, BaseAgent
from backend.app.sentinel.watcher import sentinel_watcher

logger = logging.getLogger("cyrus.agents.sentinel")


class SentinelAgent(BaseAgent):
    """Specialist agent for system health surveillance, anomaly detection, and alerting."""

    def __init__(self):
        super().__init__(
            AgentMetadata(
                name="CYRUS_SENTINEL",
                display_name="CYRUS Sentinel",
                description="Specialist in proactive health monitoring, website availability pings, event severity classification, and Telegram incident alerts.",
                domain="System Health & Infrastructure Surveillance",
                capabilities=[
                    "Proactive Background Endpoint Monitoring",
                    "Event Severity Classification (L1 Info, L2 Important, L3 Critical)",
                    "Telegram Incident Notification Dispatch",
                    "Simulated Downtime Verification Drills",
                    "Local Machine Sleep/Shutdown Boundary Awareness",
                ],
                icon="shield",
            )
        )

    def can_handle(self, text: str) -> float:
        clean = text.lower()
        keywords = [
            "sentinel", "monitor", "ping", "uptime", "downtime",
            "health check", "telegram", "alert", "outage", "latency",
            "status check", "incident", "watcher",
        ]
        matches = sum(1 for kw in keywords if kw in clean)
        if matches >= 2:
            return 0.95
        if matches == 1:
            return 0.80
        return 0.05

    async def process_task(
        self,
        task_description: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Evaluates health telemetry, simulates outages, and reports surveillance status."""
        clean = task_description.lower()

        # 1. Simulate Downtime Drill
        if any(w in clean for w in ["simulate", "drill", "mock downtime", "test outage"]):
            drill_result = await sentinel_watcher.simulate_downtime()
            return {
                "response": drill_result["summary"],
                "action_type": "DOWNTIME_DRILL_SIMULATION",
                "status": "DRILL_COMPLETED",
                "within_threshold": drill_result["within_30s_threshold"],
                "elapsed_seconds": drill_result["elapsed_seconds"],
                "confidence_score": 1.0,
            }

        # 2. Limitations / Sleep Query
        if any(w in clean for w in ["sleep", "limitation", "lid", "battery", "offline"]):
            response = (
                f"Here are the operating boundaries for local surveillance, Sir:\n\n"
                f"• **Hardware Platform**: Apple Silicon MacBook Air M5 (Local execution).\n"
                f"• **Sleep Boundary**: When the MacBook enters system sleep or the display lid is closed, background pings are automatically suspended to preserve battery and respect hardware state.\n"
                f"• **Shutdown Boundary**: Proactive monitoring resumes automatically upon system wake or reboot.\n"
                f"• **Continuous Cloud Alerting**: If 24/7 un-interrupted surveillance is required when your laptop is closed, an optional cloud sidecar evaluator can be explored in Phase 12, Sir."
            )
            return {
                "response": response,
                "action_type": "LIMITATIONS_ADVISORY",
                "confidence_score": 1.0,
            }

        # 3. Status Overview / Telemetry
        daemon_status = await sentinel_watcher.get_daemon_status()
        monitors = await sentinel_watcher.get_monitors()

        mon_items = [
            f"• **{m.name}**: Status `{m.current_status.value}` (Latency: {m.last_latency_ms:.1f}ms, Interval: {m.interval_seconds}s)"
            if m.last_latency_ms is not None else
            f"• **{m.name}**: Status `{m.current_status.value}` (Interval: {m.interval_seconds}s)"
            for m in monitors
        ]

        response = (
            f"CYRUS SENTINEL surveillance status, Sir:\n\n"
            f"• **Daemon Status**: {'ACTIVE & WATCHING' if daemon_status.is_running else 'SUSPENDED'}\n"
            f"• **Services Monitored**: {daemon_status.active_monitors_count} endpoints ({daemon_status.services_up_count} UP, {daemon_status.services_down_count} DOWN, {daemon_status.services_degraded_count} DEGRADED)\n"
            f"• **Monitored Targets**:\n" + "\n".join(mon_items) + "\n\n"
            f"All health events are categorized from Level 1 Info to Level 3 Critical with automated Telegram dispatch ready, Sir."
        )

        return {
            "response": response,
            "action_type": "SENTINEL_TELEMETRY",
            "active_monitors": daemon_status.active_monitors_count,
            "services_up": daemon_status.services_up_count,
            "services_down": daemon_status.services_down_count,
            "confidence_score": 1.0,
        }


sentinel_agent = SentinelAgent()
