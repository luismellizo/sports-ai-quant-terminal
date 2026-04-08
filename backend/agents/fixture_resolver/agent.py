"""
Sports AI — Fixture Resolver Agent
Deterministically resolves the real upcoming fixture for the requested team pair.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext, AgentOutcome, AgentStatus
from backend.services.api_football_client import get_api_football_client


class FixtureResolverAgent(BaseAgent):
    name = "FixtureResolverAgent"
    is_critical = True
    timeout_seconds = 60.0

    MAX_TEAM_CANDIDATES = 6
    NEXT_FIXTURE_WINDOW = 20

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        requested_home = (ctx.data.get("team_home") or "").strip()
        requested_away = (ctx.data.get("team_away") or "").strip()
        requested_league = (ctx.data.get("league_hint") or "").strip()

        if not requested_home or not requested_away:
            return {
                "fixture_resolution_status": "missing_teams",
                "fixture_resolution_confidence": 0.0,
                "fixture_resolution_warnings": [
                    "No se pudieron resolver ambos equipos desde la consulta."
                ],
            }

        api = get_api_football_client()
        home_candidates = (await api.search_teams(requested_home))[
            : self.MAX_TEAM_CANDIDATES
        ]
        away_candidates = (await api.search_teams(requested_away))[
            : self.MAX_TEAM_CANDIDATES
        ]

        if not home_candidates or not away_candidates:
            warnings = []
            if not home_candidates:
                warnings.append(
                    f"No se encontraron candidatos para '{requested_home}'."
                )
            if not away_candidates:
                warnings.append(
                    f"No se encontraron candidatos para '{requested_away}'."
                )
            return {
                "fixture_resolution_status": "team_not_found",
                "fixture_resolution_confidence": 0.0,
                "fixture_resolution_warnings": warnings,
            }

        fixtures_by_team = await self._prefetch_candidate_fixtures(
            api=api,
            home_candidates=home_candidates,
            away_candidates=away_candidates,
        )
        all_candidates = home_candidates + away_candidates

        pair_scores = self._score_candidate_pairs(
            home_candidates=home_candidates,
            away_candidates=away_candidates,
            fixtures_by_team=fixtures_by_team,
            requested_league=requested_league,
            all_candidates=all_candidates,
        )

        if not pair_scores:
            return {
                "fixture_resolution_status": "pair_unresolved",
                "fixture_resolution_confidence": 0.0,
                "fixture_resolution_warnings": [
                    "No fue posible resolver un cruce de equipos válido."
                ],
            }

        pair_scores.sort(key=lambda item: item["score"], reverse=True)
        best = pair_scores[0]
        runner_up = pair_scores[1] if len(pair_scores) > 1 else None
        confidence = self._compute_confidence(best, runner_up)

        return self._build_resolved_payload(
            best,
            confidence,
            requested_home,
            requested_away,
            requested_league,
            pair_scores[1:4],
        )

    async def _prefetch_candidate_fixtures(self, api, home_candidates, away_candidates):
        team_ids = []
        for entry in home_candidates + away_candidates:
            team_id = self._team_id(entry)
            if team_id and team_id not in team_ids:
                team_ids.append(team_id)

        fixtures_by_team = {}
        for team_id in team_ids:
            fixtures = await api.get_fixtures(
                team_id=team_id
            )
            fixtures_by_team[team_id] = fixtures or []
        return fixtures_by_team

    def _score_candidate_pairs(
        self,
        home_candidates,
        away_candidates,
        fixtures_by_team,
        requested_league,
        all_candidates,
    ):
        scores = []
        for home_rank, home_entry in enumerate(home_candidates):
            for away_rank, away_entry in enumerate(away_candidates):
                home_id = self._team_id(home_entry)
                away_id = self._team_id(away_entry)
                if not home_id or not away_id or home_id == away_id:
                    continue

                fixture = self._find_shared_upcoming_fixture(
                    home_id, away_id, fixtures_by_team
                )
                score = 100.0 - (home_rank * 7.0 + away_rank * 7.0)
                if fixture:
                    score += 120.0
                    fixture_league = str((fixture.get("league") or {}).get("name", ""))
                    if requested_league and self._text_overlap(
                        requested_league, fixture_league
                    ):
                        score += 20.0
                else:
                    score -= 25.0

                scores.append(
                    {
                        "score": score,
                        "home_entry": home_entry,
                        "away_entry": away_entry,
                        "fixture": fixture,
                        "canonical_home_entry": self._entry_for_team_id(
                            all_candidates, self._fixture_home_id(fixture)
                        )
                        if fixture
                        else home_entry,
                        "canonical_away_entry": self._entry_for_team_id(
                            all_candidates, self._fixture_away_id(fixture)
                        )
                        if fixture
                        else away_entry,
                    }
                )
        return scores

    def _build_resolved_payload(
        self,
        best,
        confidence,
        requested_home,
        requested_away,
        requested_league,
        alternatives,
    ):
        fixture = best.get("fixture")
        home_entry = best.get("canonical_home_entry") or best.get("home_entry")
        away_entry = best.get("canonical_away_entry") or best.get("away_entry")

        home_team = (home_entry or {}).get("team", {})
        away_team = (away_entry or {}).get("team", {})
        home_id = self._team_id(home_entry)
        away_id = self._team_id(away_entry)

        warnings = []
        status = "resolved"

        if not fixture:
            status = "resolved_without_fixture"
            warnings.append(
                "No se encontró fixture próximo confirmado entre ambos equipos."
            )

        if confidence < 0.60:
            status = "ambiguous"
            warnings.append("Resolución ambigua del partido.")

        fixture_id = ((fixture or {}).get("fixture") or {}).get("id")
        league = (fixture or {}).get("league") or {}
        fixture_date = ((fixture or {}).get("fixture") or {}).get("date")

        confirm_message = ""
        if fixture:
            confirm_message = f"Confirmación: {home_team.get('name')} vs {away_team.get('name')} ({league.get('name', 'Liga desconocida')}) el {fixture_date}."

        return {
            "team_home": home_team.get("name") or requested_home,
            "team_away": away_team.get("name") or requested_away,
            "home_team_id": home_id,
            "away_team_id": away_id,
            "fixture": fixture,
            "fixture_id": fixture_id,
            "league_id": league.get("id"),
            "league_name": league.get("name"),
            "league_country": league.get("country"),
            "season": league.get("season"),
            "fixture_resolution_status": status,
            "fixture_resolution_confidence": round(confidence, 3),
            "fixture_resolution_confirmation_message": confirm_message,
            "fixture_resolution_warnings": warnings,
            "fixture_resolution_alternatives": [
                self._format_alternative(item) for item in alternatives
            ],
        }

    def _find_shared_upcoming_fixture(self, team_a_id, team_b_id, fixtures_by_team):
        fixtures = fixtures_by_team.get(team_a_id, [])
        if not fixtures:
            return None
            
        shared = []
        for fixture in fixtures:
            home_id = self._fixture_home_id(fixture)
            away_id = self._fixture_away_id(fixture)
            if team_a_id in {home_id, away_id} and team_b_id in {home_id, away_id}:
                shared.append(fixture)
                
        if not shared:
            return None
            
        now = datetime.now(timezone.utc).timestamp()
        
        def _get_timestamp(f):
            ts = f.get("fixture", {}).get("timestamp")
            return float(ts) if ts else 0.0
            
        def _sort_key(f):
            ts = _get_timestamp(f)
            diff = ts - now
            is_far_past = diff < -86400 * 3  # older than 3 days
            return (is_far_past, abs(diff))
            
        shared.sort(key=_sort_key)
        return shared[0]

    def _compute_confidence(self, best, runner_up):
        best_score = float(best.get("score", 0.0))
        second_score = float((runner_up or {}).get("score", 0.0))
        margin = max(0.0, best_score - second_score)
        has_fixture = bool(best.get("fixture"))
        base = 0.35 if has_fixture else 0.15
        confidence = base + min(0.35, best_score / 300.0) + min(0.30, margin / 140.0)
        return max(0.0, min(0.99, confidence))

    def _entry_for_team_id(self, entries, team_id):
        if not team_id:
            return None
        for entry in entries:
            if self._team_id(entry) == team_id:
                return entry
        return None

    def _format_alternative(self, candidate):
        home_team = ((candidate.get("home_entry") or {}).get("team") or {}).get("name")
        away_team = ((candidate.get("away_entry") or {}).get("team") or {}).get("name")
        fixture = candidate.get("fixture") or {}
        fixture_meta = fixture.get("fixture") or {}
        league_meta = fixture.get("league") or {}
        return {
            "score": round(float(candidate.get("score", 0.0)), 2),
            "home_team": home_team,
            "away_team": away_team,
            "fixture_id": fixture_meta.get("id"),
            "fixture_date": fixture_meta.get("date"),
            "league_name": league_meta.get("name"),
        }

    @staticmethod
    def _team_id(entry):
        team = (entry or {}).get("team") or {}
        value = team.get("id")
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _fixture_home_id(fixture):
        value = ((fixture or {}).get("teams") or {}).get("home", {}).get("id")
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _fixture_away_id(fixture):
        value = ((fixture or {}).get("teams") or {}).get("away", {}).get("id")
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _text_overlap(text_a, text_b):
        a = str(text_a or "").strip().lower()
        b = str(text_b or "").strip().lower()
        if not a or not b:
            return False
        return a in b or b in a
