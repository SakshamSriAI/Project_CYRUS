"""CYRUS Comprehensive Unit Test Runner (Zero-Dependency Python Standard Library).

Runs all architectural and component tests for Phase 1, Phase 2, Phase 3, and Phase 4.
"""

import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.core.language_config import language_governance
from backend.app.core.orchestrator import cyrus_core
from backend.app.database import check_db_health, execute_query, execute_write, init_db
from backend.app.guardian.permissions import (
    ActionRequest,
    PermissionEngine,
    PermissionTier,
    permission_engine,
)
from backend.app.lifecycle.process_manager import (
    LifecycleState,
    process_manager,
)
from backend.tests.test_phase2_core import TestPhase2CoreOrchestrator
from backend.tests.test_phase3_guardian import TestPhase3Guardian
from backend.tests.test_phase4_memory import TestPhase4Memory


class TestLanguageGovernance(unittest.TestCase):
    """Test suite for Language Governance (Hindi/Hinglish understanding -> English output)."""

    def test_english_input_detection(self):
        text = "Good morning, CYRUS. How are you today?"
        self.assertEqual(language_governance.detect_input_language(text), "English")

    def test_hindi_devanagari_input_detection(self):
        text = "आज का मौसम कैसा है और मेरा शेड्यूल क्या है?"
        self.assertEqual(language_governance.detect_input_language(text), "Hindi")

    def test_hinglish_input_detection(self):
        hinglish_samples = [
            "CYRUS, aaj mera schedule kya hai?",
            "Mujhe batao website mein kya problem hai.",
            "Kal subah mujhe 7 baje yaad dilana.",
            "Mera GitHub project open karo.",
            "Aaj ka kaam shuru karo.",
        ]
        for sample in hinglish_samples:
            detected = language_governance.detect_input_language(sample)
            self.assertEqual(detected, "Hinglish", f"Failed for: {sample}")

    def test_response_compliance_english(self):
        english_resp = "Good morning Saksham. All systems are operational. You have 3 tasks scheduled today."
        compliant, reason = language_governance.validate_response_compliance(english_resp)
        self.assertTrue(compliant, reason)

    def test_response_compliance_rejects_devanagari(self):
        hindi_resp = "नमस्ते सक्षम, आपका सिस्टम तैयार है।"
        compliant, reason = language_governance.validate_response_compliance(hindi_resp)
        self.assertFalse(compliant)
        self.assertIn("Devanagari", reason)

    def test_response_compliance_rejects_hinglish(self):
        hinglish_resp = "Haan bhai, aaj aapka kaam shuru karte hain aur kal dekhenge."
        compliant, reason = language_governance.validate_response_compliance(hinglish_resp)
        self.assertFalse(compliant)
        self.assertIn("Hinglish", reason)


class TestGuardianPermissions(unittest.TestCase):
    """Test suite for CYRUS GUARDIAN permission tiers and sandbox bounds."""

    def test_read_in_sandbox_allowed(self):
        req = ActionRequest(
            actor="CORE",
            action_type="read_file",
            target_resource=str(Path(settings.CYRUS_SANDBOX_PATH) / "README.md"),
        )
        res = permission_engine.evaluate_action(req)
        self.assertTrue(res.is_allowed)
        self.assertFalse(res.requires_human_approval)
        self.assertEqual(res.risk_level, PermissionTier.L1_READ)

    def test_read_outside_sandbox_restricted(self):
        req = ActionRequest(
            actor="CORE",
            action_type="read_file",
            target_resource="/etc/passwd",
        )
        res = permission_engine.evaluate_action(req)
        self.assertFalse(res.is_allowed)
        self.assertTrue(res.requires_human_approval)
        self.assertEqual(res.risk_level, PermissionTier.L4_RESTRICTED)

    def test_destructive_delete_restricted(self):
        req = ActionRequest(
            actor="AGENT_DEV",
            action_type="delete_file",
            target_resource=str(Path(settings.CYRUS_SANDBOX_PATH) / "temp.txt"),
        )
        res = permission_engine.evaluate_action(req)
        self.assertFalse(res.is_allowed)
        self.assertTrue(res.requires_human_approval)
        self.assertEqual(res.risk_level, PermissionTier.L4_RESTRICTED)

    def test_write_in_sandbox_execute_tier(self):
        req = ActionRequest(
            actor="AGENT_DEV",
            action_type="write_file",
            target_resource=str(Path(settings.CYRUS_SANDBOX_PATH) / "test.py"),
        )
        res = permission_engine.evaluate_action(req)
        self.assertTrue(res.is_allowed)
        self.assertEqual(res.risk_level, PermissionTier.L3_EXECUTE)


