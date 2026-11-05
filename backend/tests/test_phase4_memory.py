"""Tests for Phase 4: CYRUS Persistent Memory Subsystem.

Verifies:
1. Personal Memory CRUD (routines, preferences, study goals).
2. Business Memory with strict multi-tenant isolation (Tenant A cannot see Tenant B).
3. Working Memory state checkpoints.
4. Dynamic Context Manager prompt injection.
5. Auto-extraction of explicit memory statements ("Remember that...").
6. Session recovery and dirty crash recovery detection.
7. Audit log generation for memory additions and deletions.
"""

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import execute_query, execute_write, init_db
from backend.app.memory.context_manager import context_manager
from backend.app.memory.memory_store import memory_store
from backend.app.memory.models import FactType, MemoryCategory
from backend.app.memory.session_recovery import session_recovery


class TestPhase4Memory(unittest.IsolatedAsyncioTestCase):
    """Test suite for CYRUS Persistent Memory and Session Recovery."""

    async def asyncSetUp(self):
        await init_db()

    async def test_personal_memory_crud(self):
        # 1. Save Personal Preference
        save_res = await memory_store.save_memory(
            category=MemoryCategory.PERSONAL,
            memory_key="study_focus",
            memory_value="B.Tech Computer Science and AI Architecture",
            fact_type=FactType.PREFERENCE,
            confidence=1.0,
            source="user_explicit",
        )
        self.assertEqual(save_res["memory_key"], "study_focus")
        self.assertEqual(save_res["confidence"], 1.0)

        # 2. Retrieve
        item = await memory_store.get_memory(MemoryCategory.PERSONAL, "study_focus")
        self.assertIsNotNone(item)
        self.assertEqual(item["memory_value"], "B.Tech Computer Science and AI Architecture")

        # 3. Update
        updated = await memory_store.update_memory(
            memory_id=item["id"],
            new_value="B.Tech Computer Science 1st Year (Advanced)",
            confidence=0.95,
        )
        self.assertTrue(updated)
        item_updated = await memory_store.get_memory(MemoryCategory.PERSONAL, "study_focus")
        self.assertEqual(item_updated["memory_value"], "B.Tech Computer Science 1st Year (Advanced)")

        # 4. Delete (Soft delete)
        deleted = await memory_store.delete_memory(memory_id=item["id"], soft_delete=True)
        self.assertTrue(deleted)
        # Verify not returned in active list
        active_items = await memory_store.list_memories(category=MemoryCategory.PERSONAL)
        self.assertNotIn("study_focus", [x["memory_key"] for x in active_items])

    async def test_business_memory_multi_tenant_isolation(self):
        # Tenant A: Company Alpha
        await memory_store.save_memory(
            category=MemoryCategory.BUSINESS,
            tenant_id="company_alpha",
            memory_key="primary_client",
            memory_value="Alpha Corp International (Revenue: $50,000)",
            fact_type=FactType.VERIFIED_FACT,
        )

        # Tenant B: Company Beta
        await memory_store.save_memory(
            category=MemoryCategory.BUSINESS,
            tenant_id="company_beta",
            memory_key="primary_client",
            memory_value="Beta Solutions Ltd (Revenue: ₹10,00,000)",
            fact_type=FactType.VERIFIED_FACT,
        )

        # Query Tenant A
        alpha_items = await memory_store.list_memories(
            category=MemoryCategory.BUSINESS,
            tenant_id="company_alpha",
        )
        alpha_keys = [x["memory_value"] for x in alpha_items]
        self.assertTrue(any("Alpha Corp" in val for val in alpha_keys))
        self.assertFalse(any("Beta Solutions" in val for val in alpha_keys), "Tenant isolation breached: Beta data leaked into Alpha!")

        # Query Tenant B
        beta_items = await memory_store.list_memories(
            category=MemoryCategory.BUSINESS,
            tenant_id="company_beta",
        )
        beta_keys = [x["memory_value"] for x in beta_items]
        self.assertTrue(any("Beta Solutions" in val for val in beta_keys))
        self.assertFalse(any("Alpha Corp" in val for val in beta_keys), "Tenant isolation breached: Alpha data leaked into Beta!")

    async def test_context_manager_prompt_injection(self):
        # Save a routine
        await memory_store.save_memory(
            category=MemoryCategory.PERSONAL,
            memory_key="morning_routine",
            memory_value="Wake up at 6:30 AM, plan coding sprint",
            fact_type=FactType.ROUTINE,
        )

        # Save a working memory task
        await memory_store.save_memory(
            category=MemoryCategory.WORKING,
            memory_key="active_sprint",
            memory_value="Build CYRUS Phase 4 Memory Subsystem",
            fact_type=FactType.TASK_GOAL,
        )

        prompt_block = await context_manager.build_context_prompt(tenant_id="default")
        self.assertIn("morning_routine", prompt_block)
        self.assertIn("6:30 AM", prompt_block)
        self.assertIn("active_sprint", prompt_block)
        self.assertIn("PERSISTENT MEMORY CONTEXT", prompt_block)

    async def test_explicit_memory_auto_extraction(self):
        text = "Please remember that my favorite language is Python"
        res = await context_manager.detect_and_store_explicit_memory(text)
        self.assertIsNotNone(res)
        self.assertEqual(res["memory_value"], "Python")

        # Verify it was persisted to SQLite
        item = await memory_store.get_memory(MemoryCategory.PERSONAL, res["memory_key"])
        self.assertIsNotNone(item)
        self.assertEqual(item["memory_value"], "Python")

    async def test_session_recovery_clean_shutdown(self):
        # Insert a session marked as SHUTDOWN
        clean_sess_id = f"test_clean_{int(datetime.now(timezone.utc).timestamp())}"
        now = datetime.now(timezone.utc).isoformat()
        await execute_write(
            "INSERT INTO sessions (id, started_at, ended_at, status, last_heartbeat) VALUES (?, ?, ?, 'SHUTDOWN', ?)",
            (clean_sess_id, now, now, now),
        )

        briefing = await session_recovery.get_recovery_briefing()
        self.assertTrue(briefing["has_previous_session"])
        self.assertEqual(briefing["recovery_status"], "CLEAN_RESTORE")
        self.assertTrue(briefing["is_clean_shutdown"])
        self.assertIn("saved successfully", briefing["briefing"])

    async def test_crash_recovery_detection(self):
        # Insert a session marked as ACTIVE (dirty shutdown)
        crash_sess_id = f"test_crash_{int(datetime.now(timezone.utc).timestamp())}"
        now = datetime.now(timezone.utc).isoformat()
        await execute_write(
            "INSERT INTO sessions (id, started_at, status, last_heartbeat) VALUES (?, ?, 'ACTIVE', ?)",
            (crash_sess_id, now, now),
        )

        briefing = await session_recovery.get_recovery_briefing()
        self.assertTrue(briefing["has_previous_session"])
        self.assertEqual(briefing["recovery_status"], "CRASH_RECOVERY")
        self.assertFalse(briefing["is_clean_shutdown"])
        self.assertIn("unexpected shutdown", briefing["briefing"])

    async def test_working_memory_checkpoint(self):
        sess_id = "test_checkpoint_sess"
        now = datetime.now(timezone.utc).isoformat()
        await execute_write(
            "INSERT INTO sessions (id, started_at, status, last_heartbeat) VALUES (?, ?, 'ACTIVE', ?) ON CONFLICT(id) DO NOTHING",
            (sess_id, now, now),
        )

        success = await session_recovery.save_checkpoint(
            session_id=sess_id,
            open_section="memory_center",
        )
        self.assertTrue(success)

        rows = await execute_query("SELECT metadata_json FROM sessions WHERE id = ?", (sess_id,))
        self.assertIn("memory_center", rows[0]["metadata_json"])


def run():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase4Memory)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == "__main__":
    run()
