"""
Sports AI — Statpal Client Adapter
Compatibility layer that preserves the old API-Football client interface.
"""

from __future__ import annotations

import asyncio
import re
import unicodedata
from datetime import date, datetime
from difflib import SequenceMatcher
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

import httpx

from backend.config.settings import get_settings
from backend.utils.cache import cached
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

API_BASE = settings.statpal_base_url.rstrip("/")
SPORT_NAME = (settings.statpal_sport or "soccer").strip("/")


class APIFootballClient:
    """
    Async client using Statpal Soccer V2 while exposing API-Football-like methods.
    """

    DAILY_WINDOW_MIN_OFFSET = -7
    DAILY_WINDOW_MAX_OFFSET = 7
    PRIORITY_LEAGUES = (
        ("france", "ligue 1"),
        ("england", "premier league"),
        ("spain", "laliga"),
        ("spain", "la liga"),
        ("italy", "serie a"),
        ("germany", "bundesliga"),
        ("netherlands", "eredivisie"),
        ("portugal", "primeira liga"),
        ("turkey", "super lig"),
        ("scotland", "premiership"),
        ("belgium", "pro league"),
        ("brazil", "serie a"),
        ("argentina", "liga profesional"),
        ("colombia", "primera a"),
        ("colombia", "primera division"),
        ("mexico", "liga mx"),
        ("usa", "major league soccer"),
        ("usa", "mls"),
        ("world", "uefa champions league"),
        ("world", "uefa europa league"),
        ("world", "uefa conference league"),
    )
    TEAM_ALIAS_GROUPS = (
        {"psg", "paris saint germain", "paris sg", "paris saint germain fc"},
        {"monaco", "as monaco"},
        {"inter", "inter milan", "internazionale"},
        {"manchester united", "man united", "man utd"},
        {"manchester city", "man city"},
        {"tottenham", "tottenham hotspur", "spurs"},
        {"atletico madrid", "atletico de madrid", "atleti"},
        {"real madrid", "real madrid cf"},
        {"barcelona", "fc barcelona", "barca"},
        {"juventus", "juventus turin"},
        {"bayern munich", "bayern", "fc bayern"},
        {"borussia dortmund", "dortmund", "bvb"},
        {"newcastle united", "newcastle"},
    )
    TOKEN_STOPWORDS = {"fc", "cf", "sc", "ac", "as", "club", "de", "the", "cd", "sd"}
    TOKEN_ALIASES = {
        "deportivo": ("dep",),
        "dep": ("deportivo",),
        "atletico": ("atl",),
        "atl": ("atletico",),
        "independiente": ("ind",),
        "ind": ("independiente",),
    }

    def __init__(self):
        base_url = API_BASE if API_BASE.endswith("/") else f"{API_BASE}/"
        self.access_key = settings.statpal_access_key or settings.api_football_key
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self._fixture_index: Dict[int, Dict[str, Any]] = {}
        self._team_profile_cache: Dict[int, Dict[str, Any]] = {}

        if not self.access_key:
            logger.warning("No Statpal access key configured. API responses will fail.")

    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make authenticated request to Statpal."""
        request_params = dict(params or {})
        if self.access_key:
            request_params["access_key"] = self.access_key

        clean_endpoint = endpoint.lstrip("/")
        try:
            response = await self.client.get(clean_endpoint, params=request_params)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                logger.warning(f"Statpal error on {clean_endpoint}: {data.get('error')}")
            return data if isinstance(data, dict) else {}
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            logger.error(f"Statpal request failed for {clean_endpoint} (status={status_code})")
            return {}
        except httpx.HTTPError as exc:
            logger.error(
                "Statpal request failed for %s (%s)",
                clean_endpoint,
                exc.__class__.__name__,
            )
            return {}

    # ── Team Search ───────────────────────────────────────────────

    @cached("team_search_v3", ttl=86400)
    async def search_teams(self, name: str) -> List[Dict]:
        """Search teams by name using recent Statpal schedules."""
        query = self._normalize_lookup_text(name)
        if not query:
            return []

        fixtures = await self._load_daily_window_fixtures()
        candidates: Dict[int, Dict[str, Any]] = {}

        for fixture in fixtures:
            league = fixture.get("league", {})
            for side in ("home", "away"):
                team = fixture.get("teams", {}).get(side, {})
                team_id = self._to_int(team.get("id"))
                team_name = self._clean_text(team.get("name"))
                if not team_id or not team_name:
                    continue

                entry = candidates.get(team_id)
                if not entry:
                    entry = {
                        "team": {
                            "id": team_id,
                            "name": team_name,
                            "code": self._derive_code(team_name),
                            "country": self._clean_text(league.get("country")).title() or None,
                            "logo": None,
                        },
                        "venue": {"name": None},
                        "leagues": {"league_id": []},
                    }
                    candidates[team_id] = entry

                league_id = self._to_int(league.get("id"))
                if league_id and str(league_id) not in entry["leagues"]["league_id"]:
                    entry["leagues"]["league_id"].append(str(league_id))

        # Add curated references from major leagues to avoid mismatches
        # when teams are not present in the ±7 daily window.
        for team_entry in await self._get_reference_team_candidates():
            team_id = self._to_int((team_entry.get("team") or {}).get("id"))
            if not team_id:
                continue
            existing = candidates.get(team_id)
            if not existing:
                candidates[team_id] = team_entry
                continue
            existing_leagues = (existing.get("leagues") or {}).get("league_id", [])
            incoming_leagues = (team_entry.get("leagues") or {}).get("league_id", [])
            for league_id in self._ensure_list(incoming_leagues):
                if league_id and league_id not in existing_leagues:
                    existing_leagues.append(league_id)

        # Include richer data for teams already fetched directly.
        for team_id, profile in self._team_profile_cache.items():
            candidates[team_id] = profile

        scored: List[tuple[float, Dict[str, Any]]] = []
        for candidate in candidates.values():
            score = self._team_match_score(query, candidate)
            if score >= 35.0:
                scored.append((score, candidate))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in scored[:30]]

    @cached("team_info", ttl=86400)
    async def get_team(self, team_id: int) -> Optional[Dict]:
        """Get team info by ID from Statpal."""
        data = await self._request(f"{SPORT_NAME}/teams/{team_id}")
        raw_team = data.get("team")
        if not isinstance(raw_team, dict):
            return None

        mapped = {
            "team": {
                "id": self._to_int(raw_team.get("id"), team_id),
                "name": self._clean_text(raw_team.get("name"), f"Team {team_id}"),
                "code": self._derive_code(raw_team.get("name")),
                "country": self._clean_text(raw_team.get("country")) or None,
                "logo": None,
            },
            "venue": {
                "name": self._clean_text(raw_team.get("venue_name")) or None,
                "city": self._clean_text(raw_team.get("venue_city")) or None,
                "capacity": self._to_int(raw_team.get("venue_capacity")),
                "surface": self._clean_text(raw_team.get("venue_surface")) or None,
            },
            "coach": raw_team.get("coach") or {},
            "squad": raw_team.get("squad") or {},
            "leagues": raw_team.get("leagues") or {},
            "league_stats": raw_team.get("league_stats") or {},
            "transfers": raw_team.get("transfers") or {},
            "trophies": raw_team.get("trophies") or {},
        }

        team_id_mapped = mapped["team"]["id"]
        if team_id_mapped:
            self._team_profile_cache[team_id_mapped] = mapped
        return mapped

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
        """Get fixtures with filters, normalized to API-Football-like shape."""
        fixtures: List[Dict[str, Any]] = []
        season_param = self._normalize_season_param(season)

        if league_id:
            fixtures.extend(await self._get_league_fixtures(league_id, season_param))
        elif team_id:
            league_ids = await self._infer_team_leagues(team_id)
            for team_league_id in league_ids[:10]:
                fixtures.extend(await self._get_league_fixtures(team_league_id, season_param))
            
            # Siempre cargar los diarios para asegurar partidos de HOY (en caso no viniera en sus ligas top)
            daily_fixtures = await self._load_daily_window_fixtures()
            for df in daily_fixtures:
                if team_id in (
                    df.get("teams", {}).get("home", {}).get("id"),
                    df.get("teams", {}).get("away", {}).get("id")
                ) and df not in fixtures:
                    fixtures.append(df)
        elif date_str:
            fixtures.extend(await self._get_daily_by_date(date_str))
        else:
            fixtures.extend(await self._get_daily_fixtures(0))

        fixtures = self._dedupe_fixtures(fixtures)

        # Apply filters
        if team_id:
            fixtures = [
                fixture
                for fixture in fixtures
                if team_id in (
                    fixture.get("teams", {}).get("home", {}).get("id"),
                    fixture.get("teams", {}).get("away", {}).get("id"),
                )
            ]
        if league_id:
            fixtures = [
                fixture
                for fixture in fixtures
                if fixture.get("league", {}).get("id") == league_id
            ]
        if season:
            fixtures = [
                fixture
                for fixture in fixtures
                if fixture.get("league", {}).get("season") == season
            ]
        if date_str:
            target_date = self._normalize_date_filter(date_str)
            fixtures = [
                fixture
                for fixture in fixtures
                if self._normalize_date_filter(
                    str(fixture.get("fixture", {}).get("date", ""))
                )
                == target_date
            ]

        if last:
            completed = [f for f in fixtures if self._is_finished_fixture(f)]
            completed.sort(key=self._fixture_sort_key, reverse=True)
            return completed[:last]

        if next_n:
            upcoming = [f for f in fixtures if not self._is_finished_fixture(f)]
            upcoming.sort(key=self._fixture_sort_key)
            return upcoming[:next_n]

        fixtures.sort(key=self._fixture_sort_key, reverse=True)
        return fixtures

    @cached("fixture_detail", ttl=1800)
    async def get_fixture(self, fixture_id: int) -> Optional[Dict]:
        """Get single fixture details."""
        if fixture_id in self._fixture_index:
            return self._fixture_index[fixture_id]

        for fixture in await self._load_daily_window_fixtures():
            if fixture.get("fixture", {}).get("id") == fixture_id:
                return fixture

        # Fallback: scan leagues already discovered via team lookups.
        league_ids: List[int] = []
        for team in self._team_profile_cache.values():
            leagues = team.get("leagues", {})
            raw_ids = leagues.get("league_id") if isinstance(leagues, dict) else []
            for league_id in self._ensure_list(raw_ids):
                league_id_int = self._to_int(league_id)
                if league_id_int and league_id_int not in league_ids:
                    league_ids.append(league_id_int)

        for league_id in league_ids[:20]:
            fixtures = await self._get_league_fixtures(league_id, season=None)
            for fixture in fixtures:
                if fixture.get("fixture", {}).get("id") == fixture_id:
                    return fixture

        return None

    # ── Head to Head ──────────────────────────────────────────────

    @cached("h2h", ttl=3600)
    async def get_h2h(self, team1_id: int, team2_id: int, last: int = 20) -> List[Dict]:
        """Get head-to-head fixtures between two teams."""
        data = await self._request(
            f"{SPORT_NAME}/head-to-head",
            {"team1_id": team1_id, "team2_id": team2_id},
        )
        h2h_payload = data.get("head-to-head", {})
        meetings = self._ensure_list(
            (h2h_payload.get("recent_meetings") or {}).get("match")
        )

        fixtures = [self._normalize_h2h_match(match) for match in meetings]
        fixtures = [fixture for fixture in fixtures if fixture]
        fixtures.sort(key=self._fixture_sort_key, reverse=True)
        return fixtures[:last]

    @cached("h2h_stats", ttl=3600)
    async def get_h2h_stats(self, team1_id: int, team2_id: int, last: int = 20) -> Dict[str, Any]:
        """Get rich head-to-head stats and fixtures between two teams."""
        data = await self._request(
            f"{SPORT_NAME}/head-to-head",
            {"team1_id": team1_id, "team2_id": team2_id},
        )
        h2h_payload = data.get("head-to-head", {})
        meetings = self._ensure_list(
            (h2h_payload.get("recent_meetings") or {}).get("match")
        )

        fixtures = [self._normalize_h2h_match(match) for match in meetings]
        fixtures = [fixture for fixture in fixtures if fixture]
        fixtures.sort(key=self._fixture_sort_key, reverse=True)
        
        return {
            "fixtures": fixtures[:last],
            "overall_record": h2h_payload.get("overall_record", {}),
            "biggest_victory": h2h_payload.get("biggest_victory", {}),
            "biggest_defeat": h2h_payload.get("biggest_defeat", {}),
            "goals": h2h_payload.get("goals", {}),
            "last5_home": h2h_payload.get("last5_home", {}),
            "last5_away": h2h_payload.get("last5_away", {}),
            "leagues": h2h_payload.get("leagues", {})
        }

    # ── Team Statistics ───────────────────────────────────────────

    @cached("team_stats", ttl=3600)
    async def get_team_statistics(
        self, team_id: int, league_id: int, season: int
    ) -> Optional[Dict]:
        """Get team statistics for a league/season."""
        team = await self.get_team(team_id)
        team_name = self._clean_text(
            (team or {}).get("team", {}).get("name"),
            f"Team {team_id}",
        )

        if team:
            stats = self._map_team_stats_from_payload(
                team,
                team_id=team_id,
                team_name=team_name,
                league_id=league_id,
                season=season,
            )
            if stats:
                return stats

        fixtures = await self.get_fixtures(
            team_id=team_id,
            league_id=league_id,
            season=season,
        )
        return self._build_team_stats_from_fixtures(
            fixtures=fixtures,
            team_id=team_id,
            team_name=team_name,
            league_id=league_id,
            season=season,
        )

    @cached("league_squad_stats", ttl=14400)
    async def get_league_squad_stats(self, league_id: int) -> Dict[str, Any]:
        """Get detailed roster statistics for all teams in a league."""
        data = await self._request(f"{SPORT_NAME}/leagues/{league_id}/stats")
        league_stats = data.get("league_stats") or {}
        if not isinstance(league_stats, dict):
            return {}
        return league_stats.get("league") or {}

    # ── Lineups ───────────────────────────────────────────────────

    @cached("lineups", ttl=1800)
    async def get_lineups(self, fixture_id: int) -> List[Dict]:
        """Get lineups for a fixture."""
        fixture = await self.get_fixture(fixture_id)
        if not fixture:
            return []

        raw_match = fixture.get("raw", {}).get("match", {})
        lineups = raw_match.get("lineups")
        if not isinstance(lineups, dict):
            return []

        coaches = raw_match.get("coaches") or {}
        substitutions = raw_match.get("substitutions") or {}

        parsed_lineups = []
        for side in ("home", "away"):
            team = fixture.get("teams", {}).get(side, {})
            team_id = team.get("id")
            team_name = team.get("name")
            side_lineup = lineups.get(side) or {}
            players = self._ensure_list(side_lineup.get("player"))

            start_xi = [
                {
                    "player": {
                        "name": self._clean_text(player.get("name"), "Unknown"),
                        "number": self._to_int(player.get("number")),
                        "pos": self._clean_text(player.get("pos"), ""),
                    }
                }
                for player in players
            ]

            subs_raw = self._ensure_list(
                (substitutions.get(side) or {}).get("substitution")
            )
            substitutes = []
            for player in subs_raw:
                in_name = self._clean_text(player.get("player_in_name"))
                if not in_name:
                    continue
                substitutes.append(
                    {
                        "player": {
                            "name": in_name,
                            "number": self._to_int(player.get("player_in_number")),
                            "pos": "",
                        }
                    }
                )

            parsed_lineups.append(
                {
                    "team": {"id": team_id, "name": team_name},
                    "formation": self._clean_text(side_lineup.get("formation"), "Unknown"),
                    "coach": {
                        "name": self._clean_text(
                            (coaches.get(side) or {}).get("coach", {}).get("name"),
                            "Unknown",
                        )
                    },
                    "startXI": start_xi,
                    "substitutes": substitutes,
                }
            )

        return parsed_lineups

    # ── Injuries ──────────────────────────────────────────────────

    @cached("injuries", ttl=1800)
    async def get_injuries(
        self, fixture_id: Optional[int] = None, team_id: Optional[int] = None
    ) -> List[Dict]:
        """Get injuries for a fixture or team."""
        data = await self._request(f"{SPORT_NAME}/injuries-suspensions")
        payload = data.get("injuries_suspensions", {})

        injuries: List[Dict[str, Any]] = []
        for league in self._ensure_list(payload.get("league")):
            for match in self._ensure_list(league.get("match")):
                match_id = self._to_int(match.get("main_id"))
                if fixture_id and match_id != fixture_id:
                    continue

                for side in ("home", "away"):
                    side_team = match.get(side) or {}
                    side_team_id = self._to_int(side_team.get("id"))
                    if team_id and side_team_id != team_id:
                        continue

                    sidelined = side_team.get("sidelined") or {}
                    injuries.extend(
                        self._parse_injury_bucket(
                            sidelined=sidelined,
                            bucket="to_miss",
                            team_id=side_team_id,
                            team_name=self._clean_text(side_team.get("name"), "Unknown"),
                            fixture_id=match_id,
                        )
                    )
                    injuries.extend(
                        self._parse_injury_bucket(
                            sidelined=sidelined,
                            bucket="questionable",
                            team_id=side_team_id,
                            team_name=self._clean_text(side_team.get("name"), "Unknown"),
                            fixture_id=match_id,
                        )
                    )

        return injuries

    # ── Odds ──────────────────────────────────────────────────────

    @cached("odds", ttl=1800)
    async def get_odds(
        self,
        fixture_id: Optional[int] = None,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        bookmaker_id: Optional[int] = None,
    ) -> List[Dict]:
        """Get betting odds and map to API-Football format."""
        target_league_id = league_id
        if not target_league_id and fixture_id:
            fixture = await self.get_fixture(fixture_id)
            target_league_id = (fixture or {}).get("league", {}).get("id")

        if not target_league_id:
            return []

        params: Dict[str, Any] = {}
        season_param = self._normalize_season_param(season)
        if season_param:
            params["season"] = season_param

        data = await self._request(
            f"{SPORT_NAME}/leagues/{target_league_id}/odds/prematch",
            params=params,
        )
        odds_root = data.get("prematch_odds", {})
        league = odds_root.get("league") or {}
        matches = self._ensure_list(league.get("match"))

        normalized: List[Dict[str, Any]] = []
        for match in matches:
            match_id = self._to_int(match.get("main_id"))
            if fixture_id and match_id != fixture_id:
                continue

            market = self._find_match_winner_market(match.get("odds"))
            if not market:
                continue

            bookmakers = []
            for bookmaker in self._ensure_list(market.get("bookmaker")):
                bookmaker_int_id = self._to_int(bookmaker.get("id"))
                if bookmaker_id and bookmaker_int_id != bookmaker_id:
                    continue

                odds_values = self._parse_1x2_odds_values(bookmaker.get("odd"))
                if not odds_values:
                    continue

                bookmakers.append(
                    {
                        "name": self._clean_text(bookmaker.get("name"), "Unknown"),
                        "bets": [
                            {
                                "name": "Match Winner",
                                "values": [
                                    {"value": "Home", "odd": str(odds_values["Home"])},
                                    {"value": "Draw", "odd": str(odds_values["Draw"])},
                                    {"value": "Away", "odd": str(odds_values["Away"])},
                                ],
                            }
                        ],
                    }
                )

            if bookmakers:
                normalized.append(
                    {
                        "fixture": {"id": match_id},
                        "bookmakers": bookmakers,
                    }
                )

        return normalized

    # ── Standings ─────────────────────────────────────────────────

    @cached("standings", ttl=3600)
    async def get_standings(self, league_id: int, season: int) -> List[Dict]:
        """Get league standings mapped to API-Football-like shape."""
        season_param = self._normalize_season_param(season)
        params = {"season": season_param} if season_param else {}

        data = await self._request(
            f"{SPORT_NAME}/leagues/{league_id}/standings",
            params=params,
        )
        standings = data.get("standings") or {}

        # Some leagues fail with season filter on Statpal free tier.
        if not standings and season_param:
            data = await self._request(f"{SPORT_NAME}/leagues/{league_id}/standings")
            standings = data.get("standings") or {}

        if not isinstance(standings, dict):
            return []

        tournament = standings.get("tournament") or {}
        parsed_rows = self._parse_standing_rows(tournament)
        if not parsed_rows:
            return []

        season_raw = tournament.get("season") or season
        season_year = self._extract_season_year(season_raw) or season

        return [
            {
                "league": {
                    "id": self._to_int(tournament.get("id"), league_id),
                    "name": self._clean_text(tournament.get("league"), "Unknown League"),
                    "country": self._clean_text(standings.get("country")) or None,
                    "season": season_year,
                    "standings": [parsed_rows],
                }
            }
        ]

    # ── Predictions ───────────────────────────────────────────────

    @cached("api_predictions", ttl=3600)
    async def get_predictions(self, fixture_id: int) -> Optional[Dict]:
        """Statpal Soccer V2 currently has no direct fixture prediction endpoint."""
        return None

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    # ── Internal helpers ──────────────────────────────────────────

    @cached("statpal_daily_fixtures", ttl=900)
    async def _get_daily_fixtures(self, offset: int) -> List[Dict]:
        data = await self._request(f"{SPORT_NAME}/matches/daily", {"offset": offset})
        payload = self._extract_daily_payload(data)
        fixtures = self._normalize_daily_payload(payload)
        return fixtures

    @cached("statpal_league_fixtures", ttl=1800)
    async def _get_league_fixtures(
        self, league_id: int, season: Optional[str]
    ) -> List[Dict]:
        params: Dict[str, Any] = {}
        if season:
            params["season"] = season

        data = await self._request(
            f"{SPORT_NAME}/leagues/{league_id}/matches",
            params=params,
        )
        fixtures = self._normalize_league_payload(data)

        if not fixtures and season:
            data = await self._request(f"{SPORT_NAME}/leagues/{league_id}/matches")
            fixtures = self._normalize_league_payload(data)

        return fixtures

    async def _load_daily_window_fixtures(self) -> List[Dict]:
        tasks = [
            self._get_daily_fixtures(offset)
            for offset in range(self.DAILY_WINDOW_MIN_OFFSET, self.DAILY_WINDOW_MAX_OFFSET + 1)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        fixtures: List[Dict[str, Any]] = []
        for result in results:
            if isinstance(result, list):
                fixtures.extend(result)
        return self._dedupe_fixtures(fixtures)

    @cached("statpal_league_catalog", ttl=43200)
    async def _get_league_catalog(self) -> List[Dict[str, Any]]:
        data = await self._request(f"{SPORT_NAME}/leagues")
        leagues = (data.get("leagues") or {}).get("league")
        return self._ensure_list(leagues)

    @cached("statpal_reference_teams_v2", ttl=43200)
    async def _get_reference_team_candidates(self) -> List[Dict[str, Any]]:
        leagues = await self._get_league_catalog()
        selected = self._select_priority_leagues(leagues)
        if not selected:
            return []

        tasks = [
            self._request(f"{SPORT_NAME}/leagues/{league_id}/standings")
            for league_id, _, _ in selected
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        candidates: Dict[int, Dict[str, Any]] = {}
        for selected_item, response in zip(selected, results):
            league_id, league_name, league_country = selected_item
            if isinstance(response, Exception) or not isinstance(response, dict):
                continue

            standings = response.get("standings") or {}
            tournament = standings.get("tournament") or {}
            rows = self._parse_standing_rows(tournament)
            country_name = self._clean_text(
                standings.get("country"), self._clean_text(league_country).title()
            )

            for row in rows:
                team = row.get("team") or {}
                team_id = self._to_int(team.get("id"))
                team_name = self._clean_text(team.get("name"))
                if not team_id or not team_name:
                    continue

                entry = candidates.get(team_id)
                if not entry:
                    entry = {
                        "team": {
                            "id": team_id,
                            "name": team_name,
                            "code": self._derive_code(team_name),
                            "country": country_name or None,
                            "logo": None,
                        },
                        "venue": {"name": None},
                        "leagues": {"league_id": []},
                    }
                    candidates[team_id] = entry

                league_id_str = str(league_id)
                if league_id_str not in entry["leagues"]["league_id"]:
                    entry["leagues"]["league_id"].append(league_id_str)

        return list(candidates.values())

    async def _get_daily_by_date(self, date_str: str) -> List[Dict]:
        target = self._normalize_date_filter(date_str)
        if not target:
            return []

        try:
            target_date = datetime.strptime(target, "%Y-%m-%d").date()
        except ValueError:
            return []

        today = date.today()
        offset = (target_date - today).days
        if self.DAILY_WINDOW_MIN_OFFSET <= offset <= self.DAILY_WINDOW_MAX_OFFSET:
            return await self._get_daily_fixtures(offset)
        return []

    async def _infer_team_leagues(self, team_id: int) -> List[int]:
        league_ids: List[int] = []

        team = await self.get_team(team_id)
        if team:
            leagues = team.get("leagues", {})
            raw_ids = leagues.get("league_id") if isinstance(leagues, dict) else []
            for league_id in self._ensure_list(raw_ids):
                league_id_int = self._to_int(league_id)
                if league_id_int and league_id_int not in league_ids:
                    league_ids.append(league_id_int)

        if league_ids:
            return league_ids

        fixtures = await self._load_daily_window_fixtures()
        for fixture in fixtures:
            home_id = fixture.get("teams", {}).get("home", {}).get("id")
            away_id = fixture.get("teams", {}).get("away", {}).get("id")
            if team_id not in (home_id, away_id):
                continue
            league_id = fixture.get("league", {}).get("id")
            if league_id and league_id not in league_ids:
                league_ids.append(league_id)

        return league_ids

    def _extract_daily_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {}
        if isinstance(data.get("live_matches"), dict):
            return data["live_matches"]
        for key, value in data.items():
            if key.startswith("matches_") and isinstance(value, dict):
                return value
        return {}

    def _normalize_daily_payload(self, payload: Dict[str, Any]) -> List[Dict]:
        fixtures: List[Dict[str, Any]] = []
        for league in self._ensure_list(payload.get("league")):
            league_context = {
                "id": league.get("id"),
                "name": league.get("name"),
                "country": league.get("country"),
            }
            for match in self._ensure_list(league.get("match")):
                normalized = self._normalize_match(match, league_context=league_context)
                if normalized:
                    fixtures.append(normalized)
        return fixtures

    def _normalize_league_payload(self, data: Dict[str, Any]) -> List[Dict]:
        payload = data.get("matches", {})
        if not isinstance(payload, dict):
            return []

        country = payload.get("country")
        tournament = payload.get("tournament")
        tournaments = self._ensure_list(tournament)
        fixtures: List[Dict[str, Any]] = []

        for item in tournaments:
            if not isinstance(item, dict):
                continue

            league_context = {
                "id": item.get("id"),
                "name": item.get("league"),
                "country": country,
                "season": item.get("season"),
            }

            if item.get("week") is not None:
                for week in self._ensure_list(item.get("week")):
                    week_number = self._clean_text((week or {}).get("number"))
                    round_name = f"Week {week_number}" if week_number else None
                    for match in self._ensure_list((week or {}).get("match")):
                        normalized = self._normalize_match(
                            match,
                            league_context=league_context,
                            round_name=round_name,
                        )
                        if normalized:
                            fixtures.append(normalized)
            else:
                for match in self._ensure_list(item.get("match")):
                    normalized = self._normalize_match(match, league_context=league_context)
                    if normalized:
                        fixtures.append(normalized)

        return fixtures

    def _normalize_match(
        self,
        match: Dict[str, Any],
        league_context: Dict[str, Any],
        round_name: Optional[str] = None,
    ) -> Optional[Dict]:
        if not isinstance(match, dict):
            return None

        fixture_id = (
            self._to_int(match.get("main_id"))
            or self._to_int(match.get("fallback_id_1"))
            or self._to_int(match.get("fallback_id_2"))
            or self._to_int(match.get("fallback_id_3"))
        )
        if not fixture_id:
            return None

        kickoff = self._parse_datetime(match.get("date"), match.get("time"))
        date_iso = kickoff.isoformat() if kickoff else self._clean_text(match.get("date"))
        timestamp = int(kickoff.timestamp()) if kickoff else None

        home = match.get("home") or {}
        away = match.get("away") or {}
        home_goals = self._to_int(home.get("goals", home.get("score")))
        away_goals = self._to_int(away.get("goals", away.get("score")))

        raw_status = self._clean_text(match.get("status"))
        status_short = self._infer_status_short(raw_status, kickoff, home_goals, away_goals)
        status_long = self._status_long_label(status_short, raw_status)
        elapsed = self._to_int(raw_status) if raw_status.isdigit() else None

        season_raw = league_context.get("season")
        season = self._extract_season_year(season_raw)

        normalized = {
            "fixture": {
                "id": fixture_id,
                "date": date_iso,
                "timestamp": timestamp,
                "status": {
                    "long": status_long,
                    "short": status_short,
                    "elapsed": elapsed,
                },
            },
            "league": {
                "id": self._to_int(league_context.get("id")),
                "name": self._clean_text(league_context.get("name"), "Unknown League"),
                "country": self._clean_text(league_context.get("country")) or None,
                "season": season,
                "round": round_name,
            },
            "teams": {
                "home": {
                    "id": self._to_int(home.get("id")),
                    "name": self._clean_text(home.get("name"), "Home"),
                },
                "away": {
                    "id": self._to_int(away.get("id")),
                    "name": self._clean_text(away.get("name"), "Away"),
                },
            },
            "goals": {
                "home": home_goals,
                "away": away_goals,
            },
            "score": {
                "halftime": self._parse_score_map(match.get("ht")),
                "fulltime": self._parse_score_map(match.get("ft"), fallback_home=home_goals, fallback_away=away_goals),
                "extratime": self._parse_score_map(match.get("et")),
                "penalty": self._parse_score_map(match.get("penalties")),
            },
            "raw": {
                "match": match,
                "league": league_context,
            },
        }

        self._fixture_index[fixture_id] = normalized
        return normalized

    def _normalize_h2h_match(self, match: Dict[str, Any]) -> Optional[Dict]:
        if not isinstance(match, dict):
            return None

        fixture_id = (
            self._to_int(match.get("main_id"))
            or self._to_int(match.get("fallback_id_1"))
            or self._to_int(match.get("fallback_id_2"))
        )
        if not fixture_id:
            return None

        kickoff = self._parse_datetime(match.get("date"), "00:00")
        date_iso = kickoff.isoformat() if kickoff else self._clean_text(match.get("date"))
        timestamp = int(kickoff.timestamp()) if kickoff else None

        team1_score = self._to_int(match.get("team1_score"), 0)
        team2_score = self._to_int(match.get("team2_score"), 0)
        season = self._extract_season_year(match.get("date"))

        normalized = {
            "fixture": {
                "id": fixture_id,
                "date": date_iso,
                "timestamp": timestamp,
                "status": {"long": "Match Finished", "short": "FT", "elapsed": 90},
            },
            "league": {
                "id": self._to_int(match.get("league_id")),
                "name": self._clean_text(match.get("league"), "Unknown League"),
                "country": self._clean_text(match.get("country")) or None,
                "season": season,
                "round": None,
            },
            "teams": {
                "home": {
                    "id": self._to_int(match.get("team1_id")),
                    "name": self._clean_text(match.get("team1_name"), "Home"),
                },
                "away": {
                    "id": self._to_int(match.get("team2_id")),
                    "name": self._clean_text(match.get("team2_name"), "Away"),
                },
            },
            "goals": {"home": team1_score, "away": team2_score},
            "score": {
                "halftime": {"home": None, "away": None},
                "fulltime": {"home": team1_score, "away": team2_score},
                "extratime": {"home": None, "away": None},
                "penalty": {"home": None, "away": None},
            },
            "raw": {"match": match},
        }

        self._fixture_index[fixture_id] = normalized
        return normalized

    def _map_team_stats_from_payload(
        self,
        team: Dict[str, Any],
        team_id: int,
        team_name: str,
        league_id: int,
        season: int,
    ) -> Optional[Dict]:
        league_stats = team.get("league_stats") or {}
        leagues = self._ensure_list(league_stats.get("league"))

        for league in leagues:
            league_item_id = self._to_int((league or {}).get("id"))
            if league_item_id != league_id:
                continue

            league_season = self._extract_season_year((league or {}).get("season"))
            if season and league_season and league_season != season:
                continue

            fulltime = (league or {}).get("fulltime") or {}
            wins = fulltime.get("win") or {}
            draws = fulltime.get("draw") or {}
            losses = fulltime.get("lost") or {}
            goals_for = fulltime.get("goals_for") or {}
            goals_against = fulltime.get("goals_against") or {}

            return {
                "team": {"id": team_id, "name": team_name},
                "league": {"id": league_id, "season": league_season or season},
                "fixtures": {
                    "wins": {
                        "total": self._to_int(wins.get("total"), 0),
                        "home": self._to_int(wins.get("home"), 0),
                        "away": self._to_int(wins.get("away"), 0),
                    },
                    "draws": {
                        "total": self._to_int(draws.get("total"), 0),
                        "home": self._to_int(draws.get("home"), 0),
                        "away": self._to_int(draws.get("away"), 0),
                    },
                    "loses": {
                        "total": self._to_int(losses.get("total"), 0),
                        "home": self._to_int(losses.get("home"), 0),
                        "away": self._to_int(losses.get("away"), 0),
                    },
                },
                "goals": {
                    "for": {
                        "total": {
                            "total": self._to_int(goals_for.get("total"), 0),
                            "home": self._to_int(goals_for.get("home"), 0),
                            "away": self._to_int(goals_for.get("away"), 0),
                        }
                    },
                    "against": {
                        "total": {
                            "total": self._to_int(goals_against.get("total"), 0),
                            "home": self._to_int(goals_against.get("home"), 0),
                            "away": self._to_int(goals_against.get("away"), 0),
                        }
                    },
                },
                "lineups": [],
            }

        return None

    def _build_team_stats_from_fixtures(
        self,
        fixtures: List[Dict[str, Any]],
        team_id: int,
        team_name: str,
        league_id: int,
        season: int,
    ) -> Dict:
        finished = [fixture for fixture in fixtures if self._is_finished_fixture(fixture)]
        wins = draws = losses = 0
        wins_home = draws_home = losses_home = 0
        wins_away = draws_away = losses_away = 0
        goals_for_total = goals_against_total = 0
        goals_for_home = goals_against_home = 0
        goals_for_away = goals_against_away = 0
        formation_counter: Counter[str] = Counter()

        for fixture in finished:
            teams = fixture.get("teams", {})
            goals = fixture.get("goals", {})
            home_id = teams.get("home", {}).get("id")
            away_id = teams.get("away", {}).get("id")
            home_goals = self._to_int(goals.get("home"), 0)
            away_goals = self._to_int(goals.get("away"), 0)
            is_home = team_id == home_id

            if team_id not in (home_id, away_id):
                continue

            goals_for = home_goals if is_home else away_goals
            goals_against = away_goals if is_home else home_goals

            goals_for_total += goals_for
            goals_against_total += goals_against
            if is_home:
                goals_for_home += goals_for
                goals_against_home += goals_against
            else:
                goals_for_away += goals_for
                goals_against_away += goals_against

            if goals_for > goals_against:
                wins += 1
                if is_home:
                    wins_home += 1
                else:
                    wins_away += 1
            elif goals_for == goals_against:
                draws += 1
                if is_home:
                    draws_home += 1
                else:
                    draws_away += 1
            else:
                losses += 1
                if is_home:
                    losses_home += 1
                else:
                    losses_away += 1

            raw_match = fixture.get("raw", {}).get("match", {})
            side = "home" if is_home else "away"
            formation = self._clean_text(
                ((raw_match.get("lineups") or {}).get(side) or {}).get("formation")
            )
            if formation:
                formation_counter[formation] += 1

        lineups = [
            {"formation": formation, "played": count}
            for formation, count in formation_counter.most_common(5)
        ]

        return {
            "team": {"id": team_id, "name": team_name},
            "league": {"id": league_id, "season": season},
            "fixtures": {
                "wins": {"total": wins, "home": wins_home, "away": wins_away},
                "draws": {"total": draws, "home": draws_home, "away": draws_away},
                "loses": {"total": losses, "home": losses_home, "away": losses_away},
            },
            "goals": {
                "for": {
                    "total": {
                        "total": goals_for_total,
                        "home": goals_for_home,
                        "away": goals_for_away,
                    }
                },
                "against": {
                    "total": {
                        "total": goals_against_total,
                        "home": goals_against_home,
                        "away": goals_against_away,
                    }
                },
            },
            "lineups": lineups,
        }

    def _parse_injury_bucket(
        self,
        sidelined: Dict[str, Any],
        bucket: str,
        team_id: Optional[int],
        team_name: str,
        fixture_id: Optional[int],
    ) -> List[Dict]:
        if not isinstance(sidelined, dict):
            return []

        section = sidelined.get(bucket)
        if not section:
            return []

        if isinstance(section, dict):
            players = self._ensure_list(section.get("player"))
        else:
            players = self._ensure_list(section)

        parsed = []
        for player in players:
            if not isinstance(player, dict):
                continue
            status = self._clean_text(player.get("status"), "Unavailable")
            parsed.append(
                {
                    "team": {"id": team_id, "name": team_name},
                    "fixture": {"id": fixture_id},
                    "player": {
                        "id": self._to_int(player.get("id")),
                        "name": self._clean_text(player.get("name"), "Unknown"),
                        "type": bucket,
                        "reason": status,
                    },
                }
            )
        return parsed

    def _find_match_winner_market(self, markets: Any) -> Optional[Dict[str, Any]]:
        for market in self._ensure_list(markets):
            market_name = self._clean_text((market or {}).get("name")).lower()
            if market_name in {"1x2", "match winner", "winner", "1x2 full time"}:
                return market
        return None

    def _parse_1x2_odds_values(self, raw_odds: Any) -> Optional[Dict[str, float]]:
        values: Dict[str, float] = {}
        for item in self._ensure_list(raw_odds):
            if not isinstance(item, dict):
                continue
            label = self._clean_text(item.get("name")).lower()
            value = self._to_float(item.get("value"))
            if value is None:
                continue
            if label == "home":
                values["Home"] = value
            elif label == "draw":
                values["Draw"] = value
            elif label == "away":
                values["Away"] = value

        if {"Home", "Draw", "Away"}.issubset(values):
            return values
        return None

    def _parse_standing_rows(self, tournament: Dict[str, Any]) -> List[Dict]:
        rows: List[Dict[str, Any]] = []
        if not isinstance(tournament, dict):
            return rows

        for team_row in self._ensure_list(tournament.get("team")):
            parsed = self._parse_standing_row(team_row, group_name=None)
            if parsed:
                rows.append(parsed)

        for group in self._ensure_list(tournament.get("group")):
            if not isinstance(group, dict):
                continue
            group_name = self._clean_text(group.get("name")) or None
            for team_row in self._ensure_list(group.get("team")):
                parsed = self._parse_standing_row(team_row, group_name=group_name)
                if parsed:
                    rows.append(parsed)

        rows.sort(key=lambda row: row.get("rank") or 999)
        return rows

    def _parse_standing_row(
        self, row: Dict[str, Any], group_name: Optional[str]
    ) -> Optional[Dict]:
        if not isinstance(row, dict):
            return None

        overall = self._ensure_dict(row.get("overall"))
        home = self._ensure_dict(row.get("home"))
        away = self._ensure_dict(row.get("away"))
        total = self._ensure_dict(row.get("total"))

        played = self._to_int(overall.get("games_played"), 0)
        parsed = {
            "rank": self._to_int(row.get("position"), 0),
            "team": {
                "id": self._to_int(row.get("id")),
                "name": self._clean_text(row.get("name"), "Unknown"),
            },
            "points": self._to_int(total.get("points"), 0),
            "goalsDiff": self._to_int(total.get("goal_difference"), 0),
            "group": group_name,
            "form": self._clean_text(row.get("recent_form")) or None,
            "status": self._clean_text(row.get("status")) or None,
            "description": self._clean_text((row.get("description") or {}).get("value")) or None,
            "played": played,
            "all": {
                "played": played,
                "win": self._to_int(overall.get("wins"), 0),
                "draw": self._to_int(overall.get("draws"), 0),
                "lose": self._to_int(overall.get("losses"), 0),
            },
            "home": {
                "played": self._to_int(home.get("games_played"), 0),
                "win": self._to_int(home.get("wins"), 0),
                "draw": self._to_int(home.get("draws"), 0),
                "lose": self._to_int(home.get("losses"), 0),
            },
            "away": {
                "played": self._to_int(away.get("games_played"), 0),
                "win": self._to_int(away.get("wins"), 0),
                "draw": self._to_int(away.get("draws"), 0),
                "lose": self._to_int(away.get("losses"), 0),
            },
        }
        return parsed

    def _team_match_score(self, query: str, candidate: Dict[str, Any]) -> float:
        team = candidate.get("team", {})
        team_name = self._normalize_lookup_text(team.get("name", ""))
        code = self._normalize_lookup_text(team.get("code", ""))

        if not team_name:
            return 0.0

        query_variants = self._name_variants(query)
        name_variants = self._name_variants(team_name)
        if code:
            name_variants.add(code)

        if query_variants & name_variants:
            return 100.0

        best_overlap = 0.0
        best_seq = 0.0
        for q_variant in query_variants:
            q_tokens = self._token_signature(q_variant)
            for name_variant in name_variants:
                n_tokens = self._token_signature(name_variant)
                if q_tokens:
                    overlap = len(q_tokens & n_tokens) / len(q_tokens)
                    best_overlap = max(best_overlap, overlap)
                best_seq = max(best_seq, SequenceMatcher(None, q_variant, name_variant).ratio())

        if best_overlap == 0.0 and best_seq < 0.75:
            return best_seq * 20.0

        score = max(best_overlap * 92.0 + best_seq * 8.0, best_seq * 70.0)

        q_len = len(self._token_signature(query))
        n_len = len(self._token_signature(team_name))
        score -= abs(q_len - n_len) * 4.0
        if q_len >= 3 and n_len <= 1 and best_overlap < 0.7:
            score -= 20.0

        return max(score, 0.0)

    def _select_priority_leagues(self, leagues: List[Dict[str, Any]]) -> List[tuple[int, str, str]]:
        selected: List[tuple[int, str, str, int]] = []

        for item in leagues:
            league_id = self._to_int((item or {}).get("id"))
            if not league_id:
                continue
            country = self._normalize_lookup_text((item or {}).get("country"))
            name = self._normalize_lookup_text((item or {}).get("name"))
            season = self._extract_season_year((item or {}).get("season")) or 0

            for country_match, league_match in self.PRIORITY_LEAGUES:
                if country_match in country and league_match in name:
                    selected.append((league_id, name, country, season))
                    break

        dedup: Dict[int, tuple[int, str, str, int]] = {}
        for entry in sorted(selected, key=lambda value: value[3], reverse=True):
            league_id = entry[0]
            if league_id not in dedup:
                dedup[league_id] = entry

        return [(lid, lname, lcountry) for lid, lname, lcountry, _ in dedup.values()]

    def _name_variants(self, normalized_name: str) -> set[str]:
        base = self._normalize_lookup_text(normalized_name)
        if not base:
            return set()

        variants = {base}
        for group in self.TEAM_ALIAS_GROUPS:
            normalized_group = {self._normalize_lookup_text(alias) for alias in group}
            if base in normalized_group:
                variants |= normalized_group

        tokens = base.split()
        if len(tokens) == 2 and tokens[0] == "as":
            variants.add(tokens[1])
        if len(tokens) == 2 and tokens[0] in {"fc", "ac", "sc", "cf"}:
            variants.add(tokens[1])
        if len(tokens) >= 3 and tokens[0] == "paris" and "saint" in tokens:
            variants.add("psg")

        compact = " ".join(token for token in tokens if token not in self.TOKEN_STOPWORDS)
        if compact:
            variants.add(compact)

        for idx, token in enumerate(tokens):
            for alias in self.TOKEN_ALIASES.get(token, ()):
                alt = list(tokens)
                alt[idx] = alias
                alt_name = " ".join(alt).strip()
                if alt_name:
                    variants.add(alt_name)

                alt_compact = " ".join(
                    piece for piece in alt if piece not in self.TOKEN_STOPWORDS
                ).strip()
                if alt_compact:
                    variants.add(alt_compact)

        return {variant for variant in variants if variant}

    def _token_signature(self, normalized_name: str) -> set[str]:
        tokens = self._normalize_lookup_text(normalized_name).split()
        return {token for token in tokens if token and token not in self.TOKEN_STOPWORDS}

    def _is_finished_fixture(self, fixture: Dict[str, Any]) -> bool:
        status = self._clean_text(
            fixture.get("fixture", {}).get("status", {}).get("short")
        ).upper()
        
        # Explicit early returns based on status string from API Provider
        if status in {"FT", "AET", "PEN", "AWD", "WO", "CANC", "ABD"}:
            return True
        if status in {"NS", "TBD", "PST", "LIVE", "1H", "HT", "2H", "ET", "BT", "P", "INT", "SUSP"}:
            return False
            
        if status.isdigit():
            return int(status) >= 90

        goals = fixture.get("goals", {})
        home_goals = goals.get("home")
        away_goals = goals.get("away")
        
        # Fallback heuristic: only assume it's finished if goals are present AND the date is strictly PAST (not today),
        # because sometimes providers set goals to 0-0 early for today's matches.
        if home_goals is not None and away_goals is not None:
            fixture_date = self._parse_datetime(
                fixture.get("fixture", {}).get("date"),
                "00:00",
            )
            if fixture_date and fixture_date.date() < date.today():
                return True
                
        return False

    @staticmethod
    def _fixture_sort_key(fixture: Dict[str, Any]) -> tuple[int, int]:
        timestamp = fixture.get("fixture", {}).get("timestamp")
        fixture_id = fixture.get("fixture", {}).get("id")
        return (timestamp or 0, fixture_id or 0)

    @staticmethod
    def _dedupe_fixtures(fixtures: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: Dict[int, Dict[str, Any]] = {}
        passthrough: List[Dict[str, Any]] = []
        for fixture in fixtures:
            fixture_id = (fixture.get("fixture") or {}).get("id")
            if fixture_id:
                deduped[fixture_id] = fixture
            else:
                passthrough.append(fixture)
        return list(deduped.values()) + passthrough

    @classmethod
    def _normalize_date_filter(cls, raw: str) -> str:
        raw = cls._clean_text(raw)
        if not raw:
            return ""

        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(raw[:10], fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Already ISO datetime
        if "T" in raw:
            return raw.split("T", 1)[0]
        return raw[:10]

    @classmethod
    def _parse_datetime(cls, date_raw: Any, time_raw: Any) -> Optional[datetime]:
        date_clean = cls._clean_text(date_raw)
        if not date_clean:
            return None

        time_clean = cls._clean_text(time_raw, "00:00")
        if ":" not in time_clean:
            time_clean = "00:00"

        for fmt in ("%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"):
            try:
                return datetime.strptime(f"{date_clean} {time_clean}", fmt)
            except ValueError:
                continue

        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(date_clean, fmt)
            except ValueError:
                continue

        return None

    @classmethod
    def _parse_score_map(
        cls,
        score_raw: Any,
        fallback_home: Optional[int] = None,
        fallback_away: Optional[int] = None,
    ) -> Dict[str, Optional[int]]:
        home_value: Optional[int] = None
        away_value: Optional[int] = None

        if isinstance(score_raw, dict):
            home_value = cls._to_int(score_raw.get("home"))
            away_value = cls._to_int(score_raw.get("away"))
        elif isinstance(score_raw, str) and "-" in score_raw:
            left, right = score_raw.split("-", 1)
            home_value = cls._to_int(left)
            away_value = cls._to_int(right)

        if home_value is None:
            home_value = fallback_home
        if away_value is None:
            away_value = fallback_away
        return {"home": home_value, "away": away_value}

    @classmethod
    def _infer_status_short(
        cls,
        raw_status: str,
        kickoff: Optional[datetime],
        home_goals: Optional[int],
        away_goals: Optional[int],
    ) -> str:
        status = cls._clean_text(raw_status).upper()

        if not status:
            if home_goals is not None and away_goals is not None:
                return "FT"
            return "NS"

        if ":" in status:
            return "NS"

        if status in {"NS", "TBD"}:
            return "NS"
        if status in {"FT", "AET", "PEN"}:
            return status
        if status in {"HT", "LIVE", "1H", "2H", "ET"}:
            return "LIVE"
        if status in {"CANC", "ABD", "POST", "AWD", "WO"}:
            return status
        if status.isdigit():
            minute = int(status)
            if minute >= 90:
                return "FT"
            return "LIVE"

        if home_goals is not None and away_goals is not None:
            if kickoff and kickoff.date() <= date.today():
                return "FT"
        return "NS"

    @staticmethod
    def _status_long_label(status_short: str, raw_status: str) -> str:
        mapping = {
            "NS": "Not Started",
            "LIVE": "Live",
            "HT": "Halftime",
            "FT": "Match Finished",
            "AET": "After Extra Time",
            "PEN": "Penalty Shootout",
            "CANC": "Cancelled",
            "ABD": "Abandoned",
            "POST": "Postponed",
            "AWD": "Awarded",
            "WO": "Walkover",
        }
        return mapping.get(status_short, raw_status or "Unknown")

    @classmethod
    def _extract_season_year(cls, raw_season: Any) -> Optional[int]:
        clean = cls._clean_text(raw_season)
        if not clean:
            return None

        match = re.search(r"\d{4}", clean)
        if not match:
            return None
        return cls._to_int(match.group(0))

    @staticmethod
    def _normalize_season_param(season: Optional[int]) -> Optional[str]:
        if season is None:
            return None
        season_str = str(season).strip()
        return season_str or None

    @staticmethod
    def _derive_code(team_name: Any) -> Optional[str]:
        name = str(team_name or "").strip()
        if not name:
            return None
        parts = [p for p in re.split(r"\s+", name) if p]
        if len(parts) >= 2:
            return (parts[0][:1] + parts[1][:2]).upper()
        return parts[0][:3].upper()

    @staticmethod
    def _normalize_lookup_text(value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKD", text)
        without_accents = "".join(
            ch for ch in normalized if not unicodedata.combining(ch)
        )
        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", without_accents).lower()
        return re.sub(r"\s+", " ", clean).strip()

    @staticmethod
    def _ensure_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    @staticmethod
    def _ensure_dict(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            return value[0]
        return {}

    @staticmethod
    def _clean_text(value: Any, default: str = "") -> str:
        if value is None:
            return default
        text = str(value).strip()
        if not text or text in {"?", "null", "None"}:
            return default
        return text

    @staticmethod
    def _to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
        if value is None:
            return default
        text = str(value).strip()
        if not text or text in {"?", "null", "None"}:
            return default
        try:
            return int(float(text))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text in {"?", "null", "None"}:
            return None
        try:
            return float(text)
        except (TypeError, ValueError):
            return None


# Singleton instance
_client: Optional[APIFootballClient] = None


def get_api_football_client() -> APIFootballClient:
    """Get or create API client singleton (Statpal-backed adapter)."""
    global _client
    if _client is None:
        _client = APIFootballClient()
    return _client