class TestSQLiteDatabase(unittest.IsolatedAsyncioTestCase):
    """Test suite for SQLite WAL mode and table schema."""

    async def test_db_initialization_and_wal(self):
        init_res = await init_db()
        self.assertEqual(init_res["journal_mode"].upper(), "WAL")
        self.assertGreaterEqual(init_res["table_count"], 8)

        health = await check_db_health()
        self.assertTrue(health["healthy"])
        self.assertEqual(health["journal_mode"].upper(), "WAL")

    async def test_session_persistence_crud(self):
        sess_id = f"test-sess-{int(datetime.now(timezone.utc).timestamp())}"
        now = datetime.now(timezone.utc).isoformat()
        await execute_write(
            "INSERT INTO sessions (id, started_at, status, last_heartbeat) VALUES (?, ?, ?, ?)",
            (sess_id, now, "ACTIVE", now),
        )

        rows = await execute_query("SELECT * FROM sessions WHERE id = ?", (sess_id,))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], sess_id)
        self.assertEqual(rows[0]["status"], "ACTIVE")

        await execute_write("DELETE FROM sessions WHERE id = ?", (sess_id,))


class TestProcessManager(unittest.IsolatedAsyncioTestCase):
    """Test suite for Process Ownership and Lifecycle Management."""

    async def test_lifecycle_state_machine(self):
        process_manager.set_state(LifecycleState.ACTIVE)
        self.assertEqual(process_manager.current_state, LifecycleState.ACTIVE)

        pause_res = await process_manager.pause_system()
        self.assertEqual(process_manager.current_state, LifecycleState.PAUSED)
        self.assertEqual(pause_res["status"], "PAUSED")

        resume_res = await process_manager.resume_system()
        self.assertEqual(process_manager.current_state, LifecycleState.ACTIVE)
        self.assertEqual(resume_res["status"], "ACTIVE")

        exam_res = await process_manager.enter_exam_mode()
        self.assertEqual(process_manager.current_state, LifecycleState.EXAM_MODE)
        self.assertEqual(exam_res["status"], "EXAM_MODE_ACTIVE")

        process_manager.set_state(LifecycleState.ACTIVE)

    async def test_process_registration(self):
        my_pid = os.getpid()
        await process_manager.register_process(
            pid=my_pid,
            process_name="cyrus_test_runner",
            purpose="test_process_manager",
            owned_by_cyrus=True,
        )

        active = await process_manager.list_registered_processes(only_running=True)
        matching = [p for p in active if p["pid"] == my_pid]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["process_name"], "cyrus_test_runner")
        self.assertTrue(matching[0]["os_alive"])

        await process_manager.unregister_process(my_pid, "STOPPED")


def run():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite([
        loader.loadTestsFromTestCase(TestLanguageGovernance),
        loader.loadTestsFromTestCase(TestGuardianPermissions),
        loader.loadTestsFromTestCase(TestSQLiteDatabase),
        loader.loadTestsFromTestCase(TestProcessManager),
        loader.loadTestsFromTestCase(TestPhase2CoreOrchestrator),
        loader.loadTestsFromTestCase(TestPhase3Guardian),
        loader.loadTestsFromTestCase(TestPhase4Memory),
    ])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    run()
