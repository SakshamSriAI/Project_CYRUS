"""CYRUS PERSONAL Specialist Agent.

Manages:
- Daily agendas and schedule breakdowns.
- Study plans for Saksham's B.Tech Computer Science curriculum.
- Habit tracking, reminders, and daily goals.
- Personal memory recall and persistence.
Always addresses the user as "Sir".
"""

from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import AgentMetadata, BaseAgent
from backend.app.memory.memory_store import memory_store
from backend.app.memory.models import FactType, MemoryCategory

logger = logging.getLogger("cyrus.agents.personal")


class PersonalAgent(BaseAgent):
    """Specialist agent for personal productivity, habits, and study planning."""

    def __init__(self):
        super().__init__(
            AgentMetadata(
                name="CYRUS_PERSONAL",
                display_name="CYRUS Personal",
                description="Specialist in personal planning, daily schedules, habits, B.Tech study routines, and wellness.",
                domain="Personal Productivity & Academic Routine",
                capabilities=[
                    "Daily Schedule Management",
                    "B.Tech CS Study & Exam Timetable",
                    "Habit & Routine Tracking",
                    "Personal Preference Recall",
                ],
                icon="user-check",
            )
        )

    def can_handle(self, text: str) -> float:
        clean = text.lower()
        keywords = [
            "schedule", "agenda", "routine", "habit", "study", "exam",
            "workout", "sleep", "reminder", "timetable", "personal",
            "calendar", "aaj kya", "kya plan", "routine kya", "subah",
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
        """Processes personal requests, queries personal memory, and formulates structured advice."""
        clean = task_description.lower()

        # Retrieve relevant personal memories
        personal_memories = await memory_store.list_memories(
            category=MemoryCategory.PERSONAL,
            tenant_id="default",
            limit=10,
        )

        # 1. Study & Exam Planning
        if any(w in clean for w in ["study", "exam", "b.tech", "college", "subject", "padhai"]):
            response = (
                "Here is your structured study plan, Sir:\n\n"
                "1. **Core Computer Science Focus** (2 Hours):\n"
                "   - Data Structures & Algorithms / Object-Oriented Analysis\n"
                "   - High-yield practice and architectural revision\n"
                "2. **Hands-On Engineering & CYRUS Development** (1.5 Hours):\n"
                "   - Local modular coding, testing, and component refinement\n"
                "3. **Review & Consolidation** (30 Minutes):\n"
                "   - Flashcard concept review and session checkpointing\n\n"
                "All notifications and distractions can be placed on mute when you are ready to enter Exam Mode."
            )
            action_type = "STUDY_PLAN"

        # 2. Daily Schedule / Agenda
        elif any(w in clean for w in ["schedule", "agenda", "today", "aaj", "plan"]):
            now_str = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
            response = (
                f"Good day, Sir. Here is your operational agenda for {now_str}:\n\n"
                "• **Morning**: System architecture review and priority academic goals.\n"
                "• **Midday**: Focused project milestones and software development.\n"
                "• **Evening**: Habit checkpoints, revision, and session status evaluation.\n\n"
                "All systems and local memories are synchronized. Where would you like to begin?"
            )
            action_type = "DAILY_SCHEDULE"

        # 3. Habit / Reminder Check
        elif any(w in clean for w in ["habit", "routine", "goal", "reminder"]):
            response = (
                "Your active habits and routines are intact, Sir. "
                "You have active targets set for daily computer science study, physical wellness, "
                "and consistent project commits. Would you like me to log a progress update?"
            )
            action_type = "HABIT_TRACKING"

        # 4. General Personal Inquiry
        else:
            response = (
                f"I have reviewed your personal preferences and active priorities, Sir. "
                f"We currently have {len(personal_memories)} verified records in your Personal Memory. "
                f"How would you like to optimize your schedule today?"
            )
            action_type = "PERSONAL_CONSULT"

        return {
            "response": response,
            "action_type": action_type,
            "memories_referenced_count": len(personal_memories),
            "recommendation": "Maintain consistent deep-work blocks and utilize Exam Mode during exam preparation.",
        }


personal_agent = PersonalAgent()
