"""
Sports AI — Poisson Agent
Generates Poisson-based goal predictions with LLM interpretation.
"""

import json
from typing import Dict, Any

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext
from backend.services.simulation_service import SimulationService
from backend.llm.llm_router import get_llm_router


POISSON_SYSTEM_PROMPT = """Eres un estadístico deportivo experto en modelos de Poisson aplicados al fútbol.

Devuelve ÚNICAMENTE un objeto JSON:
{
  "poisson_narrative": "3-4 líneas interpretando el modelo probabilístico",
  "goals_expectation": "descripción del perfil de goles esperado",
  "most_likely_scenarios": "descripción de los 3 escenarios más probables",
  "over_under_analysis": "análisis de Over/Under 2.5 con probabilidad",
  "btts_analysis": "análisis de ambos equipos marcan (BTTS)",
  "surprise_factor": "bajo/medio/alto — probabilidad de resultado inesperado"
}"""


class PoissonAgent(BaseAgent):
    name = "PoissonAgent"
    is_critical = False
    timeout_seconds = 60.0

    def __init__(self):
        super().__init__()
        self.sim = SimulationService()

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        home_stats = ctx.data.get("home_stats", {})
        away_stats = ctx.data.get("away_stats", {})

        lambda_home, lambda_away = self.sim.calculate_expected_goals(
            attack_rating_home=home_stats.get("attack_rating", 50.0),
            defense_rating_away=away_stats.get("defense_rating", 50.0),
            attack_rating_away=away_stats.get("attack_rating", 50.0),
            defense_rating_home=home_stats.get("defense_rating", 50.0),
        )

        score_matrix = self.sim.poisson_score_matrix(lambda_home, lambda_away)

        home_win_prob = sum(
            s.probability for s in score_matrix if s.home_goals > s.away_goals
        )
        draw_prob = sum(
            s.probability for s in score_matrix if s.home_goals == s.away_goals
        )
        away_win_prob = sum(
            s.probability for s in score_matrix if s.home_goals < s.away_goals
        )
        over_25_prob = sum(
            s.probability for s in score_matrix if (s.home_goals + s.away_goals) > 2
        )
        btts_prob = sum(
            s.probability for s in score_matrix if s.home_goals > 0 and s.away_goals > 0
        )

        llm_analysis = await self._interpret_poisson_with_llm(
            ctx.data,
            lambda_home,
            lambda_away,
            home_win_prob,
            draw_prob,
            away_win_prob,
            over_25_prob,
            btts_prob,
            score_matrix[:10],
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
        self,
        context,
        lambda_home,
        lambda_away,
        home_win_prob,
        draw_prob,
        away_win_prob,
        over_25_prob,
        btts_prob,
        top_scores,
    ):
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")
        scores_text = "\n".join(
            [
                f"  {s.home_goals}-{s.away_goals}: {s.probability:.1%}"
                for s in top_scores
            ]
        )
        prompt = f"Match: {home} vs {away}\n\nExpected Goals (λ):\n  {home}: {lambda_home:.2f} xG\n  {away}: {lambda_away:.2f} xG\n\nOutcome Probabilities:\n  {home}: {home_win_prob:.1%}\n  Draw: {draw_prob:.1%}\n  {away}: {away_win_prob:.1%}\n\nTop 10 Scores:\n{scores_text}\n\nOver 2.5: ~{over_25_prob:.1%}\nBTTS: ~{btts_prob:.1%}"
        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=POISSON_SYSTEM_PROMPT, user_message=prompt, temperature=0.3
        )
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            return {}
