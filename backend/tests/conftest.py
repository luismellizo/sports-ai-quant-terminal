"""
Sports AI — Test Configuration
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from backend.agents.core.contracts import AgentContext, AgentStatus


@pytest.fixture
def sample_context():
    return AgentContext(
        query="analiza barcelona vs real madrid",
        prediction_id="test-pred-001",
    )


@pytest.fixture
def completed_outcome():
    from backend.agents.core.contracts import AgentOutcome

    return AgentOutcome(
        agent_name="nlp",
        status=AgentStatus.COMPLETED,
        data={"teams": ["Barcelona", "Real Madrid"]},
        execution_time_ms=150.5,
    )


@pytest.fixture
def failed_outcome():
    from backend.agents.core.contracts import AgentOutcome

    return AgentOutcome(
        agent_name="nlp",
        status=AgentStatus.ERROR,
        data={},
        execution_time_ms=50.0,
        error="Failed to parse query",
    )
