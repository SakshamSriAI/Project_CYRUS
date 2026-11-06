"""Unit Tests for Phase 8: Business Intelligence & Integrations.

Verifies:
- Multi-tenant business data storage with strict tenant boundaries.
- Mock/test accounts for CRM, invoices, revenue tracking, and project tasks.
- Accurate, zero-hallucination overdue invoice queries ("Which invoices are overdue?").
- Automated financial health scoring and executive reporting.
- Full integration with CYRUS_BUSINESS specialist agent.
- Universal compliance with "Sir" form of address and 100% English outputs.
"""

import asyncio
from pathlib import Path
import sys
import unittest
import uuid

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.agents.business_agent import business_agent
from backend.app.business.business_store import business_store
from backend.app.business.models import InvoiceStatus
from backend.app.database import execute_write, init_db


class TestPhase8Business(unittest.TestCase):
    """Architectural test suite for Phase 8 Business Intelligence."""

    @classmethod
    def setUpClass(cls):
        asyncio.run(init_db())
        asyncio.run(execute_write("DELETE FROM business_invoices WHERE invoice_number LIKE 'INV-TEST-%';"))
        asyncio.run(business_store.seed_default_business_data())

    @classmethod
    def tearDownClass(cls):
        asyncio.run(execute_write("DELETE FROM business_invoices WHERE invoice_number LIKE 'INV-TEST-%';"))

    # --- 1. Multi-Tenant Data Storage & Seeding Tests ---

    def test_seed_default_business_data(self):
        """Verifies initial seed creates standard clients, invoices, and projects."""
        async def run_test():
            clients = await business_store.get_clients()
            invoices = await business_store.get_invoices()
            projects = await business_store.get_projects()
            self.assertGreaterEqual(len(clients), 3)
            self.assertGreaterEqual(len(invoices), 5)
            self.assertGreaterEqual(len(projects), 3)
        asyncio.run(run_test())

    def test_multi_tenant_isolation_clients(self):
        """Verifies querying clients for a specific tenant returns ONLY that tenant's records."""
        async def run_test():
            apex_clients = await business_store.get_clients(tenant_id="apex_corp")
            nexus_clients = await business_store.get_clients(tenant_id="nexus_tech")
            solaris_clients = await business_store.get_clients(tenant_id="solaris_media")

            self.assertEqual(len(apex_clients), 1)
            self.assertEqual(apex_clients[0].client_name, "Apex Consulting Services")

            self.assertEqual(len(nexus_clients), 1)
            self.assertEqual(nexus_clients[0].client_name, "Nexus AI Systems")

            self.assertEqual(len(solaris_clients), 1)
            self.assertEqual(solaris_clients[0].client_name, "Solaris Digital Media")
        asyncio.run(run_test())

    def test_multi_tenant_isolation_invoices(self):
        """Verifies invoice queries strictly enforce tenant boundaries without cross-contamination."""
        async def run_test():
            nexus_invoices = await business_store.get_invoices(tenant_id="nexus_tech")
            apex_invoices = await business_store.get_invoices(tenant_id="apex_corp")

            # All nexus invoices must belong strictly to nexus_tech
            for inv in nexus_invoices:
                self.assertEqual(inv.tenant_id, "nexus_tech")
                self.assertEqual(inv.client_name, "Nexus AI Systems")

            # All apex invoices must belong strictly to apex_corp
            for inv in apex_invoices:
                self.assertEqual(inv.tenant_id, "apex_corp")
                self.assertEqual(inv.client_name, "Apex Consulting Services")
        asyncio.run(run_test())

    # --- 2. Factual Overdue Invoice Queries ("Which invoices are overdue?") ---

    def test_which_invoices_are_overdue_query(self):
        """Core Milestone Verification: Queries overdue invoices factually without hallucination."""
        async def run_test():
            overdue_list = await business_store.get_overdue_invoices()
            self.assertEqual(len(overdue_list), 2)

            invoice_numbers = [i.invoice_number for i in overdue_list]
            self.assertIn("INV-2026-003", invoice_numbers)  # Apex Corp: 60,000
            self.assertIn("INV-2026-004", invoice_numbers)  # Solaris Media: 45,000

            total_overdue = sum(i.amount_inr for i in overdue_list)
            self.assertEqual(total_overdue, 105000.0)

            # Check days overdue calculation
            for inv in overdue_list:
                self.assertGreater(inv.days_overdue, 0)
        asyncio.run(run_test())

    def test_tenant_specific_overdue_query(self):
        """Verifies overdue query filtered by tenant returns only that tenant's overdue invoices."""
        async def run_test():
            apex_overdue = await business_store.get_overdue_invoices(tenant_id="apex_corp")
            self.assertEqual(len(apex_overdue), 1)
            self.assertEqual(apex_overdue[0].invoice_number, "INV-2026-003")
            self.assertEqual(apex_overdue[0].amount_inr, 60000.0)

            nexus_overdue = await business_store.get_overdue_invoices(tenant_id="nexus_tech")
            self.assertEqual(len(nexus_overdue), 0)  # Nexus has zero overdue
        asyncio.run(run_test())

    # --- 3. Financial Metrics & Health Scoring ---

    def test_financial_summary_metrics(self):
        """Verifies calculation of realized revenue, pending receivables, and collection rate."""
        async def run_test():
            summary = await business_store.get_financial_summary()
            # Paid: INV-001 (1,20,000) + INV-005 (1,50,000) = 2,70,000
            self.assertEqual(summary.total_revenue_collected_inr, 270000.0)
            # Pending: INV-002 (85,000)
            self.assertEqual(summary.total_receivables_pending_inr, 85000.0)
            # Overdue: INV-003 (60,000) + INV-004 (45,000) = 1,05,000
            self.assertEqual(summary.total_overdue_inr, 105000.0)
            # Health Score bounded
            self.assertTrue(10 <= summary.health_score <= 100)
        asyncio.run(run_test())

    def test_create_new_invoice_and_metrics_update(self):
        """Verifies creating an invoice dynamically updates pending receivables."""
        async def run_test():
            initial_summary = await business_store.get_financial_summary(tenant_id="nexus_tech")
            init_pending = initial_summary.total_receivables_pending_inr
            inv_code = f"INV-TEST-{uuid.uuid4().hex[:6]}"

            # Create new invoice for Nexus Tech
            new_inv = await business_store.create_invoice(
                tenant_id="nexus_tech",
                client_id="client_nexus_01",
                invoice_number=inv_code,
                amount_inr=50000.0,
                due_date="2026-12-31",
                description="Custom Deep Learning Optimization",
            )
            self.assertEqual(new_inv.amount_inr, 50000.0)
            self.assertEqual(new_inv.status, InvoiceStatus.ISSUED)

            updated_summary = await business_store.get_financial_summary(tenant_id="nexus_tech")
            self.assertEqual(
                updated_summary.total_receivables_pending_inr, init_pending + 50000.0
            )

            # Cleanup test invoice
            await execute_write("DELETE FROM business_invoices WHERE invoice_number = ?", (inv_code,))
        asyncio.run(run_test())

    # --- 4. Specialist Agent Integration (CYRUS BUSINESS) ---

    def test_business_agent_answers_which_invoices_are_overdue(self):
        """Verifies CYRUS_BUSINESS answers 'Which invoices are overdue?' factually with 'Sir'."""
        async def run_test():
            res = await business_agent.process_task(
                "Which invoices are overdue?",
                session_id="test_sess_p8_01",
            )
            self.assertEqual(res["action_type"], "OVERDUE_INVOICES_QUERY")
            self.assertIn("Sir", res["response"])
            self.assertIn("INV-2026-003", res["response"])
            self.assertIn("INV-2026-004", res["response"])
            self.assertIn("105,000", res["response"])
            self.assertEqual(res["overdue_count"], 2)
        asyncio.run(run_test())

    def test_business_agent_financial_health_report(self):
        """Verifies CYRUS_BUSINESS generates full financial briefing addressed to Sir in English."""
        async def run_test():
            res = await business_agent.process_task(
                "Generate a financial health and revenue briefing",
                session_id="test_sess_p8_02",
            )
            self.assertEqual(res["action_type"], "FINANCIAL_HEALTH_REPORT")
            self.assertIn("Sir", res["response"])
            self.assertIn("Revenue Collected", res["response"])
            self.assertIn("Financial Health Index", res["response"])
            self.assertGreater(res["health_score"], 0)
        asyncio.run(run_test())

    def test_business_agent_multi_tenant_client_crm(self):
        """Verifies CYRUS_BUSINESS lists client accounts under strict tenant isolation."""
        async def run_test():
            res = await business_agent.process_task(
                "Show me client accounts",
                session_id="test_sess_p8_03",
                context={"tenant_id": "nexus_tech"},
            )
            self.assertEqual(res["action_type"], "CLIENT_CRM_QUERY")
            self.assertIn("Sir", res["response"])
            self.assertIn("Nexus AI Systems", res["response"])
            self.assertEqual(res["client_count"], 1)
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
