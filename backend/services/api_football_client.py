"""
Sports AI — API-Football Client
Async HTTP client for API-Football v3 with caching and rate limiting.
"""

import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from backend.config.settings import get_settings
from backend.utils.cache import cached
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

API_BASE = settings.api_football_base_url
HEADERS = {
    "x-apisports-key": settings.api_football_key,
}


class APIFootballClient:
    """Async client for API-Football v3."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=API_BASE,
            headers=HEADERS,
            timeout=30.0,
        )

    async def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to API-Football."""
        try:
            response = await self.client.get(endpoint, params=params or {})
            response.raise_for_status()
            data = response.json()
            if data.get("errors"):
                logger.warning(f"API-Football errors: {data['errors']}")
            return data
        except httpx.HTTPError as e:
            logger.error(f"API-Football request failed: {e}")
            return {"response": []}

    # ── Team Search ───────────────────────────────────────────────

    @cached("team_search", ttl=86400)
    async def search_teams(self, name: str) -> List[Dict]:
        """Search teams by name."""
        data = await self._request("/teams", {"search": name})
        return data.get("response", [])

    @cached("team_info", ttl=86400)
    async def get_team(self, team_id: int) -> Optional[Dict]:
        """Get team info by ID."""
        data = await self._request("/teams", {"id": team_id})
        results = data.get("response", [])
        return results[0] if results else None

    # ── Fixtures ──────────────────────────────────────────────────

    @cached("fixtures", ttl=1800)
    async def get_fixtures(
        self,
        team_id: Optional[int] = None,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        date_str: Optional[str] = None,
        last: Optional[int] = None,
        next_n: Optional[int] = None,
    ) -> List[Dict]:
        """Get fixtures with various filters."""
        params = {}
        if team_id:
            params["team"] = team_id
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if date_str:
            params["date"] = date_str
        if last:
            params["last"] = last
        if next_n:
            params["next"] = next_n

        data = await self._request("/fixtures", params)
        return data.get("response", [])

    @cached("fixture_detail", ttl=1800)
    async def get_fixture(self, fixture_id: int) -> Optional[Dict]:
        """Get single fixture details."""
        data = await self._request("/fixtures", {"id": fixture_id})
        results = data.get("response", [])
        return results[0] if results else None

    # ── Head to Head ──────────────────────────────────────────────

    @cached("h2h", ttl=3600)
    async def get_h2h(self, team1_id: int, team2_id: int, last: int = 20) -> List[Dict]:
        """Get head-to-head fixtures between two teams."""
        h2h_str = f"{team1_id}-{team2_id}"
        data = await self._request("/fixtures/headtohead", {"h2h": h2h_str, "last": last})
        return data.get("response", [])

    # ── Team Statistics ───────────────────────────────────────────

    @cached("team_stats", ttl=3600)
    async def get_team_statistics(
        self, team_id: int, league_id: int, season: int
    ) -> Optional[Dict]:
        """Get team statistics for a league/season."""
        data = await self._request(
            "/teams/statistics",
            {"team": team_id, "league": league_id, "season": season},
        )
        return data.get("response")

    # ── Lineups ───────────────────────────────────────────────────

    @cached("lineups", ttl=1800)
    async def get_lineups(self, fixture_id: int) -> List[Dict]:
        """Get lineups for a fixture."""
        data = await self._request("/fixtures/lineups", {"fixture": fixture_id})
        return data.get("response", [])

    # ── Injuries ──────────────────────────────────────────────────

    @cached("injuries", ttl=1800)
    async def get_injuries(
        self, fixture_id: Optional[int] = None, team_id: Optional[int] = None
    ) -> List[Dict]:
        """Get injuries for a fixture or team."""
        params = {}
        if fixture_id:
            params["fixture"] = fixture_id
        if team_id:
            params["team"] = team_id
        data = await self._request("/injuries", params)
        return data.get("response", [])

    # ── Odds ──────────────────────────────────────────────────────

    @cached("odds", ttl=1800)
    async def get_odds(
        self,
        fixture_id: Optional[int] = None,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        bookmaker_id: Optional[int] = None,
    ) -> List[Dict]:
        """Get betting odds."""
        params = {}
        if fixture_id:
            params["fixture"] = fixture_id
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if bookmaker_id:
            params["bookmaker"] = bookmaker_id
        data = await self._request("/odds", params)
        return data.get("response", [])

    # ── Standings ─────────────────────────────────────────────────

    @cached("standings", ttl=3600)
    async def get_standings(self, league_id: int, season: int) -> List[Dict]:
        """Get league standings."""
        data = await self._request(
            "/standings", {"league": league_id, "season": season}
        )
        return data.get("response", [])

    # ── Predictions ─────────────────────────────────────────────

    @cached("api_predictions", ttl=3600)
    async def get_predictions(self, fixture_id: int) -> Optional[Dict]:
        """Get API-Football's own predictions."""
        data = await self._request("/predictions", {"fixture": fixture_id})
        results = data.get("response", [])
        return results[0] if results else None

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Singleton instance
_client: Optional[APIFootballClient] = None


def get_api_football_client() -> APIFootballClient:
    """Get or create API-Football client singleton."""
    global _client
    if _client is None:
        _client = APIFootballClient()
    return _client
