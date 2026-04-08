"""
Sports AI — History Agent
Analyzes historical match data with real API data and LLM narrative.
"""

import asyncio
import json
from typing import Dict, Any, List

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext, AgentStatus
from backend.services.api_football_client import get_api_football_client
from backend.services.feature_engineering import FeatureEngineeringService
from backend.llm.llm_router import get_llm_router


HISTORY_SYSTEM_PROMPT = """Eres un analista deportivo experto en datos históricos de fútbol. Recibirás datos REALES de partidos recientes y enfrentamientos directos (H2H).

Devuelve ÚNICAMENTE un objeto JSON:
{
  "history_narrative": "párrafo de 4-6 líneas analizando el historial con datos específicos",
  "home_form_analysis": "2-3 líneas sobre la forma del local con resultados reales",
  "away_form_analysis": "2-3 líneas sobre la forma del visitante con resultados reales",
  "h2h_analysis": "2-3 líneas sobre el historial directo con datos específicos",
  "key_historical_patterns": ["patrón1", "patrón2", "patrón3"],
  "goals_trend": "descripción de la tendencia de goles en los partidos recientes",
  "upset_risk": "bajo/medio/alto — basado en datos históricos con justificación"
}"""


class HistoryAgent(BaseAgent):
    name = "HistoryAgent"
    is_critical = False
    timeout_seconds = 180.0

    def __init__(self):
        super().__init__()
        self.fe = FeatureEngineeringService()

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        api = get_api_football_client()
        home_id = ctx.data.get("home_team_id")
        away_id = ctx.data.get("away_team_id")

        if not home_id or not away_id:
            return self._insufficient_data_stats(
                "No se pudieron identificar ambos equipos."
            )

        # Parallelize all 3 API calls
        home_last_20, away_last_20, h2h_response = await asyncio.gather(
            api.get_fixtures(team_id=home_id, last=20),
            api.get_fixtures(team_id=away_id, last=20),
            api.get_h2h_stats(home_id, away_id, last=20),
        )

        if not home_last_20 and not away_last_20:
            return self._insufficient_data_stats(
                "No hay histórico reciente disponible."
            )

        home_results = self._parse_results(home_last_20, home_id)
        away_results = self._parse_results(away_last_20, away_id)
        h2h_results = self._parse_results(h2h_response.get("fixtures", []), home_id)

        home_stats = self._calculate_team_stats(home_results, is_home=True)
        away_stats = self._calculate_team_stats(away_results, is_home=False)

        h2h_home_wins = sum(1 for r in h2h_results if r["goals_home"] > r["goals_away"])
        h2h_draws = sum(1 for r in h2h_results if r["goals_home"] == r["goals_away"])
        h2h_away_wins = len(h2h_results) - h2h_home_wins - h2h_draws

        h2h_summary = {
            "total_matches": len(h2h_results),
            "home_wins": h2h_home_wins,
            "draws": h2h_draws,
            "away_wins": h2h_away_wins,
        }

        h2h_enriched_stats = {
            "overall_record": h2h_response.get("overall_record", {}),
            "biggest_victory": h2h_response.get("biggest_victory", {}),
            "biggest_defeat": h2h_response.get("biggest_defeat", {}),
            "goals": h2h_response.get("goals", {})
        }

        llm_analysis = await self._analyze_history_with_llm(
            ctx.data,
            home_results,
            away_results,
            h2h_results,
            home_stats,
            away_stats,
            h2h_summary,
            h2h_enriched_stats,
        )

        return {
            "home_stats": home_stats,
            "away_stats": away_stats,
            "home_results": home_results[:5],
            "away_results": away_results[:5],
            "h2h_results": h2h_results,
            "h2h_summary": h2h_summary,
            "h2h_enriched_stats": h2h_enriched_stats,
            "history_narrative": llm_analysis.get("history_narrative", ""),
            "home_form_analysis": llm_analysis.get("home_form_analysis", ""),
            "away_form_analysis": llm_analysis.get("away_form_analysis", ""),
            "h2h_analysis": llm_analysis.get("h2h_analysis", ""),
            "key_historical_patterns": llm_analysis.get("key_historical_patterns", []),
            "goals_trend": llm_analysis.get("goals_trend", ""),
            "upset_risk": llm_analysis.get("upset_risk", ""),
            "history_data_source": "api"
            if home_last_20 and away_last_20
            else "partial_api",
            "history_data_available": True,
        }

    def _calculate_team_stats(self, results, is_home):
        if not results:
            return {
                "form_score": 50.0,
                "wins_last_5": 0,
                "draws_last_5": 0,
                "losses_last_5": 0,
                "goals_scored_last_5": 0,
                "goals_conceded_last_5": 0,
            }
        last5 = results[:5]
        if is_home:
            wins = sum(1 for r in last5 if r["goals_home"] > r["goals_away"])
            draws = sum(1 for r in last5 if r["goals_home"] == r["goals_away"])
            gf = sum(r["goals_home"] for r in last5)
            ga = sum(r["goals_away"] for r in last5)
        else:
            wins = sum(1 for r in last5 if r["goals_away"] > r["goals_home"])
            draws = sum(1 for r in last5 if r["goals_away"] == r["goals_home"])
            gf = sum(r["goals_away"] for r in last5)
            ga = sum(r["goals_home"] for r in last5)
        return {
            "form_score": self.fe.calculate_form_score(results[:5], is_home),
            "wins_last_5": wins,
            "draws_last_5": draws,
            "losses_last_5": 5 - wins - draws,
            "goals_scored_last_5": gf,
            "goals_conceded_last_5": ga,
        }

    async def _analyze_history_with_llm(
        self,
        context,
        home_results,
        away_results,
        h2h_results,
        home_stats,
        away_stats,
        h2h_summary,
        h2h_enriched_stats,
    ):
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")
        prompt_parts = [f"Match: {home} vs {away}\n--- {home} Last 5"]
        for i, r in enumerate(home_results[:5]):
            result = (
                "W"
                if r["goals_home"] > r["goals_away"]
                else ("D" if r["goals_home"] == r["goals_away"] else "L")
            )
            prompt_parts.append(
                f"{i + 1}. {r.get('home_team', '?')} {r['goals_home']}-{r['goals_away']} [{result}]"
            )
        prompt_parts.append(
            f"Stats: {home_stats['wins_last_5']}W-{home_stats['draws_last_5']}D-{home_stats['losses_last_5']}L"
        )
        prompt_parts.append(f"\n--- {away} Last 5")
        for i, r in enumerate(away_results[:5]):
            result = (
                "W"
                if r["goals_away"] > r["goals_home"]
                else ("D" if r["goals_away"] == r["goals_home"] else "L")
            )
            prompt_parts.append(
                f"{i + 1}. {r.get('home_team', '?')} {r['goals_home']}-{r['goals_away']} [{result}]"
            )
        prompt_parts.append(
            f"H2H Recent (Last 20): {h2h_summary['home_wins']}W-{h2h_summary['draws']}D-{h2h_summary['away_wins']}L"
        )
        
        try:
            overall = h2h_enriched_stats.get("overall_record", {}).get("total", {}).get("total", [])
            overall_str = ", ".join(f"{list(s.keys())[0]}: {list(s.values())[0]}" for s in overall if s)
            prompt_parts.append(f"H2H Overall History: {overall_str}")
        except Exception:
            pass
            
        try:
            vic = h2h_enriched_stats.get("biggest_victory", {})
            bg_vic = vic.get("team1", {}).get("match", {})
            if bg_vic:
                prompt_parts.append(f"Biggest {home} Win vs {away}: {bg_vic.get('team1_score')}-{bg_vic.get('team2_score')} in {bg_vic.get('date')}")
            bg_def = vic.get("team2", {}).get("match", {})
            if bg_def:
                prompt_parts.append(f"Biggest {away} Win vs {home}: {bg_def.get('team2_score')}-{bg_def.get('team1_score')} in {bg_def.get('date')}")
        except Exception:
            pass
            
        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=HISTORY_SYSTEM_PROMPT,
            user_message="\n".join(prompt_parts),
            temperature=0.4,
        )
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            return {}

    @staticmethod
    def _insufficient_data_stats(reason):
        neutral = {
            "form_score": 50.0,
            "wins_last_5": 0,
            "draws_last_5": 0,
            "losses_last_5": 0,
            "goals_scored_last_5": 0,
            "goals_conceded_last_5": 0,
        }
        return {
            "home_stats": neutral,
            "away_stats": neutral.copy(),
            "home_results": [],
            "away_results": [],
            "h2h_results": [],
            "h2h_summary": {
                "total_matches": 0,
                "home_wins": 0,
                "draws": 0,
                "away_wins": 0,
            },
            "h2h_enriched_stats": {},
            "history_narrative": f"Histórico no disponible: {reason}",
            "history_data_source": "missing",
            "history_data_available": False,
        }

    @staticmethod
    def _parse_results(fixtures, reference_team_id):
        results = []
        for f in fixtures:
            teams = f.get("teams", {})
            goals = f.get("goals", {})
            home_id = teams.get("home", {}).get("id")
            results.append(
                {
                    "fixture_id": f.get("fixture", {}).get("id"),
                    "date": f.get("fixture", {}).get("date"),
                    "goals_home": goals.get("home", 0) or 0,
                    "goals_away": goals.get("away", 0) or 0,
                    "is_home": home_id == reference_team_id,
                    "home_team": teams.get("home", {}).get("name"),
                    "away_team": teams.get("away", {}).get("name"),
                }
            )
        return results
