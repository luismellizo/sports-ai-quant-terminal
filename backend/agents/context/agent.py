"""
Sports AI — Context Agent
Identifies match competitive context with real data and LLM analysis.
"""

import json
import re
import unicodedata
from typing import Dict, Any

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext, AgentStatus
from backend.services.api_football_client import get_api_football_client
from backend.llm.llm_router import get_llm_router

RIVALRIES = {
    frozenset({"barcelona", "real madrid"}): "El Clásico",
    frozenset({"atletico madrid", "real madrid"}): "Derby of Madrid",
    frozenset({"ac milan", "inter"}): "Derby della Madonnina",
    frozenset({"liverpool", "manchester united"}): "North West Derby",
    frozenset({"arsenal", "tottenham"}): "North London Derby",
    frozenset({"boca juniors", "river plate"}): "Superclásico",
    frozenset({"celtic", "rangers"}): "Old Firm",
    frozenset({"bayern munich", "borussia dortmund"}): "Der Klassiker",
    frozenset({"psg", "olympique marseille"}): "Le Classique",
    frozenset({"roma", "lazio"}): "Derby della Capitale",
    frozenset({"benfica", "porto"}): "O Clássico",
    frozenset({"galatasaray", "fenerbahce"}): "Intercontinental Derby",
}

CONTEXT_SYSTEM_PROMPT = """Eres un analista deportivo experto en contexto competitivo de fútbol. Dado un partido con datos reales de la temporada, genera un análisis contextual profundo.

Devuelve ÚNICAMENTE un objeto JSON:
{
  "context_narrative": "párrafo de 3-5 líneas con el análisis contextual profundo",
  "match_importance_score": 0.0-1.0,
  "home_motivation": "alta/media/baja — con razón",
  "away_motivation": "alta/media/baja — con razón",
  "key_context_factors": ["factor1", "factor2", "factor3"],
  "tactical_context": "una línea sobre qué implica tácticamente este contexto"
}"""


