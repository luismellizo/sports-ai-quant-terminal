"""
Sports AI — Tests for Pipeline Graph
"""

import pytest
from backend.agents.core.pipeline_graph import PipelineGraph
from backend.agents.core.contracts import STAGES


class TestPipelineGraph:
    def setup_method(self):
        self.graph = PipelineGraph()

    def test_get_stage(self):
        stage = self.graph.get_stage("parse")
        assert stage.name == "parse"
        assert stage.agents == ["nlp"]

    def test_get_stage_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown stage"):
            self.graph.get_stage("nonexistent")

    def test_get_dependencies(self):
        deps = self.graph.get_dependencies("data_fetch")
        assert deps == ["context"]

    def test_get_stage_agents(self):
        agents = self.graph.get_stage_agents("analysis")
        assert set(agents) == {"sentiment", "elo", "poisson"}

    def test_is_critical_stage(self):
        assert self.graph.is_critical_stage("parse") is True
        assert self.graph.is_critical_stage("resolve") is True
        assert self.graph.is_critical_stage("context") is True
        assert self.graph.is_critical_stage("data_fetch") is False

    def test_validate_graph_valid(self):
        assert self.graph.validate_graph() is True

    def test_get_execution_order(self):
        order = self.graph.get_execution_order()
        assert order == [
            "parse",
            "resolve",
            "context",
            "data_fetch",
            "analysis",
            "features",
            "prediction",
            "decision",
            "synthesis",
        ]

    def test_get_fan_out_stages(self):
        fan_out = self.graph.get_fan_out_stages()
        assert "data_fetch" in fan_out
        assert "analysis" in fan_out
        assert "prediction" in fan_out
        assert "decision" in fan_out

    def test_should_parallelize(self):
        assert self.graph.should_parallelize("parse") is False
        assert self.graph.should_parallelize("data_fetch") is True
        assert self.graph.should_parallelize("analysis") is True

    def test_get_parallel_agents(self):
        agents = self.graph.get_parallel_agents("data_fetch")
        assert set(agents) == {"history", "lineup", "odds"}

    def test_graph_has_9_stages(self):
        assert len(self.graph.stages) == 9
