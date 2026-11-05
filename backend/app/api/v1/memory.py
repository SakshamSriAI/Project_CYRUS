"""CYRUS Memory & Session Recovery REST API Endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.memory.memory_store import memory_store
from backend.app.memory.models import FactType, MemoryCategory
from backend.app.memory.session_recovery import session_recovery

router = APIRouter(prefix="/memory", tags=["Memory & Knowledge"])


class AddMemoryPayload(BaseModel):
    category: str = Field(..., description="personal, business, or working")
    memory_key: str = Field(..., min_length=1, description="Identifier key e.g. study_routine")
    memory_value: str = Field(..., min_length=1, description="Content or value to remember")
    tenant_id: Optional[str] = Field("default", description="Tenant ID for business data isolation")
    fact_type: Optional[str] = Field("VERIFIED_FACT", description="VERIFIED_FACT, PREFERENCE, ROUTINE, ASSUMPTION, TASK_GOAL")
    confidence: Optional[float] = Field(1.0, ge=0.0, le=1.0)


class UpdateMemoryPayload(BaseModel):
    memory_value: str = Field(..., min_length=1)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    fact_type: Optional[str] = Field(None)


class CheckpointPayload(BaseModel):
    session_id: str
    open_section: Optional[str] = "dashboard"


@router.get("/items")
async def list_memories(
    category: Optional[str] = None,
    tenant_id: str = "default",
    search: Optional[str] = None,
):
    """Retrieves stored memories with category and tenant filtering."""
    cat_enum = None
    if category:
        try:
            cat_enum = MemoryCategory(category.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    items = await memory_store.list_memories(
        category=cat_enum,
        tenant_id=tenant_id,
        search_term=search,
    )
    return {"total_count": len(items), "items": items}


@router.post("/items")
async def save_memory_item(payload: AddMemoryPayload):
    """Saves or updates a memory item into SQLite."""
    try:
        cat_enum = MemoryCategory(payload.category.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {payload.category}")

    try:
        fact_enum = FactType(payload.fact_type) if payload.fact_type else FactType.VERIFIED_FACT
    except ValueError:
        fact_enum = FactType.VERIFIED_FACT

    result = await memory_store.save_memory(
        category=cat_enum,
        memory_key=payload.memory_key,
        memory_value=payload.memory_value,
        tenant_id=payload.tenant_id or "default",
        fact_type=fact_enum,
        confidence=payload.confidence or 1.0,
        source="user_explicit",
    )
    return result


@router.delete("/items/{memory_id}")
async def delete_memory_item(memory_id: str, hard_delete: bool = False):
    """Deletes a memory entry with an audit log."""
    success = await memory_store.delete_memory(
        memory_id=memory_id,
        soft_delete=not hard_delete,
        actor="Saksham",
    )
    if not success:
        raise HTTPException(status_code=404, detail="Memory item not found or already deleted.")
    return {"success": True, "deleted_id": memory_id}


@router.get("/recovery/briefing")
async def get_recovery_briefing():
    """Generates the JARVIS-style session recovery report and briefing."""
    briefing = await session_recovery.get_recovery_briefing()
    return briefing


@router.post("/checkpoint")
async def save_checkpoint(payload: CheckpointPayload):
    """Saves an incremental state checkpoint for session durability."""
    success = await session_recovery.save_checkpoint(
        session_id=payload.session_id,
        open_section=payload.open_section or "dashboard",
    )
    return {"success": success, "session_id": payload.session_id}
