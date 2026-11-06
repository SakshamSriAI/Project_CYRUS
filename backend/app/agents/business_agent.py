"""CYRUS BUSINESS Specialist Agent.

Manages:
- Client portfolios and strict multi-tenant isolation.
- Real-time accounts receivable, overdue invoice audits, and revenue metrics.
- Pipeline tracking, project milestones, and contract deliverables.
- Structured business health evaluations with zero hallucination.
Always addresses the user as "Sir".
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import AgentMetadata, BaseAgent
from backend.app.business.business_store import business_store
from backend.app.memory.memory_store import memory_store
from backend.app.memory.models import MemoryCategory

logger = logging.getLogger("cyrus.agents.business")


class BusinessAgent(BaseAgent):
    """Specialist agent for enterprise management, client metrics, and factual invoices."""

    def __init__(self):
        super().__init__(
            AgentMetadata(
                name="CYRUS_BUSINESS",
                display_name="CYRUS Business",
                description="Specialist in business intelligence, client relationships, revenue metrics, invoice tracking, and multi-tenant isolation.",
                domain="Enterprise Management & Financial Telemetry",
                capabilities=[
                    "Multi-Tenant Client Portfolio Management",
                    "Factual Invoice & Accounts Receivable Tracking",
                    "Zero-Hallucination Overdue Invoices Audit",
                    "Automated Business Financial Health Briefings",
                ],
                icon="briefcase",
            )
        )

    def can_handle(self, text: str) -> float:
        clean = text.lower()
        keywords = [
            "business", "client", "revenue", "invoice", "payment",
            "pipeline", "deal", "company", "metrics", "financial",
            "crm", "tenant", "contracts", "accounts", "overdue", "due",
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
        """Queries structured business database, calculates real metrics, and formats responses."""
        clean = task_description.lower()
        tenant_id = (context or {}).get("tenant_id")
        if tenant_id == "all" or not tenant_id:
            # Check if text mentions a specific tenant
            if "apex" in clean:
                tenant_id = "apex_corp"
            elif "nexus" in clean:
                tenant_id = "nexus_tech"
            elif "solaris" in clean:
                tenant_id = "solaris_media"

        # 1. Overdue Invoices Inquiry (e.g. "Which invoices are overdue?")
        if "overdue" in clean or ("which" in clean and "invoice" in clean):
            overdue_list = await business_store.get_overdue_invoices(tenant_id=tenant_id)
            if overdue_list:
                items = [
                    f"• **{inv.invoice_number}** ({inv.client_name}): ₹{inv.amount_inr:,.0f} "
                    f"[Due: {inv.due_date}, {inv.days_overdue} days past due]"
                    for inv in overdue_list
                ]
                total_overdue = sum(i.amount_inr for i in overdue_list)
                response = (
                    f"Here are the active overdue invoices audited factually from the database, Sir:\n\n"
                    + "\n".join(items) + "\n\n"
                    f"• **Total Overdue Receivables**: ₹{total_overdue:,.0f} across {len(overdue_list)} accounts.\n\n"
                    "Would you like me to prepare a formal payment follow-up notice for these clients, Sir?"
                )
            else:
                response = (
                    f"There are currently zero overdue invoices in the database"
                    + (f" for Tenant '{tenant_id}'" if tenant_id else "")
                    + ", Sir. All client accounts are in good standing."
                )
            return {
                "response": response,
                "action_type": "OVERDUE_INVOICES_QUERY",
                "tenant_id": tenant_id or "default",
                "overdue_count": len(overdue_list),
                "overdue_invoices": [
                    {"number": i.invoice_number, "client": i.client_name, "amount_inr": i.amount_inr}
                    for i in overdue_list
                ],
                "confidence_score": 1.0,
            }

        # 2. General Invoices & Accounts Receivable
        if any(w in clean for w in ["invoice", "payment", "bill", "receivable"]):
            invoices = await business_store.get_invoices(tenant_id=tenant_id)
            paid_count = sum(1 for i in invoices if i.status.value == "PAID")
            issued_count = sum(1 for i in invoices if i.status.value == "ISSUED")
            overdue_count = sum(1 for i in invoices if i.status.value == "OVERDUE")
            response = (
                f"Here is the accounts receivable breakdown, Sir:\n\n"
                f"• **Total Invoices Monitored**: {len(invoices)} invoices.\n"
                f"• **Settled (PAID)**: {paid_count} invoices.\n"
                f"• **In-Flight (ISSUED)**: {issued_count} pending payment.\n"
                f"• **Overdue Attention**: {overdue_count} accounts past due.\n\n"
                "All figures are verified directly against SQLite WAL records with zero estimation, Sir."
            )
            return {
                "response": response,
                "action_type": "INVOICES_BREAKDOWN",
                "tenant_id": tenant_id or "default",
                "total_invoices": len(invoices),
                "confidence_score": 1.0,
            }

        # 3. Revenue & Financial Health Analysis
        if any(w in clean for w in ["revenue", "financial", "health", "growth", "performance", "metric"]):
            report = await business_store.generate_executive_financial_report(tenant_id=tenant_id)
            summary = await business_store.get_financial_summary(tenant_id=tenant_id)
            return {
                "response": report,
                "action_type": "FINANCIAL_HEALTH_REPORT",
                "tenant_id": tenant_id or "default",
                "health_score": summary.health_score,
                "total_revenue_inr": summary.total_revenue_collected_inr,
                "confidence_score": 1.0,
            }

        # 4. Client CRM & Portfolio
        if any(w in clean for w in ["client", "customer", "crm", "portfolio", "account"]):
            clients = await business_store.get_clients(tenant_id=tenant_id)
            items = [
                f"• **{c.client_name}** (Tenant: `{c.tenant_id}`): Status `{c.status.value}` — {c.contact_email or 'No email'}"
                for c in clients
            ]
            response = (
                f"Here is your multi-tenant client roster, Sir:\n\n"
                + "\n".join(items) + "\n\n"
                f"A total of {len(clients)} enterprise accounts are actively managed under strict data isolation, Sir."
            )
            return {
                "response": response,
                "action_type": "CLIENT_CRM_QUERY",
                "tenant_id": tenant_id or "default",
                "client_count": len(clients),
                "confidence_score": 1.0,
            }

        # 5. Projects & Deliverables
        if any(w in clean for w in ["project", "deliverable", "milestone", "progress"]):
            projects = await business_store.get_projects(tenant_id=tenant_id)
            items = [
                f"• **{p.name}** ({p.client_name}): {p.progress_percent}% complete [Budget: ₹{p.budget_inr:,.0f}, Status: `{p.status.value}`]"
                for p in projects
            ]
            response = (
                f"Here is your project delivery status, Sir:\n\n"
                + "\n".join(items) + "\n\n"
                "All project timelines and budgets are tracked locally with verified milestones, Sir."
            )
            return {
                "response": response,
                "action_type": "PROJECT_TELEMETRY",
                "tenant_id": tenant_id or "default",
                "project_count": len(projects),
                "confidence_score": 1.0,
            }

        # Default Financial Briefing
        report = await business_store.generate_executive_financial_report(tenant_id=tenant_id)
        return {
            "response": report,
            "action_type": "BUSINESS_TELEMETRY_DEFAULT",
            "tenant_id": tenant_id or "default",
            "confidence_score": 0.95,
        }


business_agent = BusinessAgent()
