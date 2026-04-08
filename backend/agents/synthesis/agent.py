"""
Sports AI — Synthesis Agent
Generates the final Executive Summary from ALL pipeline data.
"""

import json
from typing import Dict, Any

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext
from backend.llm.llm_router import get_llm_router


SYNTHESIS_SYSTEM_PROMPT = """Eres el Director de Análisis de un fondo de trading deportivo cuántico de élite.

Devuelve ÚNICAMENTE un objeto JSON:
{
  "executive_summary": "párrafo de 5-8 líneas con el resumen ejecutivo completo",
  "verdict": "una línea con el veredicto claro y nivel de confianza",
  "tactical_synthesis": "3-4 líneas sintetizando el análisis táctico",
  "critical_data_points": ["dato1 con número", "dato2 con número", "dato3 con número"],
  "decisive_factors": ["factor1", "factor2", "factor3"],
  "risk_warnings": ["riesgo1", "riesgo2"],
  "final_recommendation": "2-3 líneas con la recomendación final profesional",
  "conviction_level": "muy_alta/alta/media/baja/muy_baja"
}"""


class SynthesisAgent(BaseAgent):
    name = "SynthesisAgent"
    is_critical = False
    timeout_seconds = 60.0

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        home = ctx.data.get("team_home", "Home")
        away = ctx.data.get("team_away", "Away")
        league = ctx.data.get("league_name", "Unknown")

        prompt = self._build_synthesis_prompt(ctx.data, home, away, league)

        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=SYNTHESIS_SYSTEM_PROMPT,
            user_message=prompt,
            temperature=0.4,
            max_tokens=4000,
        )

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            analysis = json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            analysis = {}

        return {
            "executive_summary": analysis.get("executive_summary", ""),
            "verdict": analysis.get("verdict", ""),
            "tactical_synthesis": analysis.get("tactical_synthesis", ""),
            "critical_data_points": analysis.get("critical_data_points", []),
            "decisive_factors": analysis.get("decisive_factors", []),
            "risk_warnings": analysis.get("risk_warnings", []),
            "final_recommendation": analysis.get("final_recommendation", ""),
            "conviction_level": analysis.get("conviction_level", ""),
        }

    def _build_synthesis_prompt(self, ctx, home, away, league) -> str:
        parts = [
            f"═══ ANÁLISIS COMPLETO: {home} vs {away} ({league}) ═══\n",
            f"── CONTEXTO ──",
            f"Round: {ctx.get('round', 'N/A')} | Rivalry: {ctx.get('rivalry_name', 'No')} | Importance: {ctx.get('match_importance', 0.5):.2f}",
            f"Context: {ctx.get('context_narrative', 'N/A')}",
            f"\n── HISTORIAL ──",
            f"Home: W{ctx.get('home_stats', {}).get('wins_last_5', 0)}-D{ctx.get('home_stats', {}).get('draws_last_5', 0)}-L{ctx.get('home_stats', {}).get('losses_last_5', 0)}",
            f"Away: W{ctx.get('away_stats', {}).get('wins_last_5', 0)}-D{ctx.get('away_stats', {}).get('draws_last_5', 0)}-L{ctx.get('away_stats', {}).get('losses_last_5', 0)}",
            f"H2H: {ctx.get('h2h_summary', {})} | Upset Risk: {ctx.get('upset_risk', 'N/A')}",
            f"\n── LINEUPS ──",
            f"Home Injuries: {ctx.get('home_injury_count', 0)} | Away Injuries: {ctx.get('away_injury_count', 0)}",
            f"Tactical: {ctx.get('tactical_advantage', 'N/A')}",
            f"\n── SENTIMENT ──",
            f"Home: {ctx.get('sentiment_home', 0):.2f} | Away: {ctx.get('sentiment_away', 0):.2f}",
            f"\n── ELO ──",
            f"{home}: {ctx.get('home_elo', 'N/A')} | {away}: {ctx.get('away_elo', 'N/A')} | Diff: {ctx.get('elo_difference', 0):+.1f}",
            f"\n── POISSON ──",
            f"xG: {home}={ctx.get('expected_goals_home', 0):.2f} | {away}={ctx.get('expected_goals_away', 0):.2f}",
            f"Probs: H={ctx.get('poisson_home_win', 0):.1%} D={ctx.get('poisson_draw', 0):.1%} A={ctx.get('poisson_away_win', 0):.1%}",
            f"\n── ML ──",
            f"Probs: H={ctx.get('ml_home_win', 0):.1%} D={ctx.get('ml_draw', 0):.1%} A={ctx.get('ml_away_win', 0):.1%}",
            f"Model Agreement: {ctx.get('model_agreement', 'N/A')}",
            f"\n── MONTE CARLO ──",
            f"MC: H={ctx.get('mc_home_win', 0):.1f}% D={ctx.get('mc_draw', 0):.1f}% A={ctx.get('mc_away_win', 0):.1f}%",
            f"Most Likely Score: {ctx.get('mc_most_likely_score', 'N/A')}",
            f"\n── MARKET EDGE ──",
            f"Best Edge: {ctx.get('best_edge', {})}",
            f"\n── RISK ──",
            f"Best Bet: {ctx.get('best_bet', {})}",
            f"Professional Verdict: {ctx.get('professional_verdict', 'N/A')}",
        ]
        return "\n".join(parts)
