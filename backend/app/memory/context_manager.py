"""CYRUS Context Manager & Memory Injection Engine.

Responsible for:
1. Building structured context blocks from Personal, Business, and Working memory.
2. Inforcing multi-tenant isolation (Business Memory of Tenant A never bleeds into Tenant B).
3. Detecting explicit user memory updates ("Remember that...", "Yaad rakhna...").
4. Injecting verified facts and routines into CYRUS CORE prompts.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from backend.app.memory.memory_store import memory_store
from backend.app.memory.models import FactType, MemoryCategory

logger = logging.getLogger("cyrus.memory.context")


class ContextManager:
    """Orchestrates memory retrieval and prompt injection."""

    async def build_context_prompt(self, tenant_id: str = "default", session_id: Optional[str] = None) -> str:
        """Assembles verified Personal, Business, and Working memory into a clean context block."""
        # 1. Personal Memory (Always applicable to Saksham)
        personal_items = await memory_store.list_memories(
            category=MemoryCategory.PERSONAL,
            tenant_id="default",
        )

        # 2. Business Memory (Strictly isolated by tenant_id)
        business_items = await memory_store.list_memories(
            category=MemoryCategory.BUSINESS,
            tenant_id=tenant_id,
        )

        # 3. Working Memory (Active session state)
        working_items = await memory_store.list_memories(
            category=MemoryCategory.WORKING,
            tenant_id="default",
        )

        context_lines = []
        if personal_items:
            context_lines.append("[Personal Knowledge & Preferences]:")
            for item in personal_items[:8]:
                context_lines.append(f"- {item['memory_key']}: {item['memory_value']} ({item['fact_type']})")

        if business_items:
            context_lines.append(f"\n[Business Information (Tenant: {tenant_id})]:")
            for item in business_items[:8]:
                context_lines.append(f"- {item['memory_key']}: {item['memory_value']}")

        if working_items:
            context_lines.append("\n[Active Working Memory & Goals]:")
            for item in working_items[:5]:
                context_lines.append(f"- {item['memory_key']}: {item['memory_value']}")

        if not context_lines:
            return ""

        return (
            "--- PERSISTENT MEMORY CONTEXT ---\n"
            + "\n".join(context_lines)
            + "\n---------------------------------"
        )

    async def detect_and_store_explicit_memory(
        self,
        text: str,
        detected_language: str = "English",
    ) -> Optional[Dict[str, Any]]:
        """Detects if Saksham is stating a persistent preference or rule to remember."""
        clean = text.strip()

        # Patterns like: "Remember that [key] is [value]", "Yaad rakhna ki [key] [value] hai"
        patterns = [
            r"(?:please\s+)?remember\s+that\s+(.+?)\s+(?:is|=|:)\s+(.+)",
            r"(?:please\s+)?remember\s+(.+?)\s+(?:is|=|:)\s+(.+)",
            r"my\s+(.+?)\s+is\s+(.+)",
            r"yaad\s+rakhna\s+(?:ki\s+)?(.+?)\s+(?:hai|hoga)\s*$",
        ]

        for p in patterns:
            match = re.search(p, clean, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    k, v = groups[0].strip(), groups[1].strip()
                else:
                    k = "note"
                    v = groups[0].strip()

                # Clean key name
                safe_key = re.sub(r"[^\w\s-]", "", k).strip().replace(" ", "_").lower()[:40]
                if not safe_key:
                    safe_key = "user_preference"

                # Store into Personal Memory
                saved = await memory_store.save_memory(
                    category=MemoryCategory.PERSONAL,
                    memory_key=safe_key,
                    memory_value=v,
                    fact_type=FactType.PREFERENCE,
                    confidence=1.0,
                    source="user_explicit",
                )
                logger.info("Auto-extracted explicit memory: %s = %s", safe_key, v)
                return saved

        return None


# Global singleton instance
context_manager = ContextManager()
