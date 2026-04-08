"""
Sports AI — Tests for the DAG orchestrator
"""

import json

import pytest

from backend.agents.core.contracts import AgentContext, AgentOutcome, AgentStatus
from backend.agents.core.orchestrator import PipelineOrchestrator


@pytest.mark.asyncio
async def test_build_prediction_includes_fixture_id(monkeypatch):
    monkeypatch.setattr("backend.agents.core.orchestrator.discover_agents", lambda: {})

    orchestrator = PipelineOrchestrator()
    ctx = AgentContext(
        query="analiza barcelona vs real madrid",
        prediction_id="pred-001",
        data={
            "team_home": "Barcelona",
            "team_away": "Real Madrid",
            "league_name": "La Liga",
            "fixture_id": 1234,
            "fixture_resolution_status": "resolved",
            "fixture_resolution_confidence": 0.87,
            "fixture_resolution_confirmation_message": "ok",
            "fixture_resolution_alternatives": [],
            "fixture_resolution_warnings": [],
        },
        timings={"nlp": 12.5, "stage_parse": 15.0},
    )

    payload = orchestrator._build_prediction(
        "pred-001",
        ctx.query,
        ctx,
        [],
        99.9,
    )

    assert payload["fixture_resolution"]["fixture_id"] == 1234
    assert payload["fixture_id"] == 1234
    assert payload["total_execution_time_ms"] == 100.0
    assert "timings" in payload
    assert payload["timings"]["by_stage"]["parse"] == 15.0


@pytest.mark.asyncio
async def test_run_aborts_cleanly_on_critical_failure(monkeypatch):
    monkeypatch.setattr("backend.agents.core.orchestrator.discover_agents", lambda: {})

    orchestrator = PipelineOrchestrator()
    orchestrator.graph.get_execution_order = lambda: ["parse"]
    orchestrator.graph.get_stage_agents = lambda stage: ["nlp"]
    orchestrator.graph.is_critical_stage = lambda stage: True
    orchestrator._get_agent = lambda name: None

    async def fake_execute_stage(ctx, stage_name):
        return [
            (
                "nlp",
                AgentOutcome(
                    agent_name="NLPAgent",
                    agent_key="nlp",
                    status=AgentStatus.ERROR,
                    execution_time_ms=3.2,
                    error="boom",
                ),
            )
        ]

    orchestrator._execute_stage = fake_execute_stage  # type: ignore[assignment]

    events = []
    async for raw_event in orchestrator.run("analiza barcelona vs real madrid"):
        events.append(json.loads(raw_event))

    assert events[0]["event"] == "pipeline_start"
    assert any(evt["event"] == "error" for evt in events)
    assert events[-1]["event"] == "pipeline_complete"
    final = events[-1]["data"]
    assert final["fixture_resolution"]["status"] == "unknown"
    assert final["total_execution_time_ms"] >= 0

