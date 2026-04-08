"""
Sports AI — Tests for Agent Contracts
"""

import pytest
from datetime import datetime
from backend.agents.core.contracts import (
    AgentStatus,
    AgentContext,
    AgentOutcome,
    PipelineEvent,
    PipelineStage,
    STAGES,
    AGENT_TO_STAGE,
    STAGE_ORDER,
    GATE_STAGES,
)


class TestAgentStatus:
    def test_all_statuses_exist(self):
        assert AgentStatus.PENDING
        assert AgentStatus.RUNNING
        assert AgentStatus.COMPLETED
        assert AgentStatus.ERROR
        assert AgentStatus.SKIPPED
        assert AgentStatus.TIMEOUT

    def test_status_is_string_enum(self):
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.ERROR.value == "error"


class TestAgentContext:
    def test_creates_with_defaults(self, sample_context):
        assert sample_context.query == "analiza barcelona vs real madrid"
        assert sample_context.prediction_id == "test-pred-001"
        assert sample_context.stage == "init"
        assert sample_context.data == {}
        assert sample_context.timings == {}
        assert sample_context.errors == {}

    def test_get_set_operations(self, sample_context):
        sample_context.set("teams", ["Barcelona", "Real Madrid"])
        assert sample_context.get("teams") == ["Barcelona", "Real Madrid"]
        assert sample_context.get("nonexistent", "default") == "default"

    def test_has_error(self, sample_context):
        assert not sample_context.has_error("nlp")
        sample_context.errors["nlp"] = "Failed"
        assert sample_context.has_error("nlp")


class TestAgentOutcome:
    def test_creates_completed_outcome(self, completed_outcome):
        assert completed_outcome.agent_name == "nlp"
        assert completed_outcome.status == AgentStatus.COMPLETED
        assert completed_outcome.is_success() is True
        assert completed_outcome.is_critical_failure() is False

    def test_creates_failed_outcome(self, failed_outcome):
        assert failed_outcome.status == AgentStatus.ERROR
        assert failed_outcome.is_success() is False
        assert failed_outcome.is_critical_failure() is True

    def test_timestamp_default(self, completed_outcome):
        assert completed_outcome.timestamp is not None
        assert isinstance(completed_outcome.timestamp, datetime)


class TestPipelineEvent:
    def test_to_sse_format(self):
        event = PipelineEvent(
            event_type="agent_complete",
            data={"agent": "nlp", "status": "completed"},
        )
        sse = event.to_sse()
        assert "agent_complete" in sse
        assert "nlp" in sse
        assert "timestamp" in sse


class TestPipelineStages:
    def test_all_15_agents_mapped(self):
        assert len(AGENT_TO_STAGE) == 15

    def test_nlp_is_gate(self):
        assert "nlp" in GATE_STAGES

    def test_gate_stages_are_gate_agents(self):
        gate_stages = [s for s in STAGES if s.name in GATE_STAGES]
        for stage in gate_stages:
            assert len(stage.agents) == 1
            assert stage.agents[0] in GATE_STAGES

    def test_stage_order_length(self):
        assert len(STAGE_ORDER) == 9

    def test_stages_have_correct_order(self):
        assert STAGE_ORDER[0] == "parse"
        assert STAGE_ORDER[-1] == "synthesis"

    def test_fan_out_stages(self):
        fan_out = [s for s in STAGES if len(s.agents) > 1]
        assert fan_out[0].name == "data_fetch"
        assert set(fan_out[0].agents) == {"history", "lineup", "odds"}
        assert fan_out[1].name == "analysis"
        assert set(fan_out[1].agents) == {"sentiment", "elo", "poisson"}
        assert fan_out[2].name == "prediction"
        assert set(fan_out[2].agents) == {"ml", "monte_carlo"}
        assert fan_out[3].name == "decision"
        assert set(fan_out[3].agents) == {"market_edge", "risk"}

    def test_all_stages_have_unique_names(self):
        names = [s.name for s in STAGES]
        assert len(names) == len(set(names))
