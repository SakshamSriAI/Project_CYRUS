"""CYRUS Specialist Agent Registry & Router.

Coordinates:
- Registration and lifecycle management of all 5 Specialist Agents.
- Semantic and keyword-based task delegation.
- Cross-agent telemetry and state inspection.
- SQLite task persistence in `agent_tasks`.
"""

import logging
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.business_agent import business_agent
from backend.app.agents.dev_agent import dev_agent
from backend.app.agents.executive_agent import executive_agent
from backend.app.agents.personal_agent import personal_agent
from backend.app.agents.research_agent import research_agent
from backend.app.database import execute_query

logger = logging.getLogger("cyrus.agents.registry")


class AgentRegistry:
    """Central registry and dispatch coordinator for CYRUS specialist agents."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        """Registers the 5 core specialist agents."""
        self.register(personal_agent)
        self.register(business_agent)
        self.register(dev_agent)
        self.register(research_agent)
        self.register(executive_agent)

    def register(self, agent: BaseAgent):
        """Adds a specialist agent to the active registry."""
        self._agents[agent.name] = agent
        logger.info("Registered specialist agent: %s (%s)", agent.name, agent.display_name)

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Retrieves an agent by exact name (case-insensitive)."""
        key = agent_name.upper().strip()
        return self._agents.get(key)

    def list_agents(self) -> List[Dict[str, Any]]:
        """Returns structured metadata for all registered agents."""
        return [
            {
                "name": agent.name,
                "display_name": agent.display_name,
                "description": agent.metadata.description,
                "domain": agent.metadata.domain,
                "capabilities": agent.metadata.capabilities,
                "icon": agent.metadata.icon,
                "status": agent.metadata.status,
            }
            for agent in self._agents.values()
        ]

    def route_intent(self, text: str, threshold: float = 0.50) -> Optional[BaseAgent]:
        """Evaluates user intent and returns the highest-confidence specialist agent."""
        best_agent: Optional[BaseAgent] = None
        best_score = 0.0

        for agent in self._agents.values():
            score = agent.can_handle(text)
            if score > best_score:
                best_score = score
                best_agent = agent

        if best_agent and best_score >= threshold:
            logger.info("Routed prompt to %s (confidence: %.2f)", best_agent.name, best_score)
            return best_agent

        return None

    async def dispatch_task(
        self,
        agent_name: str,
        task_description: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Dispatches a task directly to a designated specialist agent."""
        agent = self.get_agent(agent_name)
        if not agent:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found in registry.",
                "response": f"I could not locate specialist agent '{agent_name}', Sir.",
            }

        return await agent.execute(task_description, session_id, context)

    async def list_recent_tasks(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieves recent executed tasks across all specialist agents from SQLite."""
        query = """
        SELECT id, session_id, agent_name, task_description, status, checkpoint_state_json, created_at, updated_at
        FROM agent_tasks
        ORDER BY created_at DESC
        LIMIT ?;
        """
        rows = await execute_query(query, (limit,))
        return rows


agent_registry = AgentRegistry()
