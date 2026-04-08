"""
Sports AI — Tests for Agent Registry
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext, AgentOutcome, AgentStatus
from backend.agents.registry import register, get, get_agent, all_agents


class DummyAgent(BaseAgent):
    agent_name = "dummy"
    description = "A dummy agent for testing"

    async def execute(self, ctx: AgentContext) -> AgentOutcome:
        return AgentOutcome(
            agent_name=self.agent_name,
            status=AgentStatus.COMPLETED,
            data={"result": "ok"},
            execution_time_ms=10.0,
        )


class TestRegistry:
    def test_register_and_get(self):
        register("dummy", DummyAgent)
        assert get("dummy") == DummyAgent

    def test_get_unknown_returns_none(self):
        assert get("nonexistent") is None

    def test_get_agent_returns_instance(self):
        register("dummy", DummyAgent)
        agent = get_agent("dummy")
        assert agent is not None
        assert isinstance(agent, DummyAgent)

    def test_get_agent_unknown_returns_none(self):
        assert get_agent("nonexistent") is None

    def test_all_agents(self):
        agents = all_agents()
        assert isinstance(agents, dict)
        assert "dummy" in agents
