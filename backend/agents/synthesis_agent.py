"""
Sports AI — Agent 14: Synthesis Agent
The final brain of the pipeline: generates a comprehensive Executive Summary
using DeepSeek with ALL data from every previous agent.
"""

import json
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.llm.llm_router import get_llm_router

SYNTHESIS_SYSTEM_PROMPT = """Eres el Director de Análisis de un fondo de trading deportivo cuántico de élite. Recibirás TODOS los datos recopilados por 13 agentes especializados que han analizado un partido de fútbol.

Tu trabajo es generar el EXECUTIVE SUMMARY definitivo — el documento final que un trader profesional leería antes de tomar una decisión. NO repitas datos en bruto, INTERPRETA y SINTETIZA.

Estructura tu análisis:
1. **Veredicto** — Resultado más probable y nivel de confianza en una línea
2. **Análisis Táctico Integrado** — Síntesis de formaciones, lesiones, contexto competitivo
3. **Datos Duros** — Los 3-4 datos numéricos más relevantes (ELO, xG, MC, odds)
4. **Factores Clave** — Los 3 factores determinantes que decidirán este partido
5. **Riesgos** — Los 2-3 riesgos principales que podrían invalidar la predicción
6. **Recomendación Final** — Apuesta concreta, stake, y argumentación profesional

IMPORTANTE:
- Sé ESPECÍFICO con nombres de equipos, datos y cifras
- NO uses plantillas genéricas — cada partido debe tener un análisis ÚNICO
- Escribe como un analista profesional, no como un chatbot
- Si los datos son contradictorios, señálalo explícitamente

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
    """Generates the final Executive Summary from ALL pipeline data."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")
        league = context.get("league_name", "Unknown")

        # Build comprehensive prompt with ALL agent data
        prompt = self._build_synthesis_prompt(context, home, away, league)

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
            self.logger.warning("Failed to parse synthesis LLM response")
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

    def _build_synthesis_prompt(self, ctx: Dict, home: str, away: str, league: str) -> str:
        """Build a comprehensive prompt with data from ALL agents."""
        parts = [
            f"═══ ANÁLISIS COMPLETO: {home} vs {away} ({league}) ═══\n",

            # Agent 2: Context
            f"── CONTEXTO COMPETITIVO ──",
            f"Round: {ctx.get('round', 'N/A')}",
            f"Rivalry: {ctx.get('rivalry_name', 'No')}",
            f"Match Importance: {ctx.get('match_importance', 0.5):.2f}",
            f"Context Analysis: {ctx.get('context_narrative', 'N/A')}",
            f"Home Motivation: {ctx.get('home_motivation', 'N/A')}",
            f"Away Motivation: {ctx.get('away_motivation', 'N/A')}",
            f"Key Factors: {ctx.get('key_context_factors', [])}",

            # Agent 3: History
            f"\n── HISTORIAL ──",
            f"Home Stats: W{ctx.get('home_stats', {}).get('wins_last_5', 0)}-"
            f"D{ctx.get('home_stats', {}).get('draws_last_5', 0)}-"
            f"L{ctx.get('home_stats', {}).get('losses_last_5', 0)} (last 5)",
            f"Away Stats: W{ctx.get('away_stats', {}).get('wins_last_5', 0)}-"
            f"D{ctx.get('away_stats', {}).get('draws_last_5', 0)}-"
            f"L{ctx.get('away_stats', {}).get('losses_last_5', 0)} (last 5)",
            f"H2H: {ctx.get('h2h_summary', {})}",
            f"History Analysis: {ctx.get('history_narrative', 'N/A')}",
            f"Upset Risk: {ctx.get('upset_risk', 'N/A')}",

            # Agent 4: Lineups
            f"\n── ALINEACIONES Y LESIONES ──",
            f"Home Injuries: {ctx.get('home_injury_count', 0)}",
            f"Away Injuries: {ctx.get('away_injury_count', 0)}",
            f"Tactical Analysis: {ctx.get('lineup_narrative', 'N/A')}",
            f"Tactical Advantage: {ctx.get('tactical_advantage', 'N/A')}",

            # Agent 5: Sentiment
            f"\n── SENTIMIENTO ──",
            f"Home Sentiment: {ctx.get('sentiment_home', 0):.2f}",
            f"Away Sentiment: {ctx.get('sentiment_away', 0):.2f}",
            f"Narrative: {ctx.get('sentiment_narrative', 'N/A')}",

            # Agent 6: ELO
            f"\n── ELO RATINGS ──",
            f"{home}: {ctx.get('home_elo', 'N/A')} | {away}: {ctx.get('away_elo', 'N/A')}",
            f"Difference: {ctx.get('elo_difference', 0):+.1f}",
            f"ELO Analysis: {ctx.get('elo_narrative', 'N/A')}",

            # Agent 7: Odds
            f"\n── CUOTAS DEL MERCADO ──",
            f"Market Odds: {ctx.get('market_odds', {})}",
            f"Bookmaker Count: {ctx.get('bookmaker_count', 0)}",

            # Agent 9: Poisson
            f"\n── MODELO POISSON ──",
            f"xG: {home}={ctx.get('expected_goals_home', 0):.2f} | {away}={ctx.get('expected_goals_away', 0):.2f}",
            f"Probabilities: H={ctx.get('poisson_home_win', 0):.1%} D={ctx.get('poisson_draw', 0):.1%} A={ctx.get('poisson_away_win', 0):.1%}",
            f"Poisson Analysis: {ctx.get('poisson_narrative', 'N/A')}",

            # Agent 10: ML
            f"\n── MACHINE LEARNING ──",
            f"ML Probs: H={ctx.get('ml_home_win', 0):.1%} D={ctx.get('ml_draw', 0):.1%} A={ctx.get('ml_away_win', 0):.1%}",
            f"API Prediction: {ctx.get('api_prediction', {})}",
            f"API Advice: {ctx.get('api_advice', 'N/A')}",
            f"Model Agreement: {ctx.get('model_agreement', 'N/A')}",

            # Agent 11: Monte Carlo
            f"\n── MONTE CARLO (50K SIMS) ──",
            f"MC: H={ctx.get('mc_home_win', 0):.1f}% D={ctx.get('mc_draw', 0):.1f}% A={ctx.get('mc_away_win', 0):.1f}%",
            f"Most Likely Score: {ctx.get('mc_most_likely_score', 'N/A')}",
            f"MC Analysis: {ctx.get('mc_narrative', 'N/A')}",

            # Agent 12: Market Edge
            f"\n── VALUE BETS ──",
            f"Model Probabilities: {ctx.get('model_probabilities', {})}",
            f"Best Edge: {ctx.get('best_edge', {})}",
            f"Market Analysis: {ctx.get('market_narrative', 'N/A')}",
            f"False Positive Risk: {ctx.get('false_positive_risk', 'N/A')}",

            # Agent 13: Risk
            f"\n── GESTIÓN DE RIESGO ──",
            f"Best Bet: {ctx.get('best_bet', {})}",
            f"Risk Analysis: {ctx.get('risk_narrative', 'N/A')}",
            f"Professional Verdict: {ctx.get('professional_verdict', 'N/A')}",
        ]

        return "\n".join(parts)
