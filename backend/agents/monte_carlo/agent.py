"""
Sports AI — Monte Carlo Agent
Runs 50,000 match simulations with LLM interpretation.
"""

import json
from typing import Dict, Any

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext
from backend.services.simulation_service import SimulationService
from backend.llm.llm_router import get_llm_router


MC_SYSTEM_PROMPT = """Eres un analista cuantitativo especializado en simulaciones Monte Carlo aplicadas al fútbol.

Devuelve ÚNICAMENTE un objeto JSON:
{
  "mc_narrative": "3-4 líneas interpretando los resultados de la simulación",
  "simulation_confidence": "alta/media/baja — qué tan convergentes son los resultados",
  "volatility_assessment": "baja/media/alta — qué tan dispersos están los resultados",
  "goal_scoring_profile": "descripción del perfil de goles del partido",
  "key_simulation_insights": ["insight1", "insight2", "insight3"],
  "extreme_scenarios": "probabilidad y descripción de resultados extremos"
}"""


class MonteCarloAgent(BaseAgent):
    name = "MonteCarloAgent"
    is_critical = False
    timeout_seconds = 60.0

    def __init__(self):
        super().__init__()
        self.sim = SimulationService()

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        lambda_home = ctx.data.get("expected_goals_home", 1.5)
        lambda_away = ctx.data.get("expected_goals_away", 1.1)

        result = self.sim.simulate_match(lambda_home, lambda_away)
        llm_analysis = await self._interpret_mc_with_llm(
            ctx.data, result, lambda_home, lambda_away
        )

        return {
            "mc_simulations": result.simulations,
            "mc_home_win": result.home_win_pct,
            "mc_draw": result.draw_pct,
            "mc_away_win": result.away_win_pct,
            "mc_avg_goals_home": result.avg_goals_home,
            "mc_avg_goals_away": result.avg_goals_away,
            "mc_most_likely_score": result.most_likely_score,
            "mc_goal_distribution": result.goal_distribution,
            "mc_score_distribution": [
                s.model_dump() for s in result.score_distribution[:15]
            ],
            "mc_narrative": llm_analysis.get("mc_narrative", ""),
            "simulation_confidence": llm_analysis.get("simulation_confidence", ""),
            "volatility_assessment": llm_analysis.get("volatility_assessment", ""),
            "goal_scoring_profile": llm_analysis.get("goal_scoring_profile", ""),
            "key_simulation_insights": llm_analysis.get("key_simulation_insights", []),
            "extreme_scenarios": llm_analysis.get("extreme_scenarios", ""),
        }

    async def _interpret_mc_with_llm(self, context, result, lambda_home, lambda_away):
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")
        scores_text = "\n".join(
            [
                f"  {s.home_goals}-{s.away_goals}: {s.probability:.1%}"
                for s in result.score_distribution[:10]
            ]
        )
        goal_dist_text = "\n".join(
            [
                f"  {k} total goals: {v:.1%}"
                for k, v in sorted(
                    result.goal_distribution.items(), key=lambda x: int(x[0])
                )
            ]
        )
        prompt = f"Match: {home} vs {away}\nSimulations: {result.simulations:,}\n\nResults:\n  {home}: {result.home_win_pct:.1f}%\n  Draw: {result.draw_pct:.1f}%\n  {away}: {result.away_win_pct:.1f}%\n\nAverage Goals: {result.avg_goals_home:.2f} - {result.avg_goals_away:.2f}\nMost Likely Score: {result.most_likely_score}\n\nTop 10 Scores:\n{scores_text}\n\nTotal Goals Distribution:\n{goal_dist_text}\n\nInput λ: {home}={lambda_home:.2f}, {away}={lambda_away:.2f}"
        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=MC_SYSTEM_PROMPT, user_message=prompt, temperature=0.3
        )
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            return {}
