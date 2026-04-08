"""
Sports AI — API Routes
FastAPI routes for the sports prediction system.
"""

import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from backend.agents.core.orchestrator import PipelineOrchestrator
from backend.agents.registry import discover_agents, all_agents
from backend.services.api_football_client import get_api_football_client
from backend.config.database import async_session
from backend.models.prediction_record import PredictionRecord
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api")


async def _save_prediction(prediction_data: dict):
    """Persist a completed prediction to the database."""
    try:
        record = PredictionRecord(
            prediction_id=prediction_data.get("id", ""),
            query=prediction_data.get("query", ""),
            home_team=prediction_data.get("home_team", ""),
            away_team=prediction_data.get("away_team", ""),
            league=prediction_data.get("league"),
            probabilities=prediction_data.get("probabilities"),
            best_bet=prediction_data.get("best_bet"),
            monte_carlo_summary={
                "simulations": prediction_data.get("monte_carlo", {}).get("simulations"),
                "home_win_pct": prediction_data.get("monte_carlo", {}).get("home_win_pct"),
                "draw_pct": prediction_data.get("monte_carlo", {}).get("draw_pct"),
                "away_win_pct": prediction_data.get("monte_carlo", {}).get("away_win_pct"),
                "most_likely_score": prediction_data.get("monte_carlo", {}).get("most_likely_score"),
            },
            executive_summary=prediction_data.get("executive_summary", ""),
            verdict=prediction_data.get("verdict", ""),
            total_execution_time_ms=prediction_data.get("total_execution_time_ms", 0),
            fixture_id=(
                prediction_data.get("fixture_resolution", {}).get("fixture_id")
                if isinstance(prediction_data.get("fixture_resolution"), dict)
                else prediction_data.get("fixture_id")
            ),
        )

        async with async_session() as session:
            session.add(record)
            await session.commit()
            logger.info(f"✓ Prediction {record.prediction_id} saved to database")
    except Exception as e:
        logger.error(f"✗ Failed to save prediction: {e}")


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

    orchestrator = PipelineOrchestrator()

    async def event_stream():
        async for event in orchestrator.run_pipeline(query):
            # Intercept pipeline_complete to save prediction
            try:
                parsed = json.loads(event)
                if parsed.get("event") == "pipeline_complete":
                    await _save_prediction(parsed.get("data", {}))
            except Exception:
                pass
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

    orchestrator = PipelineOrchestrator()
    result = None

    async for event in orchestrator.run_pipeline(query):
        parsed = json.loads(event)
        if parsed.get("event") == "pipeline_complete":
            result = parsed.get("data")

    if result:
        await _save_prediction(result)

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
    """Get a stored prediction by ID."""
    from sqlalchemy import select

    async with async_session() as session:
        stmt = select(PredictionRecord).where(
            PredictionRecord.prediction_id == prediction_id
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

    if not record:
        return {"error": "Prediction not found", "prediction_id": prediction_id}

    return {
        "prediction_id": record.prediction_id,
        "query": record.query,
        "home_team": record.home_team,
        "away_team": record.away_team,
        "league": record.league,
        "probabilities": record.probabilities,
        "best_bet": record.best_bet,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "sports-ai"}


@router.get("/health/live")
async def health_live():
    """Liveness check for orchestration platforms."""
    return {"status": "alive", "service": "sports-ai"}


@router.get("/health/ready")
async def health_ready():
    """Readiness check that verifies the registry and database are reachable."""
    discover_agents()
    agents_loaded = len(all_agents()) > 0
    db_ok = False
    redis_ok = False
    try:
        from sqlalchemy import text

        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception as exc:
        logger.warning(f"Readiness DB check failed: {exc}")

    try:
        from backend.utils.cache import get_redis

        redis_client = await get_redis()
        redis_ok = bool(await redis_client.ping())
    except Exception as exc:
        logger.warning(f"Readiness Redis check failed: {exc}")

    status = "ready" if agents_loaded and db_ok and redis_ok else "degraded"
    return {
        "status": status,
        "service": "sports-ai",
        "checks": {
            "agents_loaded": agents_loaded,
            "database": db_ok,
            "redis": redis_ok,
        },
    }
