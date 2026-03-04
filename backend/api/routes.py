"""
Sports AI — API Routes
FastAPI routes for the sports prediction system.
"""

import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.services.api_football_client import get_api_football_client
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api")


@router.post("/analyze")
async def analyze_match(body: dict):
    """
    Analyze a match with the full agent pipeline.

    Streams SSE events as each agent completes.

    Request body:
        {"query": "analyze barcelona vs madrid"}
    """
    query = body.get("query", "")
    if not query:
        return {"error": "Query is required"}

    orchestrator = OrchestratorAgent()

    async def event_stream():
        async for event in orchestrator.run_pipeline(query):
            yield f"data: {event}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/analyze/sync")
async def analyze_match_sync(body: dict):
    """
    Analyze a match synchronously (non-streaming).
    Returns the complete result as JSON.
    """
    query = body.get("query", "")
    if not query:
        return {"error": "Query is required"}

    orchestrator = OrchestratorAgent()
    result = None

    async for event in orchestrator.run_pipeline(query):
        parsed = json.loads(event)
        if parsed.get("event") == "pipeline_complete":
            result = parsed.get("data")

    return result or {"error": "Pipeline failed"}


@router.get("/teams")
async def search_teams(q: str = Query(..., min_length=2)):
    """Search for teams by name."""
    api = get_api_football_client()
    results = await api.search_teams(q)

    teams = []
    for r in results[:20]:
        team = r.get("team", {})
        venue = r.get("venue", {})
        teams.append({
            "id": team.get("id"),
            "name": team.get("name"),
            "code": team.get("code"),
            "country": team.get("country"),
            "logo": team.get("logo"),
            "venue": venue.get("name"),
        })

    return {"teams": teams, "count": len(teams)}


@router.get("/match/{fixture_id}")
async def get_match(fixture_id: int):
    """Get match details by fixture ID."""
    api = get_api_football_client()
    fixture = await api.get_fixture(fixture_id)

    if not fixture:
        return {"error": "Match not found"}

    return {
        "fixture": fixture.get("fixture"),
        "league": fixture.get("league"),
        "teams": fixture.get("teams"),
        "goals": fixture.get("goals"),
        "score": fixture.get("score"),
    }


@router.get("/prediction/{prediction_id}")
async def get_prediction(prediction_id: str):
    """
    Get a stored prediction by ID.
    TODO: Implement DB storage for predictions.
    """
    return {
        "message": "Prediction storage coming soon",
        "prediction_id": prediction_id,
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "sports-ai"}
