"""Unit Tests for Phase 9: CYRUS SENTINEL & Proactive Local Monitoring.

Verifies:
- Lightweight background health-check engine (pings websites, local servers).
- Event severity classification (Level 1 Info, Level 2 Important, Level 3 Critical).
- Proactive Telegram alert integration with free-tier/simulation mode.
- Mock website downtime simulation detecting downtime within 30 seconds.
- Local monitoring limitations (MacBook sleep and shutdown boundary awareness).
- Specialist agent integration (CYRUS_SENTINEL) and universal "Sir" address.
"""

import asyncio
from pathlib import Path
import sys
import time
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.agents.sentinel_agent import sentinel_agent
from backend.app.database import execute_write, init_db
from backend.app.lifecycle.process_manager import LifecycleState, process_manager
from backend.app.sentinel.models import EventSeverity, MonitorStatus, SentinelEvent
from backend.app.sentinel.telegram_notifier import telegram_notifier
from backend.app.sentinel.watcher import sentinel_watcher


class TestPhase9Sentinel(unittest.TestCase):
    """Architectural test suite for Phase 9 Sentinel Surveillance."""

    @classmethod
    def setUpClass(cls):
        asyncio.run(init_db())
        process_manager.set_state(LifecycleState.ACTIVE)
        asyncio.run(sentinel_watcher.seed_default_monitors())

    def tearDown(self):
        process_manager.set_state(LifecycleState.ACTIVE)

    # --- 1. Monitor Seeding & Listing ---

    def test_seed_default_monitors(self):
        """Verifies default monitoring targets are initialized in SQLite."""
        async def run_test():
            monitors = await sentinel_watcher.get_monitors()
            self.assertGreaterEqual(len(monitors), 4)
            names = [m.name for m in monitors]
            self.assertIn("CYRUS Local Core Backend", names)
            self.assertIn("CYRUS Frontend Interface", names)
            self.assertIn("DuckDuckGo Public Gateway", names)
            self.assertIn("Mock Target Simulation", names)
        asyncio.run(run_test())

    def test_daemon_status_and_limitations_notice(self):
        """Verifies surveillance daemon telemetry surfaces sleep/shutdown boundary notice."""
        async def run_test():
            status = await sentinel_watcher.get_daemon_status()
            self.assertTrue(status.is_running)
            self.assertGreaterEqual(status.active_monitors_count, 4)
            self.assertIn("MacBook Air M5", status.limitations_notice)
            self.assertIn("sleep", status.limitations_notice.lower())
        asyncio.run(run_test())

    # --- 2. Event Severity Classification (Level 1, Level 2, Level 3) ---

    def test_event_severity_single_failure_important(self):
        """Verifies a single failure emits a Level 2 Important warning without setting DOWN."""
        async def run_test():
            # Reset mock monitor
            await execute_write(
                "UPDATE sentinel_monitors SET current_status = 'UP', consecutive_failures = 0 WHERE id = 'mon_mock_service';"
            )
            # 1st failure cycle
            res = await sentinel_watcher.execute_monitor_check("mon_mock_service")
            self.assertEqual(res["consecutive_failures"], 1)
            self.assertEqual(res["status"], MonitorStatus.DEGRADED.value)
            self.assertEqual(res["severity"], EventSeverity.IMPORTANT.value)
        asyncio.run(run_test())

    def test_event_severity_consecutive_failure_critical(self):
        """Verifies consecutive failures (2+) mark target DOWN and emit Level 3 Critical alert."""
        async def run_test():
            # Set to 1 failure first
            await execute_write(
                "UPDATE sentinel_monitors SET current_status = 'DEGRADED', consecutive_failures = 1 WHERE id = 'mon_mock_service';"
            )
            # 2nd failure cycle
            res = await sentinel_watcher.execute_monitor_check("mon_mock_service")
            self.assertEqual(res["consecutive_failures"], 2)
            self.assertEqual(res["status"], MonitorStatus.DOWN.value)
            self.assertEqual(res["severity"], EventSeverity.CRITICAL.value)
        asyncio.run(run_test())

    # --- 3. Downtime Drill: Detection & Alert within 30 seconds ---

    def test_simulated_website_downtime_within_30s(self):
        """Acceptance Criteria: Simulates mock website downtime; verifies detection within 30s."""
        async def run_test():
            drill = await sentinel_watcher.simulate_downtime("mon_mock_service")
            self.assertTrue(drill["success"])
            self.assertEqual(drill["status"], "DOWN")
            self.assertEqual(drill["severity"], "CRITICAL")
            self.assertTrue(drill["within_30s_threshold"])
            self.assertLess(drill["elapsed_seconds"], 30.0)
            self.assertIn("Sir", drill["summary"])
        asyncio.run(run_test())

    # --- 4. Telegram Alert Dispatch & Message Formatting ---

    def test_telegram_alert_message_formatting(self):
        """Verifies Telegram alert message includes 'Sir', severity level, and target details."""
        event = SentinelEvent(
            id="test_evt_101",
            monitor_id="mon_core_backend",
            monitor_name="CYRUS Local Core Backend",
            severity=EventSeverity.CRITICAL,
            title="Service Unreachable",
            message="Connection refused during health ping.",
            latency_ms=None,
            status_code=503,
            is_resolved=False,
        )
        msg = telegram_notifier.format_alert_message(event, "CYRUS Local Core Backend", "http://127.0.0.1:8000/api/v1/health")
        self.assertIn("Sir", msg)
        self.assertIn("LEVEL 3 CRITICAL", msg)
        self.assertIn("CYRUS Local Core Backend", msg)
        self.assertIn("503", msg)

    def test_telegram_dispatch_simulated_mode(self):
        """Verifies Telegram alert delivery operates in simulated free tier when unconfigured."""
        async def run_test():
            event = SentinelEvent(
                id="test_evt_102",
                monitor_id="mon_mock",
                monitor_name="Mock Target",
                severity=EventSeverity.CRITICAL,
                title="Mock Outage",
                message="Mock outage drill.",
            )
            res = await telegram_notifier.send_alert(event, "Mock Target", "http://mock.local")
            self.assertTrue(res["success"])
            self.assertTrue(res["dispatched"])
            self.assertIn(res["mode"], ["SIMULATED_FREE_TIER", "LIVE_TELEGRAM_API"])
        asyncio.run(run_test())

    # --- 5. Lifecycle Guard (Pause & Exam Mode Suspension) ---

    def test_lifecycle_pause_suspends_monitoring(self):
        """Verifies health-check execution immediately suspends when CYRUS is in PAUSED state."""
        async def run_test():
            process_manager.set_state(LifecycleState.PAUSED)
            res = await sentinel_watcher.execute_monitor_check("mon_core_backend")
            self.assertEqual(res["status"], "SUSPENDED_BY_LIFECYCLE")
            self.assertEqual(res["lifecycle_state"], "PAUSED")
        asyncio.run(run_test())

    def test_lifecycle_exam_mode_suspends_monitoring(self):
        """Verifies health-check execution immediately suspends in EXAM_MODE."""
        async def run_test():
            process_manager.set_state(LifecycleState.EXAM_MODE)
            res = await sentinel_watcher.execute_monitor_check("mon_core_backend")
            self.assertEqual(res["status"], "SUSPENDED_BY_LIFECYCLE")
            self.assertEqual(res["lifecycle_state"], "EXAM_MODE")
        asyncio.run(run_test())

    # --- 6. Specialist Agent Integration (CYRUS SENTINEL) ---

    def test_sentinel_agent_telemetry_reporting(self):
        """Verifies CYRUS_SENTINEL reports live surveillance telemetry addressed to Sir."""
        async def run_test():
            res = await sentinel_agent.process_task(
                "Check surveillance status and active monitors",
                session_id="test_sess_p9_01",
            )
            self.assertEqual(res["action_type"], "SENTINEL_TELEMETRY")
            self.assertIn("Sir", res["response"])
            self.assertIn("Services Monitored", res["response"])
            self.assertGreaterEqual(res["active_monitors"], 4)
        asyncio.run(run_test())

    def test_sentinel_agent_sleep_limitations_explanation(self):
        """Verifies CYRUS_SENTINEL explains local MacBook sleep/lid closure boundaries."""
        async def run_test():
            res = await sentinel_agent.process_task(
                "What happens to monitoring when my MacBook goes to sleep or lid is closed?",
                session_id="test_sess_p9_02",
            )
            self.assertEqual(res["action_type"], "LIMITATIONS_ADVISORY")
            self.assertIn("Sir", res["response"])
            self.assertIn("MacBook", res["response"])
            self.assertIn("sleep", res["response"].lower())
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
