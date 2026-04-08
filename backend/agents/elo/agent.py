"""
Sports AI — ELO Agent
Calculates dynamic ELO ratings with LLM interpretation.
"""

import json
from typing import Dict, Any

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext
from backend.llm.llm_router import get_llm_router


LEAGUE_BASE_ELO = {
    "Premier League": 1700,
    "La Liga": 1680,
    "Serie A": 1650,
    "Bundesliga": 1660,
    "Ligue 1": 1620,
    "Eredivisie": 1600,
    "Primeira Liga": 1610,
    "Liga Portugal": 1610,
    "Super Lig": 1580,
    "Belgian Pro League": 1570,
    "Scottish Premiership": 1550,
    "Champions League": 1750,
    "Copa Libertadores": 1680,
    "Brasileirão": 1630,
    "Liga MX": 1580,
    "MLS": 1560,
}
DEFAULT_BASE_ELO = 1550
K_FACTOR = 32

ELO_SYSTEM_PROMPT = """Eres un analista cuantitativo deportivo experto en sistemas de rating ELO.

Devuelve ÚNICAMENTE un objeto JSON:
{
  "elo_narrative": "2-3 líneas interpretando la diferencia de ELO",
  "competitive_gap": "imperceptible/leve/moderado/significativo/abismal",
  "elo_trend_home": "en ascenso/estable/en descenso",
  "elo_trend_away": "en ascenso/estable/en descenso",
  "elo_reliability": "alta/media/baja — justificación breve"
}"""


class EloAgent(BaseAgent):
    name = "EloAgent"
    is_critical = False
    timeout_seconds = 60.0

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        home_stats = ctx.data.get("home_stats", {})
        away_stats = ctx.data.get("away_stats", {})
        league = ctx.data.get("league_name", "")
        home_results = ctx.data.get("home_results", [])
        away_results = ctx.data.get("away_results", [])

        base_elo = LEAGUE_BASE_ELO.get(league, DEFAULT_BASE_ELO)
        home_elo = base_elo + self._elo_from_form(home_stats)
        away_elo = base_elo + self._elo_from_form(away_stats)

        home_elo = self._adjust_elo_from_results(home_elo, home_results, True)
        away_elo = self._adjust_elo_from_results(away_elo, away_results, False)

        elo_diff = home_elo - away_elo
        expected_home = 1.0 / (1.0 + 10 ** (-elo_diff / 400))
        expected_away = 1.0 - expected_home

        llm_analysis = await self._interpret_elo_with_llm(
            ctx.data,
            home_elo,
            away_elo,
            elo_diff,
            expected_home,
            expected_away,
            home_stats,
            away_stats,
        )

        return {
            "home_elo": round(home_elo, 1),
            "away_elo": round(away_elo, 1),
            "elo_difference": round(elo_diff, 1),
            "elo_expected_home": round(expected_home, 4),
            "elo_expected_away": round(expected_away, 4),
            "elo_narrative": llm_analysis.get("elo_narrative", ""),
            "competitive_gap": llm_analysis.get("competitive_gap", ""),
            "elo_trend_home": llm_analysis.get("elo_trend_home", ""),
            "elo_trend_away": llm_analysis.get("elo_trend_away", ""),
            "elo_reliability": llm_analysis.get("elo_reliability", ""),
        }

    async def _interpret_elo_with_llm(
        self,
        context,
        home_elo,
        away_elo,
        elo_diff,
        expected_home,
        expected_away,
        home_stats,
        away_stats,
    ):
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")
        league = context.get("league_name", "Unknown")
        prompt = f"Match: {home} vs {away} ({league})\n\nELO Ratings:\n  {home}: {home_elo:.1f}\n  {away}: {away_elo:.1f}\n  Difference: {elo_diff:+.1f}\n\nExpected Win Probabilities:\n  {home}: {expected_home:.1%}\n  {away}: {expected_away:.1%}\n\nForm:\n  {home}: {home_stats.get('form_score', 50)}/100\n  {away}: {away_stats.get('form_score', 50)}/100"
        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=ELO_SYSTEM_PROMPT, user_message=prompt, temperature=0.3
        )
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            return {}

    @staticmethod
    def _elo_from_form(stats: Dict) -> float:
        form = stats.get("form_score", 50.0)
        attack = stats.get("attack_rating", 50.0)
        defense = stats.get("defense_rating", 50.0)
        return (form - 50) * 2 + (attack - 50) * 0.5 + (defense - 50) * 0.5

    @staticmethod
    def _adjust_elo_from_results(elo: float, results: list, is_home: bool) -> float:
        for i, match in enumerate(results[:5]):
            weight = K_FACTOR * (0.8**i)
            gf = match.get("goals_home", 0) if is_home else match.get("goals_away", 0)
            ga = match.get("goals_away", 0) if is_home else match.get("goals_home", 0)
            if gf > ga:
                elo += weight * 0.3
            elif gf < ga:
                elo -= weight * 0.3
            elo += (gf - ga) * weight * 0.05
        return elo
