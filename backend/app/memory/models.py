"""CYRUS Memory Data Models.

Defines memory categories (Personal, Business, Working) and fact types,
supporting tenant isolation, confidence scoring, and source tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MemoryCategory(str, Enum):
    """The three major memory categories defined in CYRUS specification."""
    PERSONAL = "personal"  # User preferences, routines, study goals
    BUSINESS = "business"  # Company information, clients, projects, invoices
    WORKING = "working"    # Current in-flight tasks, pending actions, active context


class FactType(str, Enum):
    """Distinction between verified facts and temporary assumptions."""
    VERIFIED_FACT = "VERIFIED_FACT"        # Confirmed truth
    PREFERENCE = "PREFERENCE"              # Personal style / habit
    ROUTINE = "ROUTINE"                    # Daily / study schedule
    ASSUMPTION = "ASSUMPTION"              # Temporary working hypothesis
    TASK_GOAL = "TASK_GOAL"                # Current active task


@dataclass
class MemoryItemRecord:
    """Represents a single persistent memory entry."""
    id: str
    category: MemoryCategory
    tenant_id: str
    memory_key: str
    memory_value: str
    fact_type: FactType = FactType.VERIFIED_FACT
    confidence: float = 1.0
    source: str = "user_explicit"
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""
