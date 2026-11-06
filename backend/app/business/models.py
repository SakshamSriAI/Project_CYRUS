"""CYRUS Business Intelligence Models.

Defines multi-tenant data structures for clients, invoices, projects,
and financial summaries.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ClientStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LEAD = "LEAD"


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class ProjectStatus(str, Enum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"


@dataclass
class Client:
    id: str
    tenant_id: str
    client_name: str
    contact_email: Optional[str] = None
    status: ClientStatus = ClientStatus.ACTIVE
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Invoice:
    id: str
    tenant_id: str
    client_id: str
    client_name: str
    invoice_number: str
    amount_inr: float
    status: InvoiceStatus
    issue_date: str
    due_date: str
    paid_date: Optional[str] = None
    description: Optional[str] = None
    days_overdue: int = 0


@dataclass
class Project:
    id: str
    tenant_id: str
    client_id: str
    client_name: str
    name: str
    status: ProjectStatus
    budget_inr: float
    progress_percent: int = 0
    deadline: Optional[str] = None
    created_at: str = ""


@dataclass
class BusinessFinancialSummary:
    tenant_id: Optional[str]
    total_revenue_collected_inr: float
    total_receivables_pending_inr: float
    total_overdue_inr: float
    active_client_count: int
    active_project_count: int
    collection_efficiency_percent: float
    health_score: int  # 0 to 100
    overdue_invoices: List[Invoice] = field(default_factory=list)
