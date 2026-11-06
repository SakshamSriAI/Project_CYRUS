"""CYRUS Persistent Memory Store (SQLite WAL Backend).

Manages CRUD operations for Personal, Business, and Working memory.
Enforces multi-tenant isolation, source tracking, and soft/hard deletions.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid
from backend.app.database import execute_query, execute_write
from backend.app.guardian.audit import log_audit_event
from backend.app.memory.models import FactType, MemoryCategory

logger = logging.getLogger("cyrus.memory.store")


class MemoryStore:
    """Persistent storage engine for CYRUS knowledge and context."""

    async def save_memory(
        self,
        category: MemoryCategory,
        memory_key: str,
        memory_value: str,
        tenant_id: str = "default",
        fact_type: FactType = FactType.VERIFIED_FACT,
        confidence: float = 1.0,
        source: str = "user_explicit",
    ) -> Dict[str, Any]:
        """Saves or updates a memory item in SQLite with upsert logic."""
        now = datetime.now(timezone.utc).isoformat()
        memory_id = f"mem_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"

        query = """
        INSERT INTO memory_items (
            id, category, tenant_id, memory_key, memory_value, fact_type,
            confidence, source, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(category, tenant_id, memory_key) DO UPDATE SET
            memory_value = excluded.memory_value,
            fact_type = excluded.fact_type,
            confidence = excluded.confidence,
            source = excluded.source,
            is_active = 1,
            updated_at = excluded.updated_at;
        """
        await execute_write(
            query,
            (
                memory_id,
                category.value if isinstance(category, MemoryCategory) else str(category),
                tenant_id,
                memory_key,
                memory_value,
                fact_type.value if isinstance(fact_type, FactType) else str(fact_type),
                confidence,
                source,
                now,
                now,
            ),
        )

        logger.info(
            "Saved memory [%s/%s] key='%s' (type=%s, conf=%.2f)",
            category, tenant_id, memory_key, fact_type, confidence
        )

        # Audit log entry
        await log_audit_event(
            actor="CYRUS_MEMORY",
            action="SAVE_MEMORY",
            target_resource=f"{category}:{tenant_id}:{memory_key}",
            risk_level=3,
            decision="ALLOWED",
            details={"key": memory_key, "source": source, "fact_type": str(fact_type)},
        )

        return {
            "id": memory_id,
            "category": category,
            "tenant_id": tenant_id,
            "memory_key": memory_key,
            "memory_value": memory_value,
            "fact_type": fact_type,
            "confidence": confidence,
            "source": source,
            "updated_at": now,
        }

    async def get_memory(
        self,
        category: MemoryCategory,
        memory_key: str,
        tenant_id: str = "default",
    ) -> Optional[Dict[str, Any]]:
        """Retrieves an active memory entry by key, category, and tenant."""
        cat_str = category.value if isinstance(category, MemoryCategory) else str(category)
        query = """
        SELECT * FROM memory_items
        WHERE category = ? AND tenant_id = ? AND memory_key = ? AND is_active = 1;
        """
        rows = await execute_query(query, (cat_str, tenant_id, memory_key))
        return rows[0] if rows else None

    async def list_memories(
        self,
        category: Optional[MemoryCategory] = None,
        tenant_id: str = "default",
        search_term: Optional[str] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Lists memories matching filters and search queries."""
        query = "SELECT * FROM memory_items WHERE tenant_id = ?"
        params: List[Any] = [tenant_id]

        if category:
            cat_str = category.value if isinstance(category, MemoryCategory) else str(category)
            query += " AND category = ?"
            params.append(cat_str)

        if not include_inactive:
            query += " AND is_active = 1"

        if search_term and search_term.strip():
            query += " AND (memory_key LIKE ? OR memory_value LIKE ?)"
            term = f"%{search_term.strip()}%"
            params.extend([term, term])

        query += " ORDER BY updated_at DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        query += ";"
        rows = await execute_query(query, tuple(params))
        return rows

    async def delete_memory(
        self,
        memory_id: str,
        soft_delete: bool = True,
        actor: str = "Saksham",
    ) -> bool:
        """Deletes a memory item with audit logging."""
        now = datetime.now(timezone.utc).isoformat()
        if soft_delete:
            query = "UPDATE memory_items SET is_active = 0, updated_at = ? WHERE id = ?;"
            affected = await execute_write(query, (now, memory_id))
        else:
            query = "DELETE FROM memory_items WHERE id = ?;"
            affected = await execute_write(query, (memory_id,))

        if affected > 0:
            await log_audit_event(
                actor=actor,
                action="DELETE_MEMORY",
                target_resource=f"memory:{memory_id}",
                risk_level=3,
                decision="ALLOWED",
                details={"soft_delete": soft_delete, "memory_id": memory_id},
            )
            logger.info("Deleted memory item ID %s (soft=%s)", memory_id, soft_delete)
            return True
        return False

    async def update_memory(
        self,
        memory_id: str,
        new_value: str,
        confidence: Optional[float] = None,
        fact_type: Optional[FactType] = None,
        actor: str = "Saksham",
    ) -> bool:
        """Updates the value, confidence, or fact_type of an existing memory entry."""
        now = datetime.now(timezone.utc).isoformat()
        query = "UPDATE memory_items SET memory_value = ?, updated_at = ?"
        params: List[Any] = [new_value, now]

        if confidence is not None:
            query += ", confidence = ?"
            params.append(confidence)

        if fact_type is not None:
            query += ", fact_type = ?"
            params.append(fact_type.value if isinstance(fact_type, FactType) else str(fact_type))

        query += " WHERE id = ?;"
        params.append(memory_id)

        affected = await execute_write(query, tuple(params))
        if affected > 0:
            await log_audit_event(
                actor=actor,
                action="UPDATE_MEMORY",
                target_resource=f"memory:{memory_id}",
                risk_level=3,
                decision="ALLOWED",
                details={"memory_id": memory_id, "new_value": new_value},
            )
            return True
        return False


# Global singleton instance
memory_store = MemoryStore()
