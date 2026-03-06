"""
Sports AI — Agent 8: ELO Rating Agent
Calculates dynamic ELO ratings and uses DeepSeek to interpret the competitive gap.
"""

import json
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.llm.llm_router import get_llm_router

# Base ELO ratings for known leagues (defaults)
LEAGUE_BASE_ELO = {
    "Premier League": 1700, "La Liga": 1680, "Serie A": 1650,
    "Bundesliga": 1660, "Ligue 1": 1620, "Eredivisie": 1600,
    "Primeira Liga": 1610, "Liga Portugal": 1610, "Super Lig": 1580,
    "Belgian Pro League": 1570, "Scottish Premiership": 1550,
    "Champions League": 1750, "Europa League": 1650, "Conference League": 1600,
    "Liga Profesional Argentina": 1620, "Primera División": 1620,
    "Brasileirão": 1630, "Liga BetPlay": 1560, "Liga 1": 1540,
    "Primera A": 1560, "Liga MX": 1580, "Copa Libertadores": 1680,
    "Copa Sudamericana": 1600, "MLS": 1560, "J1 League": 1560,
    "K League 1": 1550, "Saudi Pro League": 1570,
}

DEFAULT_BASE_ELO = 1550
K_FACTOR = 32

ELO_SYSTEM_PROMPT = """Eres un analista cuantitativo deportivo experto en sistemas de rating ELO. Recibirás los ratings ELO calculados para ambos equipos basados en sus resultados reales.

Interpreta los datos:
1. Qué significa la diferencia de ELO en términos de ventaja competitiva
2. Cómo los resultados recientes han movido el ELO de cada equipo
3. Si el ELO sugiere un partido equilibrado o desequilibrado
4. Probabilidades implícitas del ELO y qué tan confiables son

Devuelve ÚNICAMENTE un objeto JSON:
{
  "elo_narrative": "2-3 líneas interpretando la diferencia de ELO en contexto competitivo real",
  "competitive_gap": "imperceptible/leve/moderado/significativo/abismal",
  "elo_trend_home": "en ascenso/estable/en descenso",
  "elo_trend_away": "en ascenso/estable/en descenso",
  "elo_reliability": "alta/media/baja — justificación breve"
}"""


class EloAgent(BaseAgent):
    """Calculates dynamic ELO ratings with LLM interpretation."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        home_stats = context.get("home_stats", {})
        away_stats = context.get("away_stats", {})
        league = context.get("league_name", "")
        home_results = context.get("home_results", [])
        away_results = context.get("away_results", [])

        # Starting ELO based on league
        base_elo = LEAGUE_BASE_ELO.get(league, DEFAULT_BASE_ELO)
        home_elo = base_elo + self._elo_from_form(home_stats)
        away_elo = base_elo + self._elo_from_form(away_stats)

        # Adjust based on recent results
        home_elo = self._adjust_elo_from_results(home_elo, home_results, True)
        away_elo = self._adjust_elo_from_results(away_elo, away_results, False)

        # Calculate expected results
        elo_diff = home_elo - away_elo
        expected_home = 1.0 / (1.0 + 10 ** (-elo_diff / 400))
        expected_away = 1.0 - expected_home

        # ── DeepSeek: ELO interpretation ──
        llm_analysis = await self._interpret_elo_with_llm(
            context, home_elo, away_elo, elo_diff,
            expected_home, expected_away, home_stats, away_stats
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
        self, context, home_elo, away_elo, elo_diff,
        expected_home, expected_away, home_stats, away_stats
    ) -> Dict:
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")
        league = context.get("league_name", "Unknown")

        prompt = (
            f"Match: {home} vs {away} ({league})\n\n"
            f"ELO Ratings:\n"
            f"  {home}: {home_elo:.1f}\n"
            f"  {away}: {away_elo:.1f}\n"
            f"  Difference: {elo_diff:+.1f} (favor {'local' if elo_diff > 0 else 'visitante'})\n\n"
            f"Expected Win Probabilities (ELO-based):\n"
            f"  {home}: {expected_home:.1%}\n"
            f"  {away}: {expected_away:.1%}\n\n"
            f"Form Scores:\n"
            f"  {home}: {home_stats.get('form_score', 50)}/100 | Momentum: {home_stats.get('momentum', 0)}\n"
            f"  {away}: {away_stats.get('form_score', 50)}/100 | Momentum: {away_stats.get('momentum', 0)}\n\n"
            f"Attack/Defense Ratings:\n"
            f"  {home}: ATK {home_stats.get('attack_rating', 50)}/100 | DEF {home_stats.get('defense_rating', 50)}/100\n"
            f"  {away}: ATK {away_stats.get('attack_rating', 50)}/100 | DEF {away_stats.get('defense_rating', 50)}/100"
        )

        llm = get_llm_router()
        response = await llm.chat(system_prompt=ELO_SYSTEM_PROMPT, user_message=prompt, temperature=0.3)

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            self.logger.warning("Failed to parse ELO LLM response")
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
            weight = K_FACTOR * (0.8 ** i)
            gf = match.get("goals_home", 0) if is_home else match.get("goals_away", 0)
            ga = match.get("goals_away", 0) if is_home else match.get("goals_home", 0)
            if gf > ga:
                elo += weight * 0.3
            elif gf < ga:
                elo -= weight * 0.3
            elo += (gf - ga) * weight * 0.05
        return elo
