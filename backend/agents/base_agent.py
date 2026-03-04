"""
Sports AI — Base Agent
Abstract base class for all analysis agents in the pipeline.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any
from backend.models.prediction import AgentResult, AgentStatus
from backend.utils.logger import get_logger


class BaseAgent(ABC):
    """
    Base class for all pipeline agents.

    Each agent:
    1. Receives a shared context dict
    2. Executes its analysis
    3. Returns an AgentResult with data
    4. Adds its results to the shared context
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.name = self.__class__.__name__

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        """Execute agent with timing and error handling."""
        self.logger.info(f"▶ Starting {self.name}")
        start = time.time()

        try:
            data = await self.execute(context)
            elapsed = (time.time() - start) * 1000

            result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                execution_time_ms=round(elapsed, 2),
                data=data,
            )
            self.logger.info(f"✓ {self.name} completed in {elapsed:.0f}ms")
            return result

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            self.logger.error(f"✗ {self.name} failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.ERROR,
                execution_time_ms=round(elapsed, 2),
                error=str(e),
            )

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic.

        Args:
            context: Shared pipeline context with data from previous agents

        Returns:
            Dict of results to merge into context
        """
        pass
