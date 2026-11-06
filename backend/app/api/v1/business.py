"""CYRUS Business Intelligence & Multi-Tenant Integrations API Router.

Provides endpoints for:
- Multi-tenant client portfolio management.
- Invoices and accounts receivable tracking.
- Overdue invoice auditing with zero hallucination.
- Financial health scoring and executive reporting.
- Project milestone and deliverables tracking.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from backend.app.business.business_store import business_store

router = APIRouter(prefix="/business", tags=["CYRUS Business Intelligence & Integrations"])


# --- Request Models ---

class CreateClientRequest(BaseModel):
    tenant_id: str = Field(..., description="Unique tenant identifier for data boundary isolation")
    client_name: str = Field(..., description="Enterprise client legal or trade name")
    contact_email: Optional[str] = Field(None, description="Primary billing contact email")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata attributes")


class CreateInvoiceRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant identifier")
    client_id: str = Field(..., description="Target client ID")
    invoice_number: str = Field(..., description="Unique invoice code (e.g. INV-2026-006)")
    amount_inr: float = Field(..., gt=0, description="Invoice amount in INR")
    due_date: str = Field(..., description="Payment due date (YYYY-MM-DD)")
    description: Optional[str] = Field(None, description="Scope description or milestone name")


# --- Endpoints ---

@router.get("/summary")
async def get_financial_summary(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID or omit for global portfolio")
) -> Dict[str, Any]:
    """Retrieves real-time financial telemetry, overdue totals, and health score."""
    summary = await business_store.get_financial_summary(tenant_id=tenant_id)
    return {
        "tenant_id": summary.tenant_id or "global",
        "total_revenue_collected_inr": summary.total_revenue_collected_inr,
        "total_receivables_pending_inr": summary.total_receivables_pending_inr,
        "total_overdue_inr": summary.total_overdue_inr,
        "active_client_count": summary.active_client_count,
        "active_project_count": summary.active_project_count,
        "collection_efficiency_percent": summary.collection_efficiency_percent,
        "health_score": summary.health_score,
        "overdue_invoices_count": len(summary.overdue_invoices),
    }


@router.get("/health-report")
async def get_financial_health_report(
    tenant_id: Optional[str] = Query(None, description="Tenant ID or omit for all")
) -> Dict[str, Any]:
    """Generates an executive briefing answering financial questions factually for Sir."""
    report_text = await business_store.generate_executive_financial_report(tenant_id=tenant_id)
    summary = await business_store.get_financial_summary(tenant_id=tenant_id)
    return {
        "report": report_text,
        "health_score": summary.health_score,
        "overdue_count": len(summary.overdue_invoices),
        "total_overdue_inr": summary.total_overdue_inr,
    }


@router.get("/invoices")
async def list_invoices(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    status: Optional[str] = Query(None, description="Filter by status (PAID, ISSUED, OVERDUE)"),
) -> Dict[str, Any]:
    """Retrieves verified accounts receivable invoices with client names."""
    invoices = await business_store.get_invoices(tenant_id=tenant_id, status=status)
    return {
        "count": len(invoices),
        "invoices": [
            {
                "id": inv.id,
                "tenant_id": inv.tenant_id,
                "client_id": inv.client_id,
                "client_name": inv.client_name,
                "invoice_number": inv.invoice_number,
                "amount_inr": inv.amount_inr,
                "status": inv.status.value,
                "issue_date": inv.issue_date,
                "due_date": inv.due_date,
                "paid_date": inv.paid_date,
                "description": inv.description,
                "days_overdue": inv.days_overdue,
            }
            for inv in invoices
        ],
    }


@router.get("/invoices/overdue")
async def list_overdue_invoices(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID")
) -> Dict[str, Any]:
    """Returns strictly overdue invoices requiring executive follow-up."""
    overdue = await business_store.get_overdue_invoices(tenant_id=tenant_id)
    return {
        "count": len(overdue),
        "total_overdue_inr": sum(i.amount_inr for i in overdue),
        "overdue_invoices": [
            {
                "id": inv.id,
                "tenant_id": inv.tenant_id,
                "client_name": inv.client_name,
                "invoice_number": inv.invoice_number,
                "amount_inr": inv.amount_inr,
                "due_date": inv.due_date,
                "days_overdue": inv.days_overdue,
                "description": inv.description,
            }
            for inv in overdue
        ],
    }


@router.post("/invoices")
async def create_invoice(request: CreateInvoiceRequest) -> Dict[str, Any]:
    """Issues a new accounts receivable invoice."""
    try:
        inv = await business_store.create_invoice(
            tenant_id=request.tenant_id,
            client_id=request.client_id,
            invoice_number=request.invoice_number,
            amount_inr=request.amount_inr,
            due_date=request.due_date,
            description=request.description,
        )
        return {
            "success": True,
            "invoice": {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "client_name": inv.client_name,
                "amount_inr": inv.amount_inr,
                "status": inv.status.value,
                "due_date": inv.due_date,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to issue invoice: {e}")


@router.get("/clients")
async def list_clients(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID")
) -> Dict[str, Any]:
    """Retrieves enterprise client accounts under strict tenant isolation."""
    clients = await business_store.get_clients(tenant_id=tenant_id)
    return {
        "count": len(clients),
        "clients": [
            {
                "id": c.id,
                "tenant_id": c.tenant_id,
                "client_name": c.client_name,
                "contact_email": c.contact_email,
                "status": c.status.value,
                "created_at": c.created_at,
                "metadata": c.metadata,
            }
            for c in clients
        ],
    }


@router.post("/clients")
async def create_client(request: CreateClientRequest) -> Dict[str, Any]:
    """Registers a new enterprise client within a tenant sandbox."""
    try:
        client = await business_store.create_client(
            tenant_id=request.tenant_id,
            client_name=request.client_name,
            contact_email=request.contact_email,
            metadata=request.metadata,
        )
        return {
            "success": True,
            "client": {
                "id": client.id,
                "tenant_id": client.tenant_id,
                "client_name": client.client_name,
                "status": client.status.value,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to register client: {e}")


@router.get("/projects")
async def list_projects(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID")
) -> Dict[str, Any]:
    """Retrieves project deliverables, budgets, and milestone progress."""
    projects = await business_store.get_projects(tenant_id=tenant_id)
    return {
        "count": len(projects),
        "projects": [
            {
                "id": p.id,
                "tenant_id": p.tenant_id,
                "client_id": p.client_id,
                "client_name": p.client_name,
                "name": p.name,
                "status": p.status.value,
                "budget_inr": p.budget_inr,
                "progress_percent": p.progress_percent,
                "deadline": p.deadline,
            }
            for p in projects
        ],
    }


@router.post("/seed-demo-data")
async def seed_demo_data() -> Dict[str, Any]:
    """Forces verification and seeding of demonstration enterprise accounts."""
    seeded = await business_store.seed_default_business_data()
    return {"seeded": seeded, "message": "Demo business data verified."}
