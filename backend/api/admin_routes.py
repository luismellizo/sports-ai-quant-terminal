"""
Sports AI — Admin API Routes
Login, prediction listing, and result lookup for the admin dashboard.
"""

import hashlib
import hmac
import json
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import select, desc

from backend.config.database import async_session
from backend.config.settings import get_settings
from backend.models.prediction_record import PredictionRecord
from backend.services.api_football_client import get_api_football_client
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

admin_router = APIRouter(prefix="/api/admin")


def _generate_token(user: str) -> str:
    """Generate an expiring HMAC token for admin sessions."""
    expires_at = int(time.time()) + int(settings.admin_token_ttl_seconds)
    payload = f"{user}:{expires_at}:{settings.admin_secret_key}"
    signature = hmac.new(
        settings.admin_secret_key.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{user}.{expires_at}.{signature}"


def _generate_legacy_token(user: str) -> str:
    payload = f"{user}:{settings.admin_secret_key}"
    return hmac.new(
        settings.admin_secret_key.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()


def _verify_token(token: str) -> bool:
    """Verify the admin token."""
    if not token:
        return False

    # New format: user.expiry.signature
    parts = token.split(".")
    if len(parts) == 3:
        user, expires_at_raw, signature = parts
        try:
            expires_at = int(expires_at_raw)
        except ValueError:
            return False
        if expires_at < int(time.time()):
            return False

        payload = f"{user}:{expires_at}:{settings.admin_secret_key}"
        expected = hmac.new(
            settings.admin_secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    # Backward-compatible legacy format.
    expected_legacy = _generate_legacy_token(settings.admin_user)
    return hmac.compare_digest(token, expected_legacy)


def _require_admin(authorization: Optional[str] = Header(None)):
    """Dependency to check admin authorization."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    if not _verify_token(token):
        raise HTTPException(status_code=401, detail="Token inválido")


@admin_router.post("/login")
async def admin_login(body: dict):
    """Authenticate admin user."""
    user = body.get("user", "")
    password = body.get("password", "")

    if user != settings.admin_user or password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = _generate_token(user)
    return {
        "token": token,
        "user": user,
        "expires_in": settings.admin_token_ttl_seconds,
    }


@admin_router.get("/predictions")
async def list_predictions(authorization: Optional[str] = Header(None)):
    """List all stored predictions with summary data."""
    _require_admin(authorization)

    async with async_session() as session:
        stmt = select(PredictionRecord).order_by(desc(PredictionRecord.created_at))
        result = await session.execute(stmt)
        records = result.scalars().all()

    predictions = []
    for r in records:
        predictions.append({
            "id": r.id,
            "prediction_id": r.prediction_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "query": r.query,
            "home_team": r.home_team,
            "away_team": r.away_team,
            "league": r.league,
            "probabilities": r.probabilities,
            "best_bet": r.best_bet,
            "monte_carlo_summary": r.monte_carlo_summary,
            "executive_summary": r.executive_summary,
            "verdict": r.verdict,
            "total_execution_time_ms": r.total_execution_time_ms,
            "fixture_id": r.fixture_id,
            "result_data": r.result_data,
        })

    return {"predictions": predictions, "count": len(predictions)}


@admin_router.get("/predictions/{prediction_id}/result")
async def get_prediction_result(
    prediction_id: str,
    authorization: Optional[str] = Header(None),
):
    """
    Fetch the real match result for a prediction.
    Uses the fixture_id to query the API and returns score data.
    """
    _require_admin(authorization)

    async with async_session() as session:
        stmt = select(PredictionRecord).where(
            PredictionRecord.prediction_id == prediction_id
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Predicción no encontrada")

    # If we already have the result cached, return it
    if record.result_data:
        return {"prediction_id": prediction_id, "result": record.result_data}

    # Try to find the fixture_id from various sources
    fixture_id = record.fixture_id

    if not fixture_id:
        # Try to find fixture by team names using the API
        api = get_api_football_client()
        try:
            teams = await api.search_teams(record.home_team)
            if teams:
                home_team_id = teams[0].get("team", {}).get("id")
                if home_team_id:
                    fixtures = await api.get_fixtures(team_id=home_team_id, last=5)
                    for fixture in fixtures:
                        teams_data = fixture.get("teams", {})
                        away_name = (teams_data.get("away", {}).get("name") or "").lower()
                        if record.away_team.lower() in away_name or away_name in record.away_team.lower():
                            fixture_id = fixture.get("fixture", {}).get("id")
                            break
        except Exception as e:
            logger.warning(f"Error searching for fixture: {e}")

    if not fixture_id:
        return {
            "prediction_id": prediction_id,
            "result": None,
            "message": "No se encontró el fixture asociado. El partido puede no haberse jugado aún.",
        }

    # Fetch the fixture data
    api = get_api_football_client()
    fixture = await api.get_fixture(fixture_id)

    if not fixture:
        return {
            "prediction_id": prediction_id,
            "result": None,
            "message": "No se pudo obtener datos del fixture.",
        }

    # Extract result data
    fixture_info = fixture.get("fixture", {})
    goals = fixture.get("goals", {})
    teams_data = fixture.get("teams", {})
    score = fixture.get("score", {})

    result_data = {
        "fixture_id": fixture_id,
        "status": fixture_info.get("status", {}).get("long", "Unknown")
            if isinstance(fixture_info.get("status"), dict)
            else str(fixture_info.get("status", "Unknown")),
        "home_team": teams_data.get("home", {}).get("name", record.home_team),
        "away_team": teams_data.get("away", {}).get("name", record.away_team),
        "goals_home": goals.get("home"),
        "goals_away": goals.get("away"),
        "score": score,
        "date": fixture_info.get("date"),
    }

    # Persist the result
    async with async_session() as session:
        stmt = select(PredictionRecord).where(
            PredictionRecord.prediction_id == prediction_id
        )
        result = await session.execute(stmt)
        db_record = result.scalar_one_or_none()
        if db_record:
            db_record.result_data = result_data
            db_record.fixture_id = fixture_id
            await session.commit()

    return {"prediction_id": prediction_id, "result": result_data}
