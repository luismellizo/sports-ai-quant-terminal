"""
Sports AI — Agent 9: Poisson Goal Model Agent
Calculates goal distribution using Poisson statistical model.
Uses DeepSeek to interpret the probabilistic landscape.
"""

import json
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.services.simulation_service import SimulationService
from backend.llm.llm_router import get_llm_router

POISSON_SYSTEM_PROMPT = """Eres un estadístico deportivo experto en modelos de Poisson aplicados al fútbol. Recibirás datos REALES de un modelo de distribución de goles.

Genera un análisis técnico pero comprensible:
1. Interpreta los goles esperados (xG) de cada equipo y qué implican
2. Analiza los escenarios de marcador más probables y sus probabilidades
3. Identifica si es un partido que se perfila con muchos o pocos goles
4. Evalúa la probabilidad de marcadores extremos o sorpresas
5. Relaciona el modelo con mercados de apuestas (Over/Under, BTTS)

Devuelve ÚNICAMENTE un objeto JSON:
{
  "poisson_narrative": "3-4 líneas interpretando el modelo probabilístico con datos específicos",
  "goals_expectation": "descripción del perfil de goles esperado",
  "most_likely_scenarios": "descripción de los 3 escenarios más probables",
  "over_under_analysis": "análisis de Over/Under 2.5 con probabilidad",
  "btts_analysis": "análisis de ambos equipos marcan (Both Teams To Score)",
  "surprise_factor": "bajo/medio/alto — probabilidad de resultado inesperado"
}"""


class PoissonAgent(BaseAgent):
    """Generates Poisson-based goal predictions with LLM interpretation."""

    def __init__(self):
        super().__init__()
        self.sim = SimulationService()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        home_stats = context.get("home_stats", {})
        away_stats = context.get("away_stats", {})

        # Calculate expected goals
        lambda_home, lambda_away = self.sim.calculate_expected_goals(
            attack_rating_home=home_stats.get("attack_rating", 50.0),
            defense_rating_away=away_stats.get("defense_rating", 50.0),
            attack_rating_away=away_stats.get("attack_rating", 50.0),
            defense_rating_home=home_stats.get("defense_rating", 50.0),
        )

        # Generate score probability matrix
        score_matrix = self.sim.poisson_score_matrix(lambda_home, lambda_away)

        # Calculate outcome probabilities from matrix
        home_win_prob = sum(s.probability for s in score_matrix if s.home_goals > s.away_goals)
        draw_prob = sum(s.probability for s in score_matrix if s.home_goals == s.away_goals)
        away_win_prob = sum(s.probability for s in score_matrix if s.home_goals < s.away_goals)
        over_25_prob = sum(s.probability for s in score_matrix if (s.home_goals + s.away_goals) > 2)
        btts_prob = sum(s.probability for s in score_matrix if s.home_goals > 0 and s.away_goals > 0)

        # ── DeepSeek: probabilistic interpretation ──
        llm_analysis = await self._interpret_poisson_with_llm(
            context, lambda_home, lambda_away,
            home_win_prob, draw_prob, away_win_prob, over_25_prob, btts_prob, score_matrix[:10]
        )

        return {
            "expected_goals_home": lambda_home,
            "expected_goals_away": lambda_away,
            "poisson_home_win": round(home_win_prob, 4),
            "poisson_draw": round(draw_prob, 4),
            "poisson_away_win": round(away_win_prob, 4),
            "score_matrix": [s.model_dump() for s in score_matrix[:20]],
            "poisson_over_25": round(over_25_prob, 4),
            "poisson_btts": round(btts_prob, 4),
            "poisson_narrative": llm_analysis.get("poisson_narrative", ""),
            "goals_expectation": llm_analysis.get("goals_expectation", ""),
            "most_likely_scenarios": llm_analysis.get("most_likely_scenarios", ""),
            "over_under_analysis": llm_analysis.get("over_under_analysis", ""),
            "btts_analysis": llm_analysis.get("btts_analysis", ""),
            "surprise_factor": llm_analysis.get("surprise_factor", ""),
        }

    async def _interpret_poisson_with_llm(
        self, context, lambda_home, lambda_away,
        home_win_prob, draw_prob, away_win_prob, over_25_prob, btts_prob, top_scores
    ) -> Dict:
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")

        scores_text = "\n".join([
            f"  {s.home_goals}-{s.away_goals}: {s.probability:.1%}"
            for s in top_scores
        ])

        prompt = (
            f"Match: {home} vs {away}\n\n"
            f"Expected Goals (Poisson λ):\n"
            f"  {home}: {lambda_home:.2f} xG\n"
            f"  {away}: {lambda_away:.2f} xG\n"
            f"  Total xG: {lambda_home + lambda_away:.2f}\n\n"
            f"Outcome Probabilities:\n"
            f"  {home} wins: {home_win_prob:.1%}\n"
            f"  Draw: {draw_prob:.1%}\n"
            f"  {away} wins: {away_win_prob:.1%}\n\n"
            f"Top 10 Most Likely Scores:\n{scores_text}\n\n"
            f"Market-relevant:\n"
            f"  Over 2.5 goals: ~{over_25_prob:.1%}\n"
            f"  BTTS (Both Teams To Score): ~{btts_prob:.1%}"
        )

        llm = get_llm_router()
        response = await llm.chat(system_prompt=POISSON_SYSTEM_PROMPT, user_message=prompt, temperature=0.3)

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            self.logger.warning("Failed to parse Poisson LLM response")
            return {}