class ContextAgent(BaseAgent):
    name = "ContextAgent"
    is_critical = True
    timeout_seconds = 60.0

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        team_home = (ctx.data.get("team_home") or "").lower()
        team_away = (ctx.data.get("team_away") or "").lower()

        api = get_api_football_client()
        home_id = ctx.data.get("home_team_id")
        away_id = ctx.data.get("away_team_id")
        fixture = ctx.data.get("fixture")
        league_info = (fixture or {}).get("league", {}) if fixture else {}

        if not home_id or not away_id:
            home_id, away_id, fixture = await self._resolve_ids(api, ctx.data)

        team_pair = frozenset({team_home, team_away})
        rivalry_name = None
        is_rivalry = False
        for pair, name in RIVALRIES.items():
            if pair.issubset(team_pair):
                rivalry_name = name
                is_rivalry = True
                break

        standings_data = {}
        home_season_stats = None
        away_season_stats = None
        league_id = league_info.get("id")
        season = league_info.get("season")

        if league_id and season:
            raw_standings = await api.get_standings(league_id, season)
            if raw_standings:
                standings_data = self._parse_standings(raw_standings, home_id, away_id)
            if home_id:
                home_season_stats = await api.get_team_statistics(
                    home_id, league_id, season
                )
            if away_id:
                away_season_stats = await api.get_team_statistics(
                    away_id, league_id, season
                )

        importance = 0.5
        round_name = (league_info.get("round") or "").lower() if league_info else ""
        if "final" in round_name:
            importance = 1.0
        elif "semi" in round_name:
            importance = 0.9
        elif "quarter" in round_name:
            importance = 0.85
        elif is_rivalry:
            importance = 0.8

        llm_analysis = await self._analyze_context_with_llm(
            ctx.data,
            standings_data,
            home_season_stats,
            away_season_stats,
            league_info,
            is_rivalry,
            rivalry_name,
            round_name,
        )

        warnings = list(ctx.data.get("fixture_resolution_warnings", []))
        if not home_id:
            warnings.append("Equipo local no identificado en API.")
        if not away_id:
            warnings.append("Equipo visitante no identificado en API.")

        context_data_source = "api" if (fixture and league_id) else "missing"

        return {
            "home_team_id": home_id,
            "away_team_id": away_id,
            "fixture": fixture,
            "fixture_id": fixture.get("fixture", {}).get("id") if fixture else None,
            "league_id": league_id,
            "league_name": league_info.get(
                "name", ctx.data.get("league_name", "Unknown")
            ),
            "league_country": league_info.get("country"),
            "season": season,
            "round": league_info.get("round"),
            "is_rivalry": is_rivalry,
            "rivalry_name": rivalry_name,
            "competition_stage": round_name or "regular_season",
            "match_importance": llm_analysis.get("match_importance_score", importance),
            "standings": standings_data,
            "home_season_stats": home_season_stats,
            "away_season_stats": away_season_stats,
            "context_narrative": llm_analysis.get("context_narrative", ""),
            "home_motivation": llm_analysis.get("home_motivation", ""),
            "away_motivation": llm_analysis.get("away_motivation", ""),
            "key_context_factors": llm_analysis.get("key_context_factors", []),
            "tactical_context": llm_analysis.get("tactical_context", ""),
            "context_data_source": context_data_source,
            "context_data_warnings": warnings,
        }

    async def _resolve_ids(self, api, data):
        home_id = data.get("home_team_id")
        away_id = data.get("away_team_id")
        fixture = data.get("fixture")
        home_team = data.get("home_team_data")
        away_team = data.get("away_team_data")

        if not home_team or not away_team:
            home_search = self._sanitize(data.get("team_home") or "")
            away_search = self._sanitize(data.get("team_away") or "")
            home_results = await api.search_teams(home_search)
            away_results = await api.search_teams(away_search)
            if not home_team and home_results:
                home_team = home_results[0]
            if not away_team and away_results:
                away_team = away_results[0]

        if home_team:
            home_id = home_team.get("team", {}).get("id")
        if away_team:
            away_id = away_team.get("team", {}).get("id")

        if home_id and away_id and not fixture:
            fixtures = await api.get_fixtures(team_id=home_id, next_n=20)
            for candidate in fixtures:
                ids = {
                    candidate.get("teams", {}).get("home", {}).get("id"),
                    candidate.get("teams", {}).get("away", {}).get("id"),
                }
                if home_id in ids and away_id in ids:
                    fixture = candidate
                    break

        return home_id, away_id, fixture

    async def _analyze_context_with_llm(
        self,
        context,
        standings,
        home_stats,
        away_stats,
        league_info,
        is_rivalry,
        rivalry_name,
        round_name,
    ):
        home = context.get("team_home", "Unknown")
        away = context.get("team_away", "Unknown")

        if not standings and not home_stats and not away_stats and not league_info:
            return {}

        prompt_parts = [f"Match: {home} vs {away}"]
        prompt_parts.append(f"League: {league_info.get('name', 'Unknown')}")
        prompt_parts.append(f"Round: {round_name or 'Unknown'}")
        prompt_parts.append(f"Is Rivalry: {is_rivalry} ({rivalry_name or 'N/A'})")

        if standings:
            prompt_parts.append("\n--- Standings ---")
            if standings.get("home"):
                h = standings["home"]
                prompt_parts.append(
                    f"{home}: Position {h.get('rank')}/{h.get('total_teams')} | {h.get('points')} pts | Form: {h.get('form', 'N/A')}"
                )
            if standings.get("away"):
                a = standings["away"]
                prompt_parts.append(
                    f"{away}: Position {a.get('rank')}/{a.get('total_teams')} | {a.get('points')} pts | Form: {a.get('form', 'N/A')}"
                )

        prompt = "\n".join(prompt_parts)
        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=CONTEXT_SYSTEM_PROMPT, user_message=prompt, temperature=0.4
        )

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            self.logger.warning("Failed to parse context LLM response")
            return {}

    @staticmethod
    def _parse_standings(raw_standings, home_id, away_id):
        result = {}
        for entry in raw_standings:
            league = entry.get("league", {})
            for group_standings in league.get("standings", []):
                total_teams = len(group_standings)
                for team_standing in group_standings:
                    tid = team_standing.get("team", {}).get("id")
                    if tid == home_id:
                        result["home"] = {**team_standing, "total_teams": total_teams}
                    elif tid == away_id:
                        result["away"] = {**team_standing, "total_teams": total_teams}
        return result

    @staticmethod
    def _sanitize(name):
        nfkd = unicodedata.normalize("NFKD", name)
        ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", ascii_only)
        return re.sub(r"\s+", " ", clean).strip()
