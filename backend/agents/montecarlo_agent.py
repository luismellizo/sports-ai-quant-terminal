"""
Sports AI — Agent 11: Monte Carlo Simulation Agent
Runs 50,000 match simulations using Poisson distribution.
Uses DeepSeek to interpret the simulation results.
"""

import json
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.services.simulation_service import SimulationService
from backend.llm.llm_router import get_llm_router

MC_SYSTEM_PROMPT = """Eres un analista cuantitativo especializado en simulaciones Monte Carlo aplicadas al fútbol. Recibirás los resultados de 50,000 simulaciones REALES de un partido.

Genera un análisis de las simulaciones:
1. Interpreta las probabilidades de victoria/empate/derrota
2. Analiza la distribución de goles y qué dice sobre la naturaleza del partido
3. Identifica el marcador más probable y su significancia
4. Evalúa la volatilidad/incertidumbre del resultado
5. Detecta escenarios de alto scoring vs low scoring

Devuelve ÚNICAMENTE un objeto JSON:
{
  "mc_narrative": "3-4 líneas interpretando los resultados de la simulación con datos específicos",
  "simulation_confidence": "alta/media/baja — qué tan convergentes son los resultados",
  "volatility_assessment": "baja/media/alta — qué tan dispersos están los resultados",
  "goal_scoring_profile": "descripción del perfil de goles del partido",
  "key_simulation_insights": ["insight1", "insight2", "insight3"],
  "extreme_scenarios": "probabilidad y descripción de resultados extremos (goleadas, 0-0, etc.)"
}"""


class MonteCarloAgent(BaseAgent):
    """Runs Monte Carlo match simulations with LLM interpretation."""

    def __init__(self):
        super().__init__()
        self.sim = SimulationService()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        lambda_home = context.get("expected_goals_home", 1.5)
        lambda_away = context.get("expected_goals_away", 1.1)

        # Run simulation
        result = self.sim.simulate_match(lambda_home, lambda_away)

        # ── DeepSeek: simulation interpretation ──
        llm_analysis = await self._interpret_mc_with_llm(
            context, result, lambda_home, lambda_away
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
            "mc_score_distribution": [s.model_dump() for s in result.score_distribution[:15]],
            "mc_narrative": llm_analysis.get("mc_narrative", ""),
            "simulation_confidence": llm_analysis.get("simulation_confidence", ""),
            "volatility_assessment": llm_analysis.get("volatility_assessment", ""),
            "goal_scoring_profile": llm_analysis.get("goal_scoring_profile", ""),
            "key_simulation_insights": llm_analysis.get("key_simulation_insights", []),
            "extreme_scenarios": llm_analysis.get("extreme_scenarios", ""),
        }

    async def _interpret_mc_with_llm(self, context, result, lambda_home, lambda_away) -> Dict:
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")

        # Top scores
        scores_text = "\n".join([
            f"  {s.home_goals}-{s.away_goals}: {s.probability:.1%}"
            for s in result.score_distribution[:10]
        ])

        # Goal distribution
        goal_dist_text = "\n".join([
            f"  {k} total goals: {v:.1%}"
            for k, v in sorted(result.goal_distribution.items(), key=lambda x: int(x[0]))
        ])

        prompt = (
            f"Match: {home} vs {away}\n"
            f"Simulations: {result.simulations:,}\n\n"
            f"Results:\n"
            f"  {home} wins: {result.home_win_pct:.1f}%\n"
            f"  Draw: {result.draw_pct:.1f}%\n"
            f"  {away} wins: {result.away_win_pct:.1f}%\n\n"
            f"Average Goals: {result.avg_goals_home:.2f} - {result.avg_goals_away:.2f} "
            f"(Total: {result.avg_goals_home + result.avg_goals_away:.2f})\n"
            f"Most Likely Score: {result.most_likely_score}\n\n"
            f"Top 10 Score Probabilities:\n{scores_text}\n\n"
            f"Total Goals Distribution:\n{goal_dist_text}\n\n"
            f"Input λ (xG): {home}={lambda_home:.2f}, {away}={lambda_away:.2f}"
        )

        llm = get_llm_router()
        response = await llm.chat(system_prompt=MC_SYSTEM_PROMPT, user_message=prompt, temperature=0.3)

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            self.logger.warning("Failed to parse MC LLM response")
            return {}
