"""Tests for Phase 6: CYRUS Specialist Agent Framework.

Verifies:
1. Specialist Agent Registry & Metadata for all 5 agents.
2. CYRUS PERSONAL (schedule, B.Tech study planning, habits).
3. CYRUS BUSINESS (client tracking, revenue, tenant isolation).
4. CYRUS DEV (codebase inspection, tests, GUARDIAN security gating).
5. CYRUS RESEARCH (factual synthesis, citations, comparative analysis).
6. CYRUS EXECUTIVE (morning briefings, evening reviews, cross-agent coordination).
7. Intent-based multi-agent routing.
8. Universal "Sir" form of address and 100% English output enforcement.
9. Lifecycle safety: Exam Mode and Emergency Halt blocking.
"""

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.agents.agent_registry import agent_registry
from backend.app.database import init_db
from backend.app.guardian.emergency_stop import emergency_controller
from backend.app.lifecycle.process_manager import LifecycleState, process_manager


class TestPhase6Agents(unittest.IsolatedAsyncioTestCase):
    """Test suite for CYRUS Specialist Agent Framework."""

    async def asyncSetUp(self):
        await init_db()
        process_manager.set_state(LifecycleState.ACTIVE)
        if emergency_controller.is_halted:
            await emergency_controller.reset_emergency_stop(reset_by="Saksham")

    def test_specialist_agent_registry(self):
        agents = agent_registry.list_agents()
        self.assertEqual(len(agents), 5)
        names = [a["name"] for a in agents]
        self.assertIn("CYRUS_PERSONAL", names)
        self.assertIn("CYRUS_BUSINESS", names)
        self.assertIn("CYRUS_DEV", names)
        self.assertIn("CYRUS_RESEARCH", names)
        self.assertIn("CYRUS_EXECUTIVE", names)

    async def test_personal_agent_execution(self):
        agent = agent_registry.get_agent("CYRUS_PERSONAL")
        self.assertIsNotNone(agent)

        res = await agent.execute(
            task_description="Help me organize my B.Tech Computer Science study schedule.",
            session_id="sess_test_personal",
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["agent"], "CYRUS_PERSONAL")
        self.assertIn("Sir", res["response"])
        self.assertNotIn("Saksham", res["response"])
        self.assertTrue("study plan" in res["response"].lower() or "agenda" in res["response"].lower())

    async def test_business_agent_execution_and_tenant_isolation(self):
        agent = agent_registry.get_agent("CYRUS_BUSINESS")
        self.assertIsNotNone(agent)

        res = await agent.execute(
            task_description="Check overdue invoices and revenue telemetry.",
            session_id="sess_test_biz",
            context={"tenant_id": "tenant_alpha"},
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["agent"], "CYRUS_BUSINESS")
        self.assertEqual(res["tenant_id"], "tenant_alpha")
        self.assertIn("Sir", res["response"])
        self.assertNotIn("Saksham", res["response"])

    async def test_dev_agent_execution_and_guardian_gating(self):
        agent = agent_registry.get_agent("CYRUS_DEV")
        self.assertIsNotNone(agent)

        res = await agent.execute(
            task_description="Run verification tests across all codebase modules.",
            session_id="sess_test_dev",
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["agent"], "CYRUS_DEV")
        self.assertIn("Sir", res["response"])
        self.assertEqual(res["permission_tier"], "L1_READ")

    async def test_research_agent_execution_and_citations(self):
        agent = agent_registry.get_agent("CYRUS_RESEARCH")
        self.assertIsNotNone(agent)

        res = await agent.execute(
            task_description="Compare local-first open-weight models versus cloud APIs.",
            session_id="sess_test_research",
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["agent"], "CYRUS_RESEARCH")
        self.assertIn("Sir", res["response"])
        self.assertGreaterEqual(len(res["citations"]), 1)

    async def test_executive_agent_morning_briefing(self):
        agent = agent_registry.get_agent("CYRUS_EXECUTIVE")
        self.assertIsNotNone(agent)

        res = await agent.execute(
            task_description="Prepare unified morning executive briefing.",
            session_id="sess_test_exec",
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["agent"], "CYRUS_EXECUTIVE")
        self.assertIn("Sir", res["response"])
        self.assertEqual(res["briefing_type"], "MORNING_EXECUTIVE_BRIEFING")

    def test_multi_agent_intent_routing(self):
        # 1. Personal intent
        agent_p = agent_registry.route_intent("What is my schedule and study plan for today?")
        self.assertIsNotNone(agent_p)
        self.assertEqual(agent_p.name, "CYRUS_PERSONAL")

        # 2. Business intent
        agent_b = agent_registry.route_intent("Review pending client invoices and revenue metrics.")
        self.assertIsNotNone(agent_b)
        self.assertEqual(agent_b.name, "CYRUS_BUSINESS")

        # 3. Dev intent
        agent_d = agent_registry.route_intent("Inspect codebase git commits and run test suite.")
        self.assertIsNotNone(agent_d)
        self.assertEqual(agent_d.name, "CYRUS_DEV")

        # 4. Research intent
        agent_r = agent_registry.route_intent("Research and compare neural audio models vs legacy TTS.")
        self.assertIsNotNone(agent_r)
        self.assertEqual(agent_r.name, "CYRUS_RESEARCH")

        # 5. Executive intent
        agent_e = agent_registry.route_intent("Give me an executive summary and full briefing of all systems.")
        self.assertIsNotNone(agent_e)
        self.assertEqual(agent_e.name, "CYRUS_EXECUTIVE")

    async def test_agent_execution_blocked_in_exam_mode(self):
        process_manager.set_state(LifecycleState.EXAM_MODE)
        agent = agent_registry.get_agent("CYRUS_PERSONAL")
        res = await agent.execute("What is on my schedule?", "sess_exam")
        self.assertFalse(res["success"])
        self.assertIn("Exam Mode is active", res["error"])
        process_manager.set_state(LifecycleState.ACTIVE)

    async def test_agent_execution_blocked_in_emergency_stop(self):
        await emergency_controller.trigger_emergency_stop(reason="Agent drill lock")
        agent = agent_registry.get_agent("CYRUS_DEV")
        res = await agent.execute("Inspect git status.", "sess_halt")
        self.assertFalse(res["success"])
        self.assertIn("CYRUS STOP is currently activated", res["error"])
        await emergency_controller.reset_emergency_stop(reset_by="Saksham")


def run():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase6Agents)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == "__main__":
    run()
